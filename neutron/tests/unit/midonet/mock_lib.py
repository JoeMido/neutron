# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
# @author: Ryu Ishimoto, Midokura Japan KK

import mock
import uuid

def get_bridge_mock(id=None, tenant_id='test-tenant', name='net'):
    if id is None:
        id = str(uuid.uuid4())

    bridge = mock.Mock()
    bridge.get_id.return_value = id
    bridge.get_tenant_id.return_value = tenant_id
    bridge.get_name.return_value = name
    return bridge


def get_bridge_port_mock(id=None, bridge_id=None,
                         type='ExteriorBridge'):
    if id is None:
        id = str(uuid.uuid4())
    if bridge_id is None:
        bridge_id = str(uuid.uuid4())

    port = mock.Mock()
    port.get_id.return_value = id
    port.get_brige_id.return_value = bridge_id
    port.get_type.return_value = type
    return port


def get_chain_mock(id=None, tenant_id='test-tenant', name='chain',
                   rules=None):
    if id is None:
        id = str(uuid.uuid4())

    if rules is None:
        rules = []

    chain = mock.Mock()
    chain.get_id.return_value = id
    chain.get_tenant_id.return_value = tenant_id
    chain.get_name.return_value = name
    chain.get_rules.return_value = rules
    return chain

def get_rule_mock(chain_id, action, id=None, tenant_id='test-tenant',
                  name='rule', **kwargs):
    if id is None:
        id = str(uuid.uuid4())

    r = mock.Mock()
    r.get_chain_id.return_value = chain_id
    r.get_flow_action.return_value = action
    r.get_id.return_value = id
    r.get_tenant_id.return_value = tenant_id
    r.get_name.return_value = name

    for k, v in kwargs.iteritems():
        properties = None
        if k == "dl_src": r.get_dl_src.return_value = v
        elif k == "dl_type": r.get_dl_type.return_value = v
        elif k == "inv_dl_src": r.get_inv_dl_src.return_value = v
        elif k == "inv_dl_type": r.get_inv_dl_type.return_value = v
        elif k == "inv_nw_dst": r.get_inv_dl_type.return_value = v
        elif k == "inv_nw_src": r.get_inv_dl_type.return_value = v
        elif k == "jump_chain_id": r.get_jump_chain_id.return_value = v
        elif k == "jump_chain_name": r.get_jump_chain_name.return_value = v
        elif k == "match_forward_flow": r.is_match_forward_flow.return_value = v
        elif k == "match_return_flow": r.is_match_return_flow.return_value = v
        elif k == "nw_dst_address": r.get_nw_dst_address.return_value = v
        elif k == "nw_dst_length": r.get_nw_dst_length.return_value = v
        elif k == "nw_proto": r.get_nw_proto.return_value = v
        elif k == "nw_src_addr": r.get_nw_src_address.return_value = v
        elif k == "nw_src_length": r.get_nw_src_length.return_value = v
        elif k == "port_group_dst": r.get_port_group_dst.return_value = v
        elif k == "port_group_src": r.get_port_group_src.return_value = v
        elif k == "position": pass # Rules don't know their own positions.
        elif k == "properties": pass # TODO: Do something with this?
        elif k == "tp_dst": r.get_tp_dst.return_value = v
        elif k == "tp_src": r.get_tp_src.return_value = v
        else: raise Exception("Unrecognized kwarg: (%s, %s)" % (k, v))

    return r

def get_port_group_mock(id=None, tenant_id='test-tenant', name='pg'):
    if id is None:
        id = str(uuid.uuid4())

    port_group = mock.Mock()
    port_group.get_id.return_value = id
    port_group.get_tenant_id.return_value = tenant_id
    port_group.get_name.return_value = name
    return port_group


def get_router_mock(id=None, tenant_id='test-tenant', name='router'):
    if id is None:
        id = str(uuid.uuid4())

    router = mock.Mock()
    router.get_id.return_value = id
    router.get_tenant_id.return_value = tenant_id
    router.get_name.return_value = name
    return router

def get_subnet_mock(bridge_id=None, gateway_ip='10.0.0.1',
                    subnet_prefix='10.0.0.0', subnet_len=int(24)):
    if bridge_id is None:
        bridge_id = str(uuid.uuid4())

    subnet = mock.Mock()
    subnet.get_id.return_value = subnet_prefix + '/' + str(subnet_len)
    subnet.get_bridge_id.return_value = bridge_id
    subnet.get_default_gateway.return_value = gateway_ip
    subnet.get_subnet_prefix.return_value = subnet_prefix
    subnet.get_subnet_length.return_value = subnet_len
    return subnet


class MidonetLibMockConfig():

    def __init__(self, inst):
        self.inst = inst

    def _create_bridge(self, tenant_id, name):
        return get_bridge_mock(tenant_id=tenant_id, name=name)

    def _create_subnet(self, bridge, gateway_ip, subnet_prefix, subnet_len):
        return get_subnet_mock(bridge.get_id(), gateway_ip=gateway_ip,
                               subnet_prefix=subnet_prefix,
                               subnet_len=subnet_len)

    def _add_bridge_port(self, bridge):
        return get_bridge_port_mock(bridge_id=bridge.get_id())

    def _get_bridge(self, id):
        return get_bridge_mock(id=id)

    def _get_port(self, id):
        return get_bridge_port_mock(id=id)

    def _get_router(self, id):
        return get_router_mock(id=id)

    def _update_bridge(self, id, name):
        return get_bridge_mock(id=id, name=name)

    def setup(self):
        # Bridge methods side effects
        self.inst.create_bridge.side_effect = self._create_bridge
        self.inst.get_bridge.side_effect = self._get_bridge
        self.inst.update_bridge.side_effect = self._update_bridge

        # Subnet methods side effects
        self.inst.create_subnet.side_effect = self._create_subnet

        # Port methods side effects
        ex_bp = self.inst.add_bridge_port
        ex_bp.side_effect = self._add_bridge_port
        self.inst.get_port.side_effect = self._get_port

        # Router methods side effects
        self.inst.get_router.side_effect = self._get_router


class MidoClientMockConfig():

    def __init__(self, inst):
        self.inst = inst
        self.chains = {}
        self.rules = {}
        self.port_groups_in = None

    def _get_query_tenant_id(self, query):
        if query is not None and query['tenant_id']:
            tenant_id = query['tenant_id']
        else:
            tenant_id = 'test-tenant'
        return tenant_id

    def _get_bridge(self, id):
        return get_bridge_mock(id=id)

    def _create_chain(self, tenant_id, name):
        chain = get_chain_mock(tenant_id=tenant_id, name=name)
        self.chains[(tenant_id, chain.get_id())] = chain
        return chain

    def _get_chain(self, id, query=None):
        tenant_id = self._get_query_tenant_id(query)
        return self.chains.get((tenant_id, id))

    def _get_chains(self, query=None):
        tenant_id = self._get_query_tenant_id(query)
        chains_out = []
        for key in self.chains.keys():
            if key[0] == tenant_id:
                chains_out.append(self.chains.get(key))
        return chains_out

    def _add_chain_rule(self, chain, action, query=None, **kwargs):
        tenant_id = self._get_query_tenant_id(query)
        r = get_rule_mock(action, chain.get_id(), tenant_id=tenant_id, **kwargs)
        self.rules[r.get_id()] = r

        position = kwargs.get("position")
        if position is None: position = 1

        if chain.get_rules is not None:
            chain_rules = chain.get_rules()
        else:
            chain_rules = []
        chain_rules.insert(position - 1, r)
        chain.get_rules.return_value = chain_rules

    def _remove_chain_rule(self, id):
        if id in self.rules:
            r = self.rules[id]
            for chain in self.chains.itervalues():
                if (chain.get_id() == r.get_chain_id()):
                    chain.get_rules().remove(r)
            del self.rules[id]
        else:
            raise Exception("Attempted to delete non-existing rule.")

    def _get_port_groups(self, query=None):
        if not self.port_groups_in:
            return []

        tenant_id = self._get_query_tenant_id(query)
        port_groups_out = []
        for port_group in self.port_groups_in:
            port_groups_out.append(get_port_group_mock(
                id=port_group['id'], name=port_group['name'],
                tenant_id=tenant_id))
        return port_groups_out

    def _get_router(self, id):
        return get_router_mock(id=id)

    def setup(self):
        self.inst.add_chain_rule.side_effect = self._add_chain_rule
        self.inst.create_chain.side_effect = self._create_chain
        self.inst.get_bridge.side_effect = self._get_bridge
        self.inst.get_chains.side_effect = self._get_chains
        self.inst.get_chain.side_effect = self._get_chain
        self.inst.get_port_groups.side_effect = self._get_port_groups
        self.inst.get_router.side_effect = self._get_router
        self.inst.remove_chain_rule.side_effect = self._remove_chain_rule
