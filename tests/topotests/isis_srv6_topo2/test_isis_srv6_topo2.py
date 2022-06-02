#!/usr/bin/env python

#
# test_isis_srv6_topo1.py
# Part of NetDEF Topology Tests
#
# Copyright (c) 2022 by
# LINE Corporation, Naoyuki Tachibana <naoyuki.tachibana@linecorp.com>
# LINE Corporation, Hiroki Shirokura <hiroki.shirokura@linecorp.com>
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted, provided
# that the above copyright notice and this permission notice appear
# in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NETDEF DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NETDEF BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
#

"""
test_isis_srv6_topo2.py: 

[+] network address 2001:db8:X:Y::NODE_ID
[+] NODE_ID = index

                         +---------+
                         |         |
                         |   RT1   |
                         |         |
                         |         |
                         +---------+
                              |eth0
                              |
                              |
                              |
         +---------+          |          +---------+
         |         |          |          |         |
         |   RT2   |eth0      |      eth0|   RT3   |
         |         +----------+----------+         |
         |         |        (1:1)        |         |
         +---------+                     +---------+
         eth1|  |eth2                    eth1|  |eth2
             |  |                            |  |
        (2:1)|  |(2:2)                  (3:1)|  |(3:2)
             |  |                            |  |
         eth0|  |eth1                    eth0|  |eth1
         +---------+                     +---------+
         |         |                     |         |
         |   RT4   |        (4:1)        |   RT5   |
         |         +---------------------+         |
         |         |eth2             eth2|         |
         +---------+                     +---------+
          eth3|                                |eth3
              |                                |
         (4:2)|                                |(5:1)
              |          +---------+           |
              |          |         |           |
              |          |   RT6   |           |
              +----------+         +-----------+
                     eth0|         |eth1
                         +---------+
"""

import os
import sys
import pytest
import json
import re
from functools import partial

# Save the Current Working Directory to find configuration files.
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(CWD, "../"))

# pylint: disable=C0413
# Import topogen and topotest helpers
from lib import topotest
from lib.topogen import Topogen, TopoRouter, get_topogen
from lib.topolog import logger

# Required to instantiate the topology builder class.

pytestmark = [pytest.mark.isisd]

def build_topo(tgen):
    "Bulid function"

    #
    # Define FRR Routers
    #
    for router in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        tgen.add_router(router)
    
    #
    # Define connections
    #
    switch = tgen.add_switch("s1")
    switch.add_link(tgen.gears["rt1"], nodeif="eth0")
    switch.add_link(tgen.gears["rt2"], nodeif="eth0")
    switch.add_link(tgen.gears["rt3"], nodeif="eth0")

    switch = tgen.add_switch("s2")
    switch.add_link(tgen.gears["rt2"], nodeif="eth1")
    switch.add_link(tgen.gears["rt4"], nodeif="eth0")

    switch = tgen.add_switch("s3")
    switch.add_link(tgen.gears["rt2"], nodeif="eth2")
    switch.add_link(tgen.gears["rt4"], nodeif="eth1")

    switch = tgen.add_switch("s4")
    switch.add_link(tgen.gears["rt3"], nodeif="eth1")
    switch.add_link(tgen.gears["rt5"], nodeif="eth0")

    switch = tgen.add_switch("s5")
    switch.add_link(tgen.gears["rt3"], nodeif="eth2")
    switch.add_link(tgen.gears["rt5"], nodeif="eth1")

    switch = tgen.add_switch("s6")
    switch.add_link(tgen.gears["rt4"], nodeif="eth2")
    switch.add_link(tgen.gears["rt5"], nodeif="eth2")

    switch = tgen.add_switch("s7")
    switch.add_link(tgen.gears["rt4"], nodeif="eth3")
    switch.add_link(tgen.gears["rt6"], nodeif="eth0")

    switch = tgen.add_switch("s8")
    switch.add_link(tgen.gears["rt5"], nodeif="eth3")
    switch.add_link(tgen.gears["rt6"], nodeif="eth1")


def setup_module(mod):
    "Sets up the pytesy environment"
    tgen = Topogen(build_topo, mod.__name__)
    tgen.start_topology()

    router_list = tgen.routers()

    # For all registered routers, load the zebra configuration file
    for rname, router in router_list.items():
        router.load_config(
            TopoRouter.RD_ZEBRA, os.path.join(CWD, "{}/zebra.conf".format(rname))
        )
        router.load_config(
            TopoRouter.RD_ISIS, os.path.join(CWD, "{}/isisd.conf".format(rname))
        )

    tgen.start_router()


def teardown_module(mod):
    "Teardown the pytest environment"
    tgen = get_topogen()

    # This function tears down the whole topology.
    tgen.stop_topology()


def router_compare_json_output(rname, command, reference):
    "Compare router JSON output"

    logger.info('Comparing router "%s" "%s" output', rname, command)

    tgen = get_topogen()
    filename = "{}/{}/{}".format(CWD, rname, reference)
    expected = json.loads(open(filename).read())

    #Run test function until we get an result. Wait at most 60 seconds.
    test_func = partial(topotest.router_json_cmp, tgen.gears[rname], command, expected)
    _, diff = topotest.run_and_expect(test_func, None, count=120, wait=0.5)
    assertmsg = '"{}" JSON output mismatches the expected result'.format(rname)
    assert diff is None, assertmsg


#
# Step 1
#
# Test initial network convergence
#
def test_isis_adjecencies_step1():
    logger.info("Test (step 1): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step1/show_yang_interface_isis_adjacencies.ref",
        )


def test_rib_ipv6_step1():
    logger.info("Test (step1 ): verify IPv6(SRv6) RIB")
    tgen = get_topogen()

    #Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step1/show_ipv6_route.ref"
        )


if __name__ == "__main__":
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
