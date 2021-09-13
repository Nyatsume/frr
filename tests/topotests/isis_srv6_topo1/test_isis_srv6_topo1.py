#!/usr/bin/env python

#
# test_isis_sr_topo1.py
# Part of NetDEF Topology Tests
#
# Copyright (c) 2019 by
# Network Device Education Foundation, Inc. ("NetDEF")
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
test_isis_sr_te_topo1.py:

                         +---------+
                         |         |
                         |   RT1   |
                         | 1.1.1.1 |
                         |         |
                         +---------+
                              |eth-sw1
                              |
                              |
                              |
         +---------+          |          +---------+
         |         |          |          |         |
         |   RT2   |eth-sw1   |   eth-sw1|   RT3   |
         | 2.2.2.2 +----------+----------+ 3.3.3.3 |
         |         |     10.0.1.0/24     |         |
         +---------+                     +---------+
    eth-rt4-1|  |eth-rt4-2          eth-rt5-1|  |eth-rt5-2
             |  |                            |  |
  10.0.2.0/24|  |10.0.3.0/24      10.0.4.0/24|  |10.0.5.0/24
             |  |                            |  |
    eth-rt2-1|  |eth-rt2-2          eth-rt3-1|  |eth-rt3-2
         +---------+                     +---------+
         |         |                     |         |
         |   RT4   |     10.0.6.0/24     |   RT5   |
         | 4.4.4.4 +---------------------+ 5.5.5.5 |
         |         |eth-rt5       eth-rt4|         |
         +---------+                     +---------+
       eth-rt6|                                |eth-rt6
              |                                |
   10.0.7.0/24|                                |10.0.8.0/24
              |          +---------+           |
              |          |         |           |
              |          |   RT6   |           |
              +----------+ 6.6.6.6 +-----------+
                  eth-rt4|         |eth-rt5
                         +---------+
                              |eth-dst (.1)
                              |
                              |10.0.11.0/24
                              |
                              |eth-rt6 (.2)
                         +---------+
                         |         |
                         |   DST   |
                         | 9.9.9.2 |
                         |         |
                         +---------+

"""

import os
import sys
import pytest
import json
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

pytestmark = [pytest.mark.bgpd, pytest.mark.isisd, pytest.mark.pathd]


def build_topo(tgen):
    "Build function"

    #
    # Define FRR Routers
    #
    for router in ["r1", "r2", "r3", "r4", "c1", "c2", "c3", "c4"]:
        tgen.add_router(router)

    #
    # Define connections
    #
    switch = tgen.add_switch("s1")
    switch.add_link(tgen.gears["c1"], nodeif="eth0")
    switch.add_link(tgen.gears["r2"], nodeif="eth2")

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


def setup_testcase(msg):
    logger.info(msg)
    tgen = get_topogen()

    # Skip if previous fatal error condition is raised
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    return tgen


def test_dummy():
    assert True, "dummy"





if __name__ == "__main__":
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
