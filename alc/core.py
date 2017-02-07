# Module:
# Submodules:
# Created:
# Copyright (C) <date> <fullname>
#
# This module is part of the <project name> project and is released under
# the MIT License: http://opensource.org/licenses/MIT
"""
"""

# ============================================================================
# Imports
# ============================================================================


# Stdlib imports
from argparse import ArgumentParser, Namespace
import asyncio
from contextlib import contextmanager
from pathlib import Path
from pprint import pprint
import re
import sys
from types import MethodType

# Third-party imports
import aiohttp
from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
from bs4.element import Tag
from yarl import URL

# Local imports


# ============================================================================
# Globals
# ============================================================================


SITEURL = URL(r'https://world-vision-canada-fr-dev.myshopify.com'
              r'/collections/sponsorships')


PROGNAME = 'linky'


PHANTOMJS_BIN = Path.cwd() / 'phantomjs.exe'


# ============================================================================
# Main
# ============================================================================


@contextmanager
def browser():
    """Create browser instance"""
    driver = webdriver.PhantomJS(executable_path=str(PHANTOMJS_BIN))
    try:
        yield driver
    finally:
        driver.quit()


def iterlinks(src):
    """Iterate over all links found in page"""
    links = SoupStrainer('a', href=True)
    page = BeautifulSoup(src, 'lxml', parse_only=links)
    for obj in page:
        if isinstance(obj, Tag):
            yield obj


async def checklink(session, link, **kwargs):
    """Retrieve link and return its HTTP status code"""
    print('CHECKING: {}'.format(link))
    url = str(link)
    async with session.get(url, **kwargs) as response:
        await response.read()
        return url, response.status, response.reason


async def session(links, *, loop=None):
    """docstring for session"""
    conn = aiohttp.TCPConnector(limit=None)
    headers = {'accept-language': 'en-US'}
    async with aiohttp.ClientSession(connector=conn, loop=loop) as s:
        ensure_future = asyncio.ensure_future
        tasks = [ensure_future(checklink(s, l, headers=headers), loop=loop)
                 for l in links]
        result = await asyncio.gather(*tasks, loop=loop)
    return result


def start_check(links):
    """docstring for start_check"""
    if sys.platform == 'win32a':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    result = loop.run_until_complete(session(links, loop=loop))
    print('DONE CHECK')
    print('CLEANING UP...', end='')
    remaining = asyncio.Task.all_tasks(loop=loop)
    f = asyncio.gather(*remaining, loop=loop)
    try:
        loop.run_until_complete(f)
    except:
        print('ERROR')
    print('OK')
    return result


def run(ns):
    """docstring for main"""
    siteurl = ns.url
    with browser() as b:
        print('Getting links...', end='')
        b.get(str(siteurl))
        print('OK')
        src = b.page_source
        current_url = URL(b.current_url)
    print('Saving source to src.html ...', end='')
    with (Path.cwd() / 'src.html').open('w', encoding='utf-8') as f:
        f.write(src)
    print('OK')
    links = {l['href'] for l in iterlinks(src)}
    all_links = set()
    good_links = set()
    bad_links = set()
    id_links = set()
    for rawurl in links:
        all_links.add(rawurl)
        url = URL(rawurl)
        if rawurl.startswith('#'):
            linkset = id_links
        elif url.scheme and url.parts and url.parts[0] == '/':
            linkset = good_links
        elif url.is_absolute():
            url = url.with_scheme(current_url.scheme)
            linkset = good_links
        elif not url.host and url.parts and url.parts[0] == '/':
            if len(url.parts) == 1:
                url = current_url
            else:
                url = (current_url.origin().with_user(current_url.user).
                       with_password(current_url.password)).join(url)
            linkset = good_links
        else:
            linkset = bad_links
        #  print(url, linkset is good_links, linkset is bad_links, linkset is id_links)
        linkset.add(url)

    print('CHECKING LINKS...')
    results = start_check(good_links)
    print('NUM RESULTS', len(results))
    for url, status, reason in results:
        if status >= 400:
            print(status, 'ERR', reason, url)


# ============================================================================
# Main
# ============================================================================


class ProcessOptions:
    """Process cli options"""

    def __call__(self, args, ns):
        for name in dir(self):
            if name.startswith('__'):
                continue
            meth = getattr(self, name)
            if isinstance(meth, MethodType):
                meth(args, ns)

    def url(self, args, ns):
        """Process url"""
        url = URL(args.url[0])
        if not url.is_absolute():
            raise ValueError('Please provide an absolute url')
        ns.url = url


process_options = ProcessOptions()


def defaultoptions(parser):
    """cli arguments"""
    parser.add_argument(
        'url', nargs=1, metavar=('URL', ),
        help='URL to link check'
    )


def create():
    """Construct basic cli interface"""
    parser = ArgumentParser(prog=PROGNAME)

    # Create loadlimit command
    defaultoptions(parser)

    return parser


def main(arglist=None):
    """docstring for main"""
    if not arglist:
        arglist = sys.argv[1:]
        if not arglist:
            arglist.append('--help')
    parser = create()
    args = parser.parse_args(arglist)
    ns = Namespace()
    process_options(args, ns)
    run(ns)


if __name__ == '__main__':
    main()


# ============================================================================
#
# ============================================================================
