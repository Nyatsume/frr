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
              +----------+   RT1   +----------+
              |      eth0|         |eth1      |
              |          |         |          |
         (1:1)|          +---------+          |(1:2)
              |                               |
              |                               |
              |                               |
              | eth0                          | eth0
         +---------+                     +---------+
         |         |                     |         |
         |   RT2   |eth1             eth1|   RT3   |
         |         +---------------------+         |
         |         |        (2:3)        |         |
         +---------+                     +---------+
         eth2|  |eth3                    eth2|  |eth3
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
    switch = tgen.add_switch("s0")
    switch.add_link(tgen.gears["rt1"], nodeif="eth0")
    switch.add_link(tgen.gears["rt2"], nodeif="eth0")

    switch = tgen.add_switch("s1")
    switch.add_link(tgen.gears["rt1"], nodeif="eth1")
    switch.add_link(tgen.gears["rt3"], nodeif="eth0")

    switch = tgen.add_switch("s3")
    switch.add_link(tgen.gears["rt2"], nodeif="eth1")
    switch.add_link(tgen.gears["rt4"], nodeif="eth0")

    switch = tgen.add_switch("s4")
    switch.add_link(tgen.gears["rt2"], nodeif="eth2")
    switch.add_link(tgen.gears["rt4"], nodeif="eth1")

    switch = tgen.add_switch("s5")
    switch.add_link(tgen.gears["rt3"], nodeif="eth1")
    switch.add_link(tgen.gears["rt5"], nodeif="eth0")

    switch = tgen.add_switch("s6")
    switch.add_link(tgen.gears["rt3"], nodeif="eth2")
    switch.add_link(tgen.gears["rt5"], nodeif="eth1")

    switch = tgen.add_switch("s7")
    switch.add_link(tgen.gears["rt4"], nodeif="eth2")
    switch.add_link(tgen.gears["rt5"], nodeif="eth2")

    switch = tgen.add_switch("s8")
    switch.add_link(tgen.gears["rt4"], nodeif="eth3")
    switch.add_link(tgen.gears["rt6"], nodeif="eth0")

    switch = tgen.add_switch("s9")
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


#
# Step 2
#
# Action(s):
# -Disable IS-IS on the eth2 interface on rt4
#
# Expected changes:
# -rt4 should uninstall the Adj-SIDs pointing to rt5
# -rt5 should uninstall the Adj-SIDs pointing to rt4
# -rt2 should reinstall rt5's Prefix-SIDs (2 nexthops deleted)
# -rt3 should reinstall rt4's Prefix-SIDs (2 nexthops deleted)
# -rt4 should reinstall rt3's Prefix-SIDs (1 nexthop deleted)
# -rt4 should reinstall rt5's Prefix-SIDs (1 nexthop changed)
# -rt5 should reinstall rt2's Prefix-SIDs (1 nexthop deleted)
# -rt5 should reinstall rt4's Prefix-SIDs (1 nexthop changed)
#

def test_isis_adjacencies_step2():
    logger.info("Test (step 2): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Disabling IS-IS on the eth2 interface on rt4")
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth2" -c "no ip router isis 1"'
    )
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth2" -c "no ipv6 router isis 1"'
    )

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step2/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step2():
    logger.info("Test (step 2): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step2/show_ipv6_route.ref"
        )
#
# Step 3
#
# Action(s):
# -Shut down the eth0 interface on rt6
# -Shut down the eth1 interface on rt6
#
# Expected changes:
# -All routers should uninstall rt6's Prefix-SIDs
# -rt4 and rt5 should uninstall the Adj-SIDs pointing to rt6
# -rt4 should reconverge rt5's Prefix-SIDs through rt2 using ECMP
# -rt5 should reconverge rt4's Prefix-SIDs through rt3 using ECMP
# -rt6 should uninstall all its IS-IS routes, Prefix-SIDs and Adj-SIDs
#
def test_isis_adjacencies_step3():
    logger.info("Test (step 3): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Shutting down the eth0 interface on rt6")
    tgen.net["rt6"].cmd('vtysh -c "conf t" -c "interface eth0" -c "shutdown"')
    logger.info("Shutting down the eth1 interface on rt6")
    tgen.net["rt6"].cmd('vtysh -c "conf t" -c "interface eth1" -c "shutdown"')

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step3/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step3():
    logger.info("Test (step 3): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step3/show_ipv6_route.ref"
        )

#
# Step 4
#
# Action(s):
# -Bring up the eth0 interface on rt6
# -Bring up the eth1 interface on rt6
# -Change rt6's Locator
#
# Expected changes:
# -All routers should install rt6's Prefix-SIDs
# -rt4 and rt5 should install Adj-SIDs for rt6
# -rt4 should reconverge rt5's Prefix-SIDs through rt6 using the new Locator
# -rt5 should reconverge rt4's Prefix-SIDs through rt6 using the new Locator
# -rt6 should reinstall all IS-IS routes and Prefix-SIDs from the network, and Adj-SIDs for rt4 and rt5
#
def test_isis_adjacencies_step4():
    logger.info("Test (step 4): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Bringing up the eth0 interface on rt6")
    tgen.net["rt6"].cmd('vtysh -c "conf t" -c "interface eth0" -c "no shutdown"')
    logger.info("Bringing up the eth1 interface on rt6")
    tgen.net["rt6"].cmd('vtysh -c "conf t" -c "interface eth1" -c "no shutdown"')
    logger.info("Changing rt6's Locator")
    tgen.net["rt6"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing global-block 18000 25999"'
    )

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step4/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step4():
    logger.info("Test (step 4): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step4/show_ipv6_route.ref"
        )

#
# Step 5
#
# Action(s):
# -Disable SR on rt6
#
# Expected changes:
# -All routers should uninstall rt6's Prefix-SIDs
# -rt4 should uninstall rt5's Prefix-SIDs since the nexthop router hasn't SR enabled anymore
# -rt5 should uninstall rt4's Prefix-SIDs since the nexthop router hasn't SR enabled anymore
# -rt6 should uninstall all Prefix-SIDs from the network, and the Adj-SIDs for rt4 and rt5
#
def test_isis_adjacencies_step5():
    logger.info("Test (step 5): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Disabling SR on rt6")
    tgen.net["rt6"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "no segment-routing on"'
    )
    
    tgen.mininet_cli()
    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step5/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step5():
    logger.info("Test (step 5): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step5/show_ipv6_route.ref"
        )

#
# Step 6
#
# Action(s):
# -Enable SR on rt6
#
# Expected changes:
# -All routers should install rt6's Prefix-SIDs
# -rt4 should install rt5's Prefix-SIDs through rt6
# -rt5 should install rt4's Prefix-SIDs through rt6
# -rt6 should install all Prefix-SIDs from the network, and Adj-SIDs for rt4 and rt5
#
def test_isis_adjacencies_step6():
    logger.info("Test (step 6): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Enabling SR on rt6")
    tgen.net["rt6"].cmd('vtysh -c "conf t" -c "router isis 1" -c "segment-routing on"')

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step6/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step6():
    logger.info("Test (step 6): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step6/show_ipv6_route.ref"
        )

#
# Step 7
#
# Action(s):
# -Delete rt1's Prefix-SIDs
#
# Expected changes:
# -All routers should uninstall rt1's Prefix-SIDs
#
def test_isis_adjacencies_step7():
    logger.info("Test (step 7): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Deleting rt1's Prefix-SIDs")
    tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "no segment-routing prefix 1.1.1.1/32 index 10"'
    )
    tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "no segment-routing prefix 2001:db8:1000::1/128 index 11"'
    )

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step7/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step7():
    logger.info("Test (step 7): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step7/show_ipv6_route.ref"
        )

#
# Step 8
#
# Action(s):
# -Re-add rt1's Prefix-SIDs
#
# Expected changes:
# -All routers should install rt1's Prefix-SIDs
#
def test_isis_adjacencies_step8():
    logger.info("Test (step 8): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Re-adding rt1's Prefix-SIDs")
    tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing prefix 1.1.1.1/32 index 10"'
    )
    tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing prefix 2001:db8:1000::1/128 index 11"'
    )

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step8/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step8():
    logger.info("Test (step 8): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step8/show_ipv6_route.ref"
        )

#
# Step 10
#
# Action(s):
# -Remove the IPv4 address from rt4's eth-rt2-1 interface
#
# Expected changes:
# -rt2 should uninstall the IPv4 Adj-SIDs attached to the eth-rt4-1 interface
# -rt2 should reinstall all IPv4 Prefix-SIDs whose nexthop router is rt4 (ECMP shouldn't be used anymore)
# -rt4 should reinstall all IPv4 Prefix-SIDs whose nexthop router is rt2 (ECMP shouldn't be used anymore)
#
def test_isis_adjacencies_step10():
    logger.info("Test (step 10): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Removing the IPv4 address from rt4's eth-rt2-1 interface")
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth-rt2-1" -c "no ip address 10.0.2.4/24"'
    )

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step10/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step10():
    logger.info("Test (step 10): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step10/show_ipv6_route.ref"
        )

#
# Step 11
#
# Action(s):
# -Enter invalid SR configuration
#
# Expected changes:
# -All commands should be rejected
#
def test_isis_invalid_config_step11():
    logger.info("Test (step 11): check if invalid configuration is rejected")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Entering invalid Segment Routing configuration...")
    ret = tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing prefix 1.1.1.1/32 index 10000"'
    )
    assert (
        re.search("Configuration failed", ret) is not None
    ), "Invalid SR configuration wasn't rejected"
    ret = tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing global-block 16000 14999"'
    )
    assert (
        re.search("Configuration failed", ret) is not None
    ), "Invalid SR configuration wasn't rejected"
    ret = tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing global-block 16000 16001"'
    )
    assert (
        re.search("Configuration failed", ret) is not None
    ), "Invalid SR configuration wasn't rejected"

#
# Step 12
#
# Action(s):
# -Restore the original network setup
#
# Expected changes:
# -All routes, Prefix-SIDs and Adj-SIDs should be the same as they were after the initial network convergence (step 1)
#
def test_isis_adjacencies_step12():
    logger.info("Test (step 12): check IS-IS adjacencies")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info("Restoring the original network setup")
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth-rt5" -c "ip router isis 1"'
    )
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth-rt5" -c "ipv6 router isis 1"'
    )
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth-rt5" -c "isis network point-to-point"'
    )
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth-rt5" -c "isis hello-multiplier 3"'
    )
    tgen.net["rt6"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing global-block 16000 23999"'
    )
    tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing prefix 1.1.1.1/32 index 10"'
    )
    tgen.net["rt1"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing prefix 2001:db8:1000::1/128 index 11"'
    )
    tgen.net["rt6"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing prefix 6.6.6.6/32 index 60 explicit-null"'
    )
    tgen.net["rt6"].cmd(
        'vtysh -c "conf t" -c "router isis 1" -c "segment-routing prefix 2001:db8:1000::6/128 index 61 explicit-null"'
    )
    tgen.net["rt4"].cmd(
        'vtysh -c "conf t" -c "interface eth-rt2-1" -c "ip address 10.0.2.4/24"'
    )

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step1/show_yang_interface_isis_adjacencies.ref",
        )

def test_rib_ipv6_step12():
    logger.info("Test (step 12): verify IPv6 RIB")
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["rt1", "rt2", "rt3", "rt4", "rt5", "rt6"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step1/show_ipv6_route.ref"
        )

# Memory leak test template
def test_memory_leak():
    "Run the memory leak test and report results."
    tgen = get_topogen()
    if not tgen.is_memleak_enabled():
        pytest.skip("Memory leak test/report is disabled")

    tgen.report_memory_leaks()

if __name__ == "__main__":
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))