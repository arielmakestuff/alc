# -*- coding: utf-8 -*-
# alc/test/test_alc.py
# Copyright (C) 2016 authors and contributors (see AUTHORS file)
#
# This module is released under the MIT License.

"""Example test"""

# ============================================================================
# Imports
# ============================================================================


# Stdlib imports
from pathlib import Path

# Third-party imports
import pytest

# Local imports
import alc.core as core


# ============================================================================
# Fixtures
# ============================================================================


@pytest.yield_fixture
def phantomjs_bin():
    """
    Return absolute path of the phantomjs binary

    :return: pathlib.Path()
    """
    oldpath = core.PHANTOMJS_BIN
    rootdir = Path(str(pytest.config.rootdir))
    core.PHANTOMJS_BIN = ret = (rootdir / 'var' / 'phantomjs' /
                                'phantomjs-2.1.1.exe')
    try:
        yield ret
    finally:
        core.PHANTOMJS_BIN = oldpath


# ============================================================================
# Test
# ============================================================================


def test_run_link_check(phantomjs_bin):
    """Test fib()"""
    URL = r'http://www.worldvision.ca/aboutus/Media-Centre/Pages/LatestNews.aspx'
    core.main([URL])


# ============================================================================
#
# ============================================================================
