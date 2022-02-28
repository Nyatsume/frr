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

#endif /* _FRR_ISIS_SRV6_H */
