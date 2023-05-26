/*
 * This is an implementation of SRv6 for IS-IS
 * as per draft-ietf-lsr-isis-srv6-extensions
 *
 * Copyright (C) 2021 LINE Corporation
 * Author: Naoyuki Tachibana <naoyuki.tachibana@linecorp.com>
 * Author: Hiroki Shirokura <hiroki.shirokura@linecorp.com>
 * Author: Ryoga Saito <ryoga.saito@linecorp.com>
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation; either version 2 of the License, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; see the file COPYING; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */


#include <zebra.h>

#include "if.h"
#include "linklist.h"
#include "log.h"
#include "command.h"
#include "termtable.h"
#include "memory.h"
#include "prefix.h"
#include "table.h"
#include "srcdest_table.h"
#include "vty.h"
#include "zclient.h"
#include "lib/lib_errors.h"

#include "isisd/isisd.h"
#include "isisd/isis_spf.h"
#include "isisd/isis_spf_private.h"
#include "isisd/isis_adjacency.h"
#include "isisd/isis_route.h"
#include "isisd/isis_mt.h"
#include "isisd/isis_sr.h"
#include "isisd/isis_srv6.h"
#include "isisd/isis_tlvs.h"
#include "isisd/isis_misc.h"
#include "isisd/isis_zebra.h"
#include "isisd/isis_errors.h"

DEFINE_MTYPE_STATIC(ISISD, SRV6, "ISIS SRV6");
DEFINE_MTYPE(ISISD, ISIS_SRV6_FUNCTION, "ISIS srv6 function");

//struct zclient *zclient;
struct isis_srv6_node_segment node_segment;
struct isis_srv6_adj_segment adj_segment[SRV6_MAX_SIDS];
struct isis_srv6_locator_address loc_addr;
// struct list *srv6_locator_chunks;
extern struct list *srv6_locator_chunks;
struct in6_addr esid[SRV6_MAX_SIDS] = {0};

static bool sid_exist(const struct in6_addr *sid)
{
	for (int i=0; i<SRV6_MAX_SIDS; i++) {
		if (sid_zero(&esid[i]))
			continue;
		if (sid_same(&esid[i], sid))
			return true;
	}
	return false;
}

static void sid_register(const struct in6_addr *sid)
{
	if (sid_exist(sid))
		return;

	for (int i=0; i<SRV6_MAX_SIDS; i++)
		if (sid_zero(&esid[i])) {
			esid[i] = *sid;
			return;
		}
}

bool alloc_new_sid(uint32_t index,
			  struct in6_addr *sid)
{
	struct listnode *node;
	struct prefix_ipv6 *chunk;
	struct in6_addr sid_buf;
	bool alloced = false;

	if (!sid)
		return false;

	for (ALL_LIST_ELEMENTS_RO(srv6_locator_chunks, node, chunk)) {
		sid_buf = chunk->prefix;
		if (index != 0) {
			sid_buf.s6_addr[15] = index;
			if (sid_exist(&sid_buf))
				return false;
			alloced = true;
			break;
		}

		for (size_t i = 1; i < 255; i++) {
			sid_buf.s6_addr[15] = (i & 0xff00) >> 8;
			sid_buf.s6_addr[14] = (i & 0x00ff);

			if (sid_exist(&sid_buf))
				continue;
			alloced = true;
			break;
		}
	}

	if (!alloced)
		return false;

	sid_register(&sid_buf);
	*sid = sid_buf;

	return true;
}

static void srv6_adj_sid_add(struct isis_adjacency *adj)
{
	struct in6_addr sid;
	struct isis_srv6_adj_sid *srv6_adj_sid;
	struct isis_srv6_lan_adj_sid *srv6_lan_sid;
	struct isis_circuit *circuit = adj->circuit;
	enum seg6local_action_t act;
	struct seg6local_context ctx = {};
	char b[256];

	marker_debug_msg("call");
	if (circuit->ext == NULL)
		circuit->ext = isis_alloc_ext_subtlvs();


	if (IS_SUBTLV(circuit->ext, EXT_SRV6_ADJ_SID) ||
			IS_SUBTLV(circuit->ext, EXT_SRV6_LAN_ADJ_SID))
		return;

	switch (circuit->circ_type) {
	case CIRCUIT_T_BROADCAST:
		srv6_lan_sid = XCALLOC(MTYPE_ISIS_SUBTLV, sizeof(*srv6_lan_sid));

		bool ret = alloc_new_sid(0, &sid);
		if (!ret) {
			marker_debug_msg("failed");
			return;
		}
		srv6_lan_sid->sid = sid;
		marker_debug_fmsg("%s", inet_ntop(AF_INET6, &sid, b, sizeof(b)));

		ctx.nh6 = *adj->global_ipv6_addrs;
		act = ZEBRA_SEG6_LOCAL_ACTION_END_X;
		zclient_send_localsid(zclient, &sid, 2, act, &ctx);
		isis_tlvs_add_srv6_lan_adj_sid(circuit->ext, srv6_lan_sid);
		break;

	case CIRCUIT_T_P2P:
		srv6_adj_sid = XCALLOC(MTYPE_ISIS_SUBTLV, sizeof(*srv6_adj_sid));

		ret = alloc_new_sid(0, &sid);
		if (!ret) {
			marker_debug_msg("failed");
			return;
		}
		srv6_adj_sid->sid = sid;
		marker_debug_fmsg("%s", inet_ntop(AF_INET6, &sid, b, sizeof(b)));

		ctx.nh6 = *adj->global_ipv6_addrs;
		act = ZEBRA_SEG6_LOCAL_ACTION_END_X;
		zclient_send_localsid(zclient, &sid, 2, act, &ctx);
		isis_tlvs_add_srv6_adj_sid(circuit->ext, srv6_adj_sid);
		break;
	default:
		flog_err(EC_LIB_DEVELOPMENT, "%s: unexpected circuit type: %u",
			__func__, circuit->circ_type);
		exit(1);
	adj->srv6_adj_sid = sid;
	}
}

static void srv6_adj_sid_del(struct isis_adjacency *adj)
{
	// TODO(nyatsume)
	struct in6_addr sid = adj->srv6_adj_sid;
	struct isis_circuit *circuit = adj->circuit;

	marker_debug_msg("sid deleted");
	isis_tlvs_del_srv6_adj_sid(circuit->ext);
	if (sid_zero(&sid))
		return;
	switch(circuit->circ_type){
	case CIRCUIT_T_BROADCAST:
		isis_tlvs_del_srv6_lan_adj_sid(circuit->ext);
		if (sid_zero(&sid))
			return;
		break;
	case CIRCUIT_T_P2P:
		isis_tlvs_del_srv6_adj_sid(circuit->ext);
		if (sid_zero(&sid))
			return;
		break;
	default:
		flog_err(EC_LIB_DEVELOPMENT, "%s: unexpected circuit type: %u",
			__func__, circuit->circ_type);
		exit(1);
	}
	zclient_send_localsid(zclient,
		&sid,
		2, ZEBRA_SEG6_LOCAL_ACTION_UNSPEC, NULL);
}

int srv6_adj_state_change(struct isis_adjacency *adj)
{
	if (!adj->circuit->area->srv6db.enabled) {
		marker_debug_msg("sid_del skipped");
		return 0;
	}
	if (adj->adj_state == ISIS_ADJ_UP) {
		marker_debug_msg("skipped");
		return 0;
	}
	marker_debug_msg("call3");
	srv6_adj_sid_del(adj);
	marker_debug_msg("call4");

	return 0;
}

int srv6_adj_ip_enabled(struct isis_adjacency *adj, int family)
{
	if (!adj->circuit->area->srv6db.enabled)
		return 0;

	srv6_adj_sid_add(adj);
	marker_debug_msg("call");

	return 0;
}

int srv6_adj_ip_disabled(struct isis_adjacency *adj, int family)
{
	srv6_adj_sid_del(adj);
	marker_debug_msg("call");

	return 0;
}

void isis_srv6_locator_add(struct isis_srv6_locator *locator, struct isis_area *area)
{
	struct isis_srv6_locator *tmp;
	listnode_add(area->srv6_locators, locator);
	tmp = isis_srv6_locator_lookup_zebra(locator->name, area);
	if(tmp) {
		lsp_regenerate_schedule(area, area->is_type, 0);
	}
}

struct isis_srv6_locator *isis_srv6_locator_lookup(const char *name, struct isis_area *area)
{
	struct isis_srv6_locator *locator;
	struct listnode *node;
	for (ALL_LIST_ELEMENTS_RO(area->srv6_locators, node, locator)) {
		if (!strncmp(name, locator->name, 256)) {
			return locator;
		}
	}
	return NULL;
}

struct isis_srv6_locator *isis_srv6_locator_lookup_zebra(const char *name, struct isis_area *area)
{
	struct isis_srv6_locator *locator;
	struct listnode *node;
	for (ALL_LIST_ELEMENTS_RO(area->srv6_locators, node, locator)) {
		if (!strncmp(name, locator->name, 256)) {
			return locator;
		}
	}
	return NULL;
}

struct isis_srv6_locator *isis_srv6_locator_alloc(const char *name)
{
	struct isis_srv6_locator *locator = NULL;
	locator = XCALLOC(MTYPE_SRV6, sizeof(struct isis_srv6_locator));
	if (locator) {
		int namelen = sizeof(locator->name);
		if (namelen > 255) {
			namelen = 255;
		}
		strlcpy (locator->name, name, namelen);
		locator->functions = list_new();

	}
	return locator;
}
static void dump_srv6_chunks(struct list *cs)
{
	struct listnode *node;
	struct prefix_ipv6 *chunk;
	char buf[256];
	for (ALL_LIST_ELEMENTS_RO(cs, node, chunk)) {
		prefix2str(chunk, buf, sizeof(buf));
		marker_debug_fmsg("- %s\n", buf);
	}
}

static bool node_segment_is_exist(void)
{
	return !sid_zero(&node_segment.sid);
}

static void node_segment_set(void)
{
	struct in6_addr sid;
	bool ret;
	enum seg6local_action_t act;
	struct seg6local_context ctx = {};

	if (node_segment_is_exist())
		return;

	ret = alloc_new_sid(0, &sid);
	if (!ret)
		marker_debug_msg("failed");

	node_segment.sid = sid;
	act = ZEBRA_SEG6_LOCAL_ACTION_END;
	zclient_send_localsid(zclient, &sid, 2, act, &ctx);
}

void isis_zebra_process_srv6_locator_chunk(ZAPI_CALLBACK_ARGS)
{
	struct stream *s = NULL;
	struct srv6_locator_chunk s6c = {};
	struct prefix_ipv6 *chunk = NULL;
	int i;

	if(!srv6_locator_chunks)
		srv6_locator_chunks = list_new();
	s = zclient->ibuf;
	zapi_srv6_locator_chunk_decode(s, &s6c);

	chunk = prefix_ipv6_new();
	*chunk = s6c.prefix;
	marker_debug_fmsg("%s",s6c.locator_name);
	listnode_add(srv6_locator_chunks, chunk);
	for (i = 0; i < 16; i++)
		loc_addr.address.s6_addr[i] = s6c.prefix.prefix.s6_addr[i];
	dump_srv6_chunks(srv6_locator_chunks);
	node_segment_set();
}
int isis_zebra_srv6_manager_get_locator_chunk(const char *name)
{
	return srv6_manager_get_locator_chunk(zclient, name);
}

int isis_srv6_start(struct isis_area *area)
{
	marker_debug_msg("call");
    struct isis_adjacency *adj;
    struct listnode *node;

    for (ALL_LIST_ELEMENTS_RO(area->adjacency_list, node, adj)) {
		marker_debug_msg("sid added");
        srv6_adj_sid_add(adj);
    }

    area->srv6db.enabled = true;
	marker_debug_msg("srv6db set to enabled");

    lsp_regenerate_schedule(area, area->is_type, 0);
	marker_debug_msg("succeed to fix lsp");
    return 0;
}

void isis_srv6_stop(struct isis_area *area)
{
    struct isis_adjacency *adj;
    struct listnode *node;

    for (ALL_LIST_ELEMENTS_RO(area->adjacency_list, node, adj)) {
		srv6_adj_sid_del(adj);
	}

    area->srv6db.enabled = false;
    lsp_regenerate_schedule(area, area->is_type, 0);
}

void isis_srv6_area_init(struct isis_area *area)
{
	struct isis_srv6_db *srv6db = &area->srv6db;

	marker_debug_msg("ISIS-SRv6 initialized");

	memset(srv6db, 0, sizeof(*srv6db));

	#ifndef FABRICD
		srv6db->config.enabled = yang_get_default_bool("%s/enabled", ISIS_SRV6);
	#else
		srv6db->config.enabled = false;
	#endif
}

void isis_srv6_area_term(struct isis_area *area)
{
	if (area->srv6db.enabled)
		isis_srv6_stop(area);
}

void isis_srv6_chunk_init(struct isis *isis)
{
	isis->srv6_enabled = false;
	memset(isis->srv6_locator_name, 0, sizeof(isis->srv6_locator_name));
	isis->srv6_locator_chunks = list_new();
}

void isis_srv6_init(void)
{
	hook_register(isis_adj_state_change_hook, srv6_adj_state_change);
	hook_register(isis_adj_ip_enabled_hook, srv6_adj_ip_enabled);
	hook_register(isis_adj_ip_disabled_hook, srv6_adj_ip_disabled);
}
void isis_srv6_term(void)
{
	hook_unregister(isis_adj_state_change_hook, srv6_adj_state_change);
	hook_unregister(isis_adj_ip_enabled_hook, srv6_adj_ip_enabled);
	hook_unregister(isis_adj_ip_disabled_hook, srv6_adj_ip_disabled);
}
