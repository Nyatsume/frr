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

#ifndef _FRR_ISIS_SRV6_H
#define _FRR_ISIS_SRV6_H

#include "lib/linklist.h"
#include "lib/mpls.h"
#include "lib/nexthop.h"
#include "lib/typesafe.h"

/* Segment Routing Adjacency. */

extern bool alloc_new_sid(uint32_t index, struct in6_addr *sid);

//extern void isis_zebra_process_srv6_locator_chunk(ZAPI_CALLBACK_ARGS);
//extern void isis_zebra_process_srv6_locator_chunk(ZAPI_CALLBACK_ARGS);
extern int isis_zebra_srv6_manager_get_locator_chunk(const char *name);
extern int srv6_adj_state_change(struct isis_adjacency *adj);
extern int srv6_adj_ip_enabled(struct isis_adjacency *adj, int family);
extern int srv6_adj_ip_disabled(struct isis_adjacency *adj, int family);
struct isis_srv6_node_segment {
	struct in6_addr sid;
};

struct isis_srv6_adj_segment {
	struct in6_addr sid;
	struct in6_addr adj_addr;
};

struct isis_srv6_locator_address {
	struct in6_addr address;
};

extern struct isis_srv6_locator_address loc_addr;
extern struct isis_srv6_node_segment node_segment;
extern struct isis_srv6_adj_segment adj_segment[SRV6_MAX_SIDS];
struct srv6_adjacency {
	struct in6_addr sid;
	struct in6_addr adj_addr;
};

struct isis_srv6_db {
	bool enabled;
	struct list *adj_sids;
	struct {
		bool enabled;
	} config;
};

extern int isis_srv6_start(struct isis_area *area);
extern void isis_srv6_stop(struct isis_area *area);
extern void isis_srv6_area_init(struct isis_area *area);
extern void isis_srv6_area_term(struct isis_area *area);
extern void isis_srv6_init(void);
extern void isis_srv6_term(void);

struct isis_area;

struct isis_srv6_locator {
	char name[256];
	struct prefix_ipv6 prefix;
	uint8_t function_bits_length;
	struct list *functions;
};

extern void isis_srv6_chunk_init(struct isis *isis);
extern void isis_srv6_locator_add(struct isis_srv6_locator *locator, struct isis_area *area);
extern struct isis_srv6_locator *isis_srv6_locator_lookup(const char *name, struct isis_area *area);
extern struct isis_srv6_locator *isis_srv6_locator_lookup_zebra(const char *name, struct isis_area *area);
extern struct isis_srv6_locator *isis_srv6_locator_alloc(const char *name);

#endif /* _FRR_ISIS_SRV6_H */
