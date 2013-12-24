# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2012 Midokura Japan K.K.
# Copyright (C) 2013 Midokura PTE LTD
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Rossella Sblendido, Midokura Europe SARL
# @author: Ryu Ishimoto, Midokura Japan KK
# @author: Tomoe Sugihara, Midokura Japan KK

import mock
import os
import sys

import neutron.common.test_lib as test_lib
import neutron.tests.unit.midonet.mock_lib as mock_lib
import neutron.tests.unit.test_db_plugin as test_plugin
import neutron.tests.unit.test_extension_ext_gw_mode as test_ext_gw_mode
import neutron.tests.unit.test_extension_security_group as sg
import neutron.tests.unit.test_l3_plugin as test_l3_plugin
import webob.exc

MIDOKURA_PKG_PATH = "neutron.plugins.midonet.plugin"
MIDONET_PLUGIN_NAME = ('%s.MidonetPluginV2' % MIDOKURA_PKG_PATH)

# Need to mock the midonetclient module since the plugin will try to load it.
sys.modules["midonetclient"] = mock.Mock()


class MidonetPluginV2TestCase(test_plugin.NeutronDbPluginV2TestCase):

    def setUp(self,
              plugin=MIDONET_PLUGIN_NAME,
              ext_mgr=None,
              service_plugins=None):
        self.mock_api = mock.patch(
            'neutron.plugins.midonet.midonet_lib.MidoClient')
        etc_path = os.path.join(os.path.dirname(__file__), 'etc')
        test_lib.test_config['config_files'] = [os.path.join(
            etc_path, 'midonet.ini.test')]

        self.instance = self.mock_api.start()
        mock_cfg = mock_lib.MidonetLibMockConfig(self.instance.return_value)
        mock_cfg.setup()
        super(MidonetPluginV2TestCase, self).setUp(plugin=plugin,
                                                   ext_mgr=ext_mgr)

    def tearDown(self):
        super(MidonetPluginV2TestCase, self).tearDown()
        self.mock_api.stop()


class TestMidonetNetworksV2(test_plugin.TestNetworksV2,
                            MidonetPluginV2TestCase):

    pass


class TestMidonetL3NatTestCase(test_l3_plugin.L3NatDBIntTestCase,
                               MidonetPluginV2TestCase):
    def setUp(self,
              plugin=MIDONET_PLUGIN_NAME,
              ext_mgr=None,
              service_plugins=None):
        super(TestMidonetL3NatTestCase, self).setUp(plugin=plugin,
                                                    ext_mgr=None,
                                                    service_plugins=None)

    def test_floatingip_with_invalid_create_port(self):
        self._test_floatingip_with_invalid_create_port(MIDONET_PLUGIN_NAME)

    def test_floatingip_assoc_no_port(self):
        with self.subnet(cidr='200.0.0.0/24') as public_sub:
            self._set_net_external(public_sub['subnet']['network_id'])
            res = super(TestMidonetL3NatTestCase, self)._create_floatingip(
                self.fmt, public_sub['subnet']['network_id'])
            # Cleanup
            floatingip = self.deserialize(self.fmt, res)
            self._delete('floatingips', floatingip['floatingip']['id'])
        self.assertFalse(self.instance.return_value.add_static_nat.called)

    def test_floatingip_assoc_with_port(self):
        with self.subnet(cidr='200.0.0.0/24') as public_sub:
            self._set_net_external(public_sub['subnet']['network_id'])
            with self.port() as private_port:
                with self.router() as r:
                    # We need to hook up the private subnet to the external
                    # network in order to associate the fip.
                    sid = private_port['port']['fixed_ips'][0]['subnet_id']
                    private_sub = {'subnet': {'id': sid}}
                    self._add_external_gateway_to_router(
                        r['router']['id'],
                        public_sub['subnet']['network_id'])
                    self._router_interface_action('add', r['router']['id'],
                                                  private_sub['subnet']['id'],
                                                  None)

                    # Create the fip.
                    res = super(TestMidonetL3NatTestCase,
                                self)._create_floatingip(
                                    self.fmt,
                                    public_sub['subnet']['network_id'],
                                    port_id=private_port['port']['id'])

                    # Cleanup the resources used for the test
                    floatingip = self.deserialize(self.fmt, res)
                    self._delete('floatingips', floatingip['floatingip']['id'])
                    self._remove_external_gateway_from_router(
                        r['router']['id'],
                        public_sub['subnet']['network_id'])
                    self._router_interface_action('remove',
                                                  r['router']['id'],
                                                  private_sub['subnet']['id'],
                                                  None)
        self.assertTrue(self.instance.return_value.add_static_nat.called)

    def test_external_network_port_creation(self):
        with self.subnet(cidr='200.200.200.0/24') as pub_sub:
            self._set_net_external(pub_sub['subnet']['network_id'])
            ip_addr = "200.200.200.200"
            port_res = self._create_port(self.fmt,
                                         pub_sub['subnet']['network_id'],
                                         webob.exc.HTTPCreated.code,
                                         tenant_id='fake_tenant_id',
                                         device_id='fake_device',
                                         device_owner='fake_owner',
                                         fixed_ips=[{'subnet_id':
                                                     pub_sub['subnet']['id'],
                                                     'ip_address': ip_addr}],
                                         set_context=False)
            port = self.deserialize(self.fmt, port_res)
            self._delete('ports', port['port']['id'])
            verify_delete_call = self.instance.return_value.delete_route
            self.assertTrue(verify_delete_call.called_once)
        verify_add_call = self.instance.return_value.add_router_route
        self.assertTrue(verify_add_call.called_with(dst_network_addr=ip_addr))


class TestMidonetSecurityGroupsTestCase(sg.SecurityGroupDBTestCase):

    _plugin_name = ('%s.MidonetPluginV2' % MIDOKURA_PKG_PATH)

    def setUp(self):
        self.mock_api = mock.patch(
            'neutron.plugins.midonet.midonet_lib.MidoClient')
        etc_path = os.path.join(os.path.dirname(__file__), 'etc')
        test_lib.test_config['config_files'] = [os.path.join(
            etc_path, 'midonet.ini.test')]

        self.instance = self.mock_api.start()
        mock_cfg = mock_lib.MidonetLibMockConfig(self.instance.return_value)
        mock_cfg.setup()
        super(TestMidonetSecurityGroupsTestCase, self).setUp(self._plugin_name)


class TestMidonetSecurityGroup(sg.TestSecurityGroups,
                               TestMidonetSecurityGroupsTestCase):

    pass


class TestMidonetSubnetsV2(test_plugin.TestSubnetsV2,
                           MidonetPluginV2TestCase):

    # IPv6 is not supported by MidoNet yet.  Ignore tests that attempt to
    # create IPv6 subnet.
    def test_create_subnet_inconsistent_ipv6_cidrv4(self):
        pass

    def test_create_subnet_inconsistent_ipv6_dns_v4(self):
        pass

    def test_create_subnet_with_v6_allocation_pool(self):
        pass

    def test_update_subnet_inconsistent_ipv6_gatewayv4(self):
        pass

    def test_update_subnet_inconsistent_ipv6_hostroute_dst_v4(self):
        pass

    def test_update_subnet_inconsistent_ipv6_hostroute_np_v4(self):
        pass

    def test_create_subnet_inconsistent_ipv6_gatewayv4(self):
        pass

    def test_create_subnet_dhcp_disabled(self):
        super(TestMidonetSubnetsV2, self)._test_create_subnet(
            enable_dhcp=False)
        self.assertFalse(self.instance.return_value.create_dhcp.called)

    def test_update_subnet_change_dhcp_info(self):
        with self.subnet(enable_dhcp=True) as subnet:
            dns_servers1 = [u'10.10.10.10']
            dns_servers2 = [u'11.11.11.11']

            data = {'subnet': {'enable_dhcp': True,
                               'dns_nameservers': dns_servers1}}
            req = self.new_update_request('subnets', data,
                                          subnet['subnet']['id'])
            req.get_response(self.api)
            verify_create = self.instance.return_value.create_dhcp
            verify_create.assert_called_with(mock.ANY, mock.ANY, mock.ANY,
                                             host_rts=[],
                                             dns_servers=dns_servers1)

            data = {'subnet': {'enable_dhcp': True,
                               'dns_nameservers': dns_servers2}}
            req = self.new_update_request('subnets', data,
                                          subnet['subnet']['id'])
            req.get_response(self.api)
            verify_create.assert_called_with(mock.ANY, mock.ANY, mock.ANY,
                                             host_rts=[],
                                             dns_servers=dns_servers2)

            data = {'subnet': {'enable_dhcp': False,
                               'dns_nameservers': dns_servers2}}
            req = self.new_update_request('subnets', data,
                                          subnet['subnet']['id'])
            req.get_response(self.api)
            verify_delete = self.instance.return_value.delete_dhcp
            verify_delete.assert_called_with(mock.ANY, mock.ANY)


class TestMidonetPortsV2(test_plugin.TestPortsV2,
                         MidonetPluginV2TestCase):

    # IPv6 is not supported by MidoNet yet.  Ignore tests that attempt to
    # create IPv6 subnet.

    def test_requested_subnet_id_v4_and_v6(self):
        pass


class TestMidonetExtGwMode(MidonetPluginV2TestCase,
                           test_ext_gw_mode.ExtGwModeIntTestCase):
    pass
