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
test_isis_srv6_topo1.py:

[+] network address 2001:db8:X:Y::NODE_ID
[+] NODE_ID = if is-router then index else 10

      +--------+                     +--------+
      |   C1   |                     |   C2   |
      +--------+                     +--------+
       eth0|                              |eth0
           |                              |
      (1:1)|                              |(2:2)
           |                              |
       eth2|                              |eth2
      +--------+                     +--------+
      |        |eth0             eth0|        |
      |   R1   +---------------------+   R2   |
      |        |        (1:2)        |        |
      +--------+                     +--------+
       eth1|                              |eth1
           |                              |
      (1:3)|                              |(2:3)
           |                              |
       eth1|                              |eth1
      +--------+                     +--------+
      |        |        (3:4)        |        |
      |   R3   +---------------------+   R4   |
      |        |eth0             eth0|        |
      +--------+                     +--------+
       eth2|                              |eth2
           |                              |
      (3:3)|                              |(4:4)
           |                              |
       eth0|                              |eth0
      +--------+                     +--------+
      |   C3   |                     |   C4   |
      +--------+                     +--------+
"""

import os
import sys
import pytest
import json
import time
from functools import partial

# Save the Current Working Directory to find configuration files.
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(CWD, "../"))

# pylint: disable=C0413
# Import topogen and topotest helpers
from lib import topotest
from lib.topogen import Topogen, TopoRouter, get_topogen
from lib.topolog import logger


pytestmark = [pytest.mark.bgpd, pytest.mark.isisd, pytest.mark.pathd]


def build_topo(tgen):
    "Build function"

    for router in ["r1", "r2", "r3", "r4", "c1", "c2", "c3", "c4"]:
        tgen.add_router(router)

    switch = tgen.add_switch("s1")
    switch.add_link(tgen.gears["c1"], nodeif="eth0")
    switch.add_link(tgen.gears["r1"], nodeif="eth2")

    switch = tgen.add_switch("s2")
    switch.add_link(tgen.gears["r1"], nodeif="eth0")
    switch.add_link(tgen.gears["r2"], nodeif="eth0")

    switch = tgen.add_switch("s3")
    switch.add_link(tgen.gears["r2"], nodeif="eth2")
    switch.add_link(tgen.gears["c2"], nodeif="eth0")

    switch = tgen.add_switch("s4")
    switch.add_link(tgen.gears["c3"], nodeif="eth0")
    switch.add_link(tgen.gears["r3"], nodeif="eth2")

    switch = tgen.add_switch("s5")
    switch.add_link(tgen.gears["r3"], nodeif="eth0")
    switch.add_link(tgen.gears["r4"], nodeif="eth0")

    switch = tgen.add_switch("s6")
    switch.add_link(tgen.gears["r4"], nodeif="eth2")
    switch.add_link(tgen.gears["c4"], nodeif="eth0")

    switch = tgen.add_switch("s7")
    switch.add_link(tgen.gears["r1"], nodeif="eth1")
    switch.add_link(tgen.gears["r3"], nodeif="eth1")

    switch = tgen.add_switch("s8")
    switch.add_link(tgen.gears["r2"], nodeif="eth1")
    switch.add_link(tgen.gears["r4"], nodeif="eth1")



def setup_module(mod):
    "Sets up the pytest environment"
    tgen = Topogen(build_topo, mod.__name__)
    frrdir = tgen.config.get(tgen.CONFIG_SECTION, "frrdir")
    if not os.path.isfile(os.path.join(frrdir, "pathd")):
        pytest.skip("pathd daemon wasn't built")
    tgen.start_topology()
    router_list = tgen.routers()

    # For all registered routers, load the zebra configuration file
    for rname, router in router_list.items():
        router.load_config( TopoRouter.RD_ZEBRA, os.path.join(CWD, "{}/zebra.conf".format(rname)))
        router.load_config( TopoRouter.RD_ISIS, os.path.join(CWD, "{}/isisd.conf".format(rname)))
    tgen.start_router()


def teardown_module(mod):
    "Teardown the pytest environment"
    tgen = get_topogen()
    tgen.stop_topology()


def setup_testcase(msg):
    logger.info(msg)
    tgen = get_topogen()
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)
    return tgen

# def open_json_file(filename):
#     try:
#         with open(filename, "r") as f:
#             return json.load(f)
#     except IOError:
#         assert False, "Could not read file {}".format(filename)


def router_compare_json_output(rname, command, reference):
    "Compare router JSON output"

    logger.info('Comparing router "%s" "%s" output', rname, command)

    tgen = get_topogen()
    filename = "{}/{}/{}".format(CWD, rname, reference)
    expected = json.loads(open(filename).read())

    # Run test function until we get an result. Wait at most 60 seconds.
    test_func = partial(topotest.router_json_cmp, tgen.gears[rname], command, expected)
    _, diff = topotest.run_and_expect(test_func, None, count=120, wait=0.5)
    assertmsg = '"{}" JSON output mismatches the expected result'.format(rname)
    assert diff is None, assertmsg


# def test_rib():
#     tgen = get_topogen()
#     if tgen.routers_have_failure():
#         pytest.skip(tgen.errors)
#     router = tgen.gears["r1"]
#     def _check(name, cmd, expected_file):
#         logger.info("polling")
#         tgen = get_topogen()
#         router = tgen.gears[name]
#         output = json.loads(router.vtysh_cmd(cmd))
#         print(output)
#         expected = open_json_file("{}/{}".format(CWD, expected_file))
#         print(expected)
#         return topotest.json_cmp(output, expected)

#     def check(name, cmd, expected_file):
#         logger.info('[+] check {} "{}" {}'.format(name, cmd, expected_file))
#         tgen = get_topogen()
#         func = partial(_check, name, cmd, expected_file)
#         success, result = topotest.run_and_expect(func, None, count=10, wait=0.5)
#         assert result is None, "Failed"

#    time.sleep(20)
#    router.vtysh_cmd(
#		"""
#		configure terminal
#		 router isis 1
#		  srv6 locator loc1
#		"""
#	)
   # check("r1", "show isis seg srv6 json", "r1/sid.json")
    # check("r1", "show ipv6 route json", "r1/route.json")
    # check("r2", "show ipv6 route json", "r2/route.json")
    # check("r3", "show ipv6 route json", "r3/route.json")
    # check("r4", "show ipv6 route json", "r4/route.json")

#
# Step 1
#
# Test initial network convergence
#

def test_isis_adjacencies_step1():
    logger.info("Test (step 1): check IS-IS adjacencies")
    tgen = get_topogen()

    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["r1", "r2", "r3", "r4"]:
        router_compare_json_output(
            rname,
            "show yang operational-data /frr-interface:lib isisd",
            "step1/show_yang_interface_isis_adjacencies.ref"
        )


def test_rib_ipv6_step1():
    logger.info("Test (step 1): verify IPv6(SRv6) RIB")
    tgen = get_topogen()

    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    for rname in ["r1", "r2", "r3", "r4"]:
        router_compare_json_output(
            rname, "show ipv6 route isis json", "step1/show_ipv6_route.ref"
        )


#
# Step 2
    


if __name__ == "__main__":
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
