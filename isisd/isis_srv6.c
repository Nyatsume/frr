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

int isis_srv6_start(struct isis_area *area)
{
    struct isis_srv6_db *srv6db = &area->srv6db;
    struct isis_adjacency *adj;
    struct listnode *node;
/* ToDo
    for (ALL_LIST_ELEMENTS_RO(area->adjacency_list, node, adj)) {
        srv6_adj_sid_add(adj);
    }
*/
    area->srv6db.enabled = true;

    //lsp_regenerate_schedule(area, area->is_type, 0);
    return 0;
}

void isis_srv6_stop(struct isis_area *area)
{
    struct isis_srv6_db *srv6db = &area->srv6db;
    struct isis_adjacency *adj;
    struct listnode *node;
/* ToDo
    for (ALL_LIST_ELEMENTS_RO(area->))
*/
    area->srv6db.enabled = false;
}
