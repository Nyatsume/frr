#!/usr/bin/env python
# SPDX-License-Identifier: ISC

#
# test_srv6_manager.py
# Part of NetDEF Topology Tests
#
# Copyright (c) 2020 by
# LINE Corporation, Hiroki Shirokura <slank.dev@gmail.com>
#

"""
test_srv6_manager.py:
Test for SRv6 manager on zebra
"""

import os
import sys
import json
import pytest
import functools

CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(CWD, "../"))

# pylint: disable=C0413
from lib import topotest
from lib.topogen import Topogen, TopoRouter, get_topogen
from lib.topolog import logger

pytestmark = [pytest.mark.bgpd, pytest.mark.sharpd]


def open_json_file(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except IOError:
        assert False, "Could not read file {}".format(filename)


def setup_module(mod):
    tgen = Topogen({None: "r1"}, mod.__name__)
    tgen.start_topology()
    for rname, router in tgen.routers().items():
        router.run("/bin/bash {}/{}/setup.sh".format(CWD, rname))
        router.load_config(
            TopoRouter.RD_ZEBRA, os.path.join(CWD, "{}/zebra.conf".format(rname))
        )
        router.load_config(
            TopoRouter.RD_BGP, os.path.join(CWD, "{}/bgpd.conf".format(rname))
        )
        router.load_config(
            TopoRouter.RD_SHARP, os.path.join(CWD, "{}/sharpd.conf".format(rname))
        )
    tgen.start_router()


def teardown_module(mod):
    tgen = get_topogen()
    tgen.stop_topology()


def get_locator_chunk_from_bgpd(router, locator):
    router.vtysh_cmd(
        """
        configure terminal
         router bgp 100
          segment-routing srv6
           locator {}
        """.format(
            locator
        )
    )


def get_locator_chunk_from_sharpd(router, locator):
    router.vtysh_cmd("sharp srv6-manager get-locator-chunk {}".format(locator))


def release_locator_chunk_from_bgpd(router, locator):
    router.vtysh_cmd(
        """
        configure terminal
         router bgp 100
          segment-routing srv6
           no locator {}
        """.format(
            locator
        )
    )


def release_locator_chunk_from_sharpd(router, locator):
    router.vtysh_cmd("sharp srv6-manager release-locator-chunk {}".format(locator))


def allocate_new_locator(router, locator, prefix):
    router.vtysh_cmd(
        """
        configure terminal
         segment-routing
          srv6
           locators
            locator {}
             prefix {}
        """.format(
            locator, prefix
        )
    )


def deallocate_locator(router, locator):
    router.vtysh_cmd(
        """
        configure terminal
         segment-routing
          srv6
           locators
            no locator {}
        """.format(
            locator
        )
    )


def disable_srv6(router):
    router.vtysh_cmd(
        """
        configure terminal
         segment-routing
          no srv6
        """
    )


def test_srv6():
    tgen = get_topogen()
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)
    router = tgen.gears["r1"]

    def _check_srv6_locator(router, expected_locator_file):
        logger.info("checking zebra locator status")
        output = json.loads(router.vtysh_cmd("show segment-routing srv6 locator json"))
        expected = open_json_file("{}/{}".format(CWD, expected_locator_file))
        return topotest.json_cmp(output, expected)

    def _check_sharpd_chunk(router, expected_chunk_file):
        logger.info("checking sharpd locator chunk status")
        output = json.loads(router.vtysh_cmd("show sharp segment-routing srv6 json"))
        expected = open_json_file("{}/{}".format(CWD, expected_chunk_file))
        return topotest.json_cmp(output, expected)

    def _check_bgpd_chunk(router, expected_chunk_file):
        logger.info("checking bgpd locator chunk status")
        output = json.loads(router.vtysh_cmd("show bgp segment-routing srv6 json"))
        expected = open_json_file("{}/{}".format(CWD, expected_chunk_file))
        return topotest.json_cmp(output, expected)

    def check_srv6_locator(router, expected_file):
        func = functools.partial(_check_srv6_locator, router, expected_file)
        success, result = topotest.run_and_expect(func, None, count=10, wait=0.5)
        assert result is None, "Failed"

    def check_sharpd_chunk(router, expected_file):
        func = functools.partial(_check_sharpd_chunk, router, expected_file)
        success, result = topotest.run_and_expect(func, None, count=10, wait=0.5)
        assert result is None, "Failed"

    def check_bgpd_chunk(router, expected_file):
        func = functools.partial(_check_bgpd_chunk, router, expected_file)
        success, result = topotest.run_and_expect(func, None, count=5, wait=0.5)
        assert result is None, "Failed"

    def check_all_srv6_status(step):
        check_srv6_locator(router, "step{}/expected_locators.json".format(step))
        check_sharpd_chunk(router, "step{}/expected_sharpd_chunks.json".format(step))
        check_bgpd_chunk(router, "step{}/expected_bgpd_chunks.json".format(step))

    # FOR DEVELOPER:
    # If you want to stop some specific line and start interactive shell,
    # please use tgen.mininet_cli() to start it.

    logger.info("Test1 for Locator Configuration")
    check_all_srv6_status(1)

    logger.info("Test2 get chunk for locator loc1 from sharpd")
    get_locator_chunk_from_sharpd(router, "loc1")
    check_all_srv6_status(2)

    logger.info("Test3 get chunk for locator loc1 from bgpd")
    get_locator_chunk_from_bgpd(router, "loc1")
    check_all_srv6_status(3)

    logger.info("Test4 release chunk for locator loc1 from sharpd")
    release_locator_chunk_from_sharpd(router, "loc1")
    check_all_srv6_status(4)

    logger.info("Test5 release chunk for locator loc1 from bgpd")
    release_locator_chunk_from_bgpd(router, "loc1")
    check_all_srv6_status(5)

    logger.info("Test6 re-get loc1 chunk from sharpd")
    get_locator_chunk_from_sharpd(router, "loc1")
    check_all_srv6_status(6)

    logger.info("Test7 re-re-release loc1 chunk from bgpd")
    release_locator_chunk_from_sharpd(router, "loc1")
    check_all_srv6_status(7)

    logger.info("Test8 additional locator loc3")
    allocate_new_locator(router, "loc3", "2001:db8:3:3::/64")
    check_all_srv6_status(8)

    logger.info("Test9 delete locator and chunk is released automatically")
    deallocate_locator(router, "loc1")
    check_all_srv6_status(9)

    logger.info("Test10 delete srv6 all configuration")
    disable_srv6(router)
    check_all_srv6_status(10)


if __name__ == "__main__":
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
