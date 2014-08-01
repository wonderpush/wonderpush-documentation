#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et

# Copyright 2014 WonderPush
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import cStringIO
import BeautifulSoup

import toc
tocModule = toc



def clean(soup, toc, ref):
    # Rewrite links
    for link in soup.findAll('a'):
        href = link.get('href')
        if href is None:
            print >> sys.stderr, "WARNING: Link with no href:", link
            continue
        if href.startswith('#') and href != '#':
            href = href[1:]
            if soup.find(attrs={'id': href}) is not None or soup.find("a", attrs={'name': href}) is not None:
                # Link to an element in the page
                continue
            target = toc.walk_id(href)
            if target is None:
                print >> sys.stderr, "WARNING: Link to an unknown ToC entry \"%s\"" % href
                continue
            link['href'] = target.link(ref)
    # Access elements by id to keep a reference before removing their id attribute
    headerElmt = soup.find("div", attrs={'id': 'header'})
    tocElmt = soup.find("div", attrs={'id': 'toc'})
    footerElmt = soup.find("div", attrs={'id': 'footer'})
    # Prefer class to id
    for id in ['header', 'toc', 'toctitle', 'preamble', 'content', 'footer', 'footer-text']:
        elmt = soup.find(attrs={'id': id})
        if elmt is not None:
            elmt['class'] = (elmt.get('class', '') + ' ' + elmt['id']).strip()
            del elmt['id']
    # Add icon in header
    if headerElmt is not None:
        iconElmt = BeautifulSoup.Tag(soup, 'div', attrs={'class': 'page-badge'})
        headerElmt.insert(0, iconElmt)
    # Add breadcrumb in header
    if headerElmt is not None:
        breadcrumbElmt = BeautifulSoup.Tag(soup, 'div', attrs={'class': 'breadcrumb'})
        for i, entry in enumerate(ref.get_ancestry()[:-1]):
            if i > 0:
                breadcrumbElmt.append(BeautifulSoup.NavigableString(u' » '))
            linkElmt = BeautifulSoup.Tag(soup, 'a', attrs={'href': entry.link(ref)})
            linkElmt.append(BeautifulSoup.NavigableString(entry.title if not entry.is_root() else 'Docs'))
            breadcrumbElmt.append(linkElmt)
        headerElmt.insert(1, breadcrumbElmt)
    # Add ToC in header
    if tocElmt is not None:
        # Remove toc's noscript
        noscript = tocElmt.find("noscript")
        if noscript is not None:
            noscript.decompose() # causes problems with subsequent soup.find()
        # Inject ToC
        tocHTMLBuffer = cStringIO.StringIO()
        ref.write_html(tocHTMLBuffer, open=ref)
        tocHTML = tocHTMLBuffer.getvalue().decode('utf-8')
        tocHTMLBuffer.close()
        if tocHTML == u'':
            # Remove ToC if empty
            tocElmt.decompose()
        else:
            tocTags = BeautifulSoup.BeautifulSoup(tocHTML)
            tocElmt.append(tocTags)
            # Use a wrapper div
            wrapper = BeautifulSoup.Tag(soup, 'div', attrs={'class':'tocwrapper'})
            tocElmt.replaceWith(wrapper)
            wrapper.append(tocElmt)
    # Add license in footer
    if footerElmt is not None:
        footerLicense = BeautifulSoup.BeautifulSoup("""
<div class="footer-license">
  Except as otherwise noted, <span xmlns:dct="http://purl.org/dc/terms/" property="dct:title">WonderPush Documentation</span> by <a xmlns:cc="http://creativecommons.org/ns#" href="http://www.wonderpush.com/docs" property="cc:attributionName" rel="cc:attributionURL">WonderPush</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>,
  and code samples are licensed under the <a rel="license" href="http://www.apache.org/licenses/LICENSE-2.0">Apache 2.0 License</a>.
</div>""")
        footerElmt.insert(0, footerLicense)
    # Return just the interesting html, not the boilerplate
    rtn = soup.body.extract()
    rtn.name = 'div'
    return rtn



def usage(args):
    print "Usage:", args[0], "-h|--help"
    print "      ", args[0], "TOC FILE"
    print "Rewrites the generated page from standard input, so that it fits well in the whole website."
    print "    TOC     DocBook XML file to extract the ToC from."
    print "    FILE    The relative path to the file to rewrite."

def main(args):
    if len(args) != 3:
        usage(args)
        return 1
    if args[1] == '-h' or args[1] == '--help':
        usage(args)
        return 0
    tocFile = sys.argv[1]
    htmlFile = sys.argv[2]

    id = os.path.relpath(htmlFile)
    while True:
        id, ext = os.path.splitext(id)
        if len(ext) == 0: break
    id = id.replace(os.path.sep, '-')

    toc = tocModule.tocFromFile(tocFile, False, True)
    ref = toc.walk_id(id)
    if ref is None:
        print >> sys.stderr, "ERROR: The file id \"%s\" was not found in the ToC!" % id
        return 1

    soup = BeautifulSoup.BeautifulSoup(sys.stdin)
    out = clean(soup, toc, ref)
    print out

    return 0

if __name__ == '__main__':
    rtn = main(sys.argv)
    sys.exit(rtn)
