/*
 * OSPFd main routine.
 *   Copyright (C) 1998, 99 Kunihiro Ishiguro, Toshiaki Takada
 *
 * This file is part of GNU Zebra.
 *
 * GNU Zebra is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2, or (at your option) any
 * later version.
 *
 * GNU Zebra is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; see the file COPYING; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include <zebra.h>

#include <lib/version.h>
#include "bfd.h"
#include "getopt.h"
#include "thread.h"
#include "prefix.h"
#include "linklist.h"
#include "if.h"
#include "vector.h"
#include "vty.h"
#include "command.h"
#include "filter.h"
#include "plist.h"
#include "stream.h"
#include "log.h"
#include "memory.h"
#include "privs.h"
#include "sigevent.h"
#include "zclient.h"
#include "vrf.h"
#include "libfrr.h"
#include "routemap.h"

#ifdef FUZZING
#include "sockopt.h"
#include <netinet/ip.h>
#endif

#include "ospfd/ospfd.h"
#include "ospfd/ospf_interface.h"
#include "ospfd/ospf_asbr.h"
#include "ospfd/ospf_lsa.h"
#include "ospfd/ospf_lsdb.h"
#include "ospfd/ospf_neighbor.h"
#include "ospfd/ospf_dump.h"
#include "ospfd/ospf_route.h"
#include "ospfd/ospf_zebra.h"
#include "ospfd/ospf_vty.h"
#include "ospfd/ospf_bfd.h"
#include "ospfd/ospf_gr.h"
#include "ospfd/ospf_errors.h"
#include "ospfd/ospf_ldp_sync.h"
#include "ospfd/ospf_routemap_nb.h"

/* ospfd privileges */
zebra_capabilities_t _caps_p[] = {ZCAP_NET_RAW, ZCAP_BIND, ZCAP_NET_ADMIN,
				  ZCAP_SYS_ADMIN};

struct zebra_privs_t ospfd_privs = {
#if defined(FRR_USER) && defined(FRR_GROUP)
	.user = FRR_USER,
	.group = FRR_GROUP,
#endif
#if defined(VTY_GROUP)
	.vty_group = VTY_GROUP,
#endif
	.caps_p = _caps_p,
	.cap_num_p = array_size(_caps_p),
	.cap_num_i = 0};

/* OSPFd options. */
const struct option longopts[] = {
	{"instance", required_argument, NULL, 'n'},
	{"apiserver", no_argument, NULL, 'a'},
	{0}
};

/* OSPFd program name */

/* Master of threads. */
struct thread_master *master;

#ifdef SUPPORT_OSPF_API
extern int ospf_apiserver_enable;
#endif /* SUPPORT_OSPF_API */

/* SIGHUP handler. */
static void sighup(void)
{
	zlog_info("SIGHUP received");
}

/* SIGINT / SIGTERM handler. */
static void sigint(void)
{
	zlog_notice("Terminating on signal");
	bfd_protocol_integration_set_shutdown(true);
	ospf_terminate();
	exit(0);
}

/* SIGUSR1 handler. */
static void sigusr1(void)
{
	zlog_rotate();
}

struct quagga_signal_t ospf_signals[] = {
	{
		.signal = SIGHUP,
		.handler = &sighup,
	},
	{
		.signal = SIGUSR1,
		.handler = &sigusr1,
	},
	{
		.signal = SIGINT,
		.handler = &sigint,
	},
	{
		.signal = SIGTERM,
		.handler = &sigint,
	},
};

static const struct frr_yang_module_info *const ospfd_yang_modules[] = {
	&frr_filter_info,
	&frr_interface_info,
	&frr_route_map_info,
	&frr_vrf_info,
	&frr_ospf_route_map_info,
};

FRR_DAEMON_INFO(ospfd, OSPF, .vty_port = OSPF_VTY_PORT,

		.proghelp = "Implementation of the OSPFv2 routing protocol.",

		.signals = ospf_signals, .n_signals = array_size(ospf_signals),

		.privs = &ospfd_privs, .yang_modules = ospfd_yang_modules,
		.n_yang_modules = array_size(ospfd_yang_modules),
);

/* OSPFd main routine. */
int main(int argc, char **argv)
{
#ifdef SUPPORT_OSPF_API
	/* OSPF apiserver is disabled by default. */
	ospf_apiserver_enable = 0;
#endif /* SUPPORT_OSPF_API */

	frr_preinit(&ospfd_di, argc, argv);


#ifdef FUZZING
	ospf_master_init(frr_init_fast());
	ospf_debug_init();
	ospf_vrf_init();

	access_list_init();
	prefix_list_init();

	ospf_if_init();

	ospf_vty_init();
	ospf_vty_show_init();
	ospf_vty_clear_init();

	ospf_route_map_init();
	ospf_opaque_init();

	ospf_error_init();

	/* Fuzz here */
	bool created;
	struct ospf *o = ospf_get_instance(instance, &created);

	uint8_t *input;
	int r = frrfuzz_read_input(&input);

	/* Simulate the read process done by ospf_recv_packet */
	stream_put(o->ibuf, input, r);
	{
		struct ip *iph;
		uint16_t ip_len;

		if ((unsigned int)r < sizeof(struct ip))
			goto done;

		iph = (struct ip *)STREAM_DATA(o->ibuf);
		sockopt_iphdrincl_swab_systoh(iph);
		ip_len = iph->ip_len;

		// skipping platform #ifdefs as I test on linux right now
		// skipping ifindex lookup as it will fail anyway

		if (r != ip_len)
			goto done;
	}

	struct prefix p;
	struct interface *ifp = if_create_ifindex(69, 0);
	ifp->mtu = 68;
	str2prefix("11.0.2.0/24", &p);

	struct in_addr in;
	inet_pton(AF_INET, "0.0.0.0", &in);
	struct ospf_area *a = ospf_area_new(o, in);

	struct connected *c = connected_add_by_prefix(ifp, &p, NULL);
	add_ospf_interface(c, a);

	struct ospf_interface *oi = listhead(a->oiflist)->data;
	if (!oi)
		goto done;
	oi->state = 7; // ISM_DR

	// struct ospf_interface *oi = ospf_if_new(o, ifp, &p);
	// oi->connected = c;

	o->fuzzing_packet_ifp = ifp;

	ospf_read_helper(o);

done:
	exit(0);
#endif

	frr_opt_add("n:a", longopts,
		    "  -n, --instance     Set the instance id\n"
		    "  -a, --apiserver    Enable OSPF apiserver\n");

	while (1) {
		int opt;

		opt = frr_getopt(argc, argv, NULL);

		if (opt == EOF)
			break;

		switch (opt) {
		case 'n':
			ospfd_di.instance = ospf_instance = atoi(optarg);
			if (ospf_instance < 1)
				exit(0);
			break;
		case 0:
			break;
#ifdef SUPPORT_OSPF_API
		case 'a':
			ospf_apiserver_enable = 1;
			break;
#endif /* SUPPORT_OSPF_API */
		default:
			frr_help_exit(1);
			break;
		}
	}

	/* Invoked by a priviledged user? -- endo. */
	if (geteuid() != 0) {
		errno = EPERM;
		perror(ospfd_di.progname);
		exit(1);
	}

	/* OSPF master init. */
	ospf_master_init(frr_init());

	/* Initializations. */
	master = om->master;

	/* Library inits. */
	ospf_debug_init();
	ospf_vrf_init();

	access_list_init();
	prefix_list_init();

	/* OSPFd inits. */
	ospf_if_init();
	ospf_zebra_init(master, ospf_instance);

	/* OSPF vty inits. */
	ospf_vty_init();
	ospf_vty_show_init();
	ospf_vty_clear_init();

	/* OSPF BFD init */
	ospf_bfd_init(master);

	/* OSPF LDP IGP Sync init */
	ospf_ldp_sync_init();

	ospf_route_map_init();
	ospf_opaque_init();
	ospf_gr_init();
	ospf_gr_helper_init();

	/* OSPF errors init */
	ospf_error_init();

	frr_config_fork();
	frr_run(master);

	/* Not reached. */
	return 0;
}
