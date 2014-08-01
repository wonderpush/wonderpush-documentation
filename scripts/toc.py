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
import xml.dom.minidom
minidom = xml.dom.minidom
import re

auto_generated_id = re.compile(r'^_.*$')
auto_generated_id_conflict = re.compile(r'^_.*_\d+$')

LINK_ROOT = os.environ.get('LINK_ROOT')
if LINK_ROOT is not None:
    if len(LINK_ROOT) == 0:
        LINK_ROOT = None
    elif not LINK_ROOT.endswith('/'):
        LINK_ROOT += '/'


class TocEntry():

    def __init__(self, id=None, title=None):
        self.parent = None
        self.id = id
        self.title = title
        self.skipToc = None
        self.linkedTo = None
        self.chunkPage = False
        self.chunkToc = False
        self.rootToc = False
        self.children = []

    def append(self, child):
        self.children.append(child)
        child.parent = self

    def is_root(self):
        return self.parent is None # or self.id is None

    def get_root(self):
        if self.is_root():
            return self
        else:
            return self.parent.get_root()

    def get_ancestry(self):
        if self.is_root():
            return [self]
        else:
            return self.parent.get_ancestry() + [self]

    def get_first_ancestor(self, filter, not_found_value=None):
        if filter(self):
            return self
        elif self.is_root():
            return not_found_value
        else:
            return self.parent.get_first_ancestor(filter, not_found_value)

    def get_common_ancestor(self, node):
        ancestrySelf = self.get_ancestry()
        ancestryNode = node.get_ancestry()
        for ancestorDepth in range(0, min(len(ancestrySelf), len(ancestryNode))):
            if not ancestrySelf[ancestorDepth] is ancestryNode[ancestorDepth]:
                ancestorDepth -= 1
                break
        return ancestrySelf[ancestorDepth]

    def depth(self):
        if self.is_root():
            return 0
        return 1 + self.parent.depth()

    def has_unskipped_children(self):
        for child in self.children:
            if not child.skipToc:
                return True
        return False

    def walk_id(self, id):
        match = []
        def callback(entry):
            if entry.id == id:
                match.append(entry)
                raise StopIteration
            return True
        self.walk(callback)
        if len(match) < 1:
            return None
        return match[0]

    def link(self, linkRef):
        if LINK_ROOT is not None:
            if self.is_root():
                return LINK_ROOT
        else:
            if self.is_root():
                print >> sys.stderr, 'WARNING: Unhandled link to root with no LINK_ROOT'
                return '[ROOT]'
        if self is linkRef:
            return '#'
        if self.linkedTo is not None:
            if ':' in self.linkedTo:
                # External link (http://, mailto:, etc.)
                return self.linkedTo
            # Internal link (a TocEntry id)
            target = self.get_root().walk_id(self.linkedTo)
            if target is None:
                print >> sys.stderr, 'WARNING: Broken link from %s to "%s"' % (self.id, self.linkedTo)
                return '[BROKEN_LINK]'
            return target.link(linkRef)
        # Get where the page starts
        chunkPageParent = self.get_first_ancestor(lambda node: node.chunkPage == True, self)
        # Create parent part
        parentParts = [node.id for node in chunkPageParent.get_ancestry()[1:]]
        # Remove id prefixes to turn them into path components
        for i in range(len(parentParts)-1, 0, -1): # from last index down to 1
            if parentParts[i].startswith(parentParts[i-1]):
                parentParts[i] = parentParts[i][len(parentParts[i-1])+1:]
        if LINK_ROOT is None:
            # Find common ancestor of chunkPageParent and linkRef
            ancestor = chunkPageParent.get_common_ancestor(linkRef)
            # Finalize parent part
            if linkRef is ancestor and not linkRef.is_root():
                # Keep the id in order to change it from file.html to folder/
                parentParts = parentParts[ancestor.depth()-1:]
            elif self is ancestor:
                # Keep the id and add one .. level, in order to change it from folder/ to file.html
                # (only needed because the target of the link is self)
                parentParts = ['..'] + parentParts[ancestor.depth()-1:]
            else:
                parentParts = parentParts[ancestor.depth():]
            parentParts = ['..'] * (linkRef.depth() - ancestor.depth() - 1) + parentParts
        parentParts = '/'.join(parentParts)
        # Add the id of self directly, no hierarchy
        # unless self is a page itself
        if chunkPageParent is self:
            return (LINK_ROOT or '') + parentParts
        else:
            return (LINK_ROOT or '') + parentParts + '#' + self.id

    def __str__(self):
        parts = []
        curr = self
        while curr.id is not None:
            parts.append(curr.title.encode('utf-8'))
            curr = curr.parent
        parts.reverse()
        return ' / '.join(parts) \
            + (' […]' if self.chunkToc else '') \
            + (' [PAGE]' if self.chunkPage else '') \
            + (' [TOC]' if self.rootToc else '') \
            + (' [LEAF]' if not self.has_unskipped_children() else '') \
            + (' [LINK]' if self.linkedTo is not None else '') \
            + ' #' + unicode(self.id).encode('utf-8') \
            + ' href:' + self.link(self.get_root()).encode('utf-8')

    def walk(self, callback):
        try:
            self.__walk(callback)
        except StopIteration:
            pass

    def __walk(self, callback):
        if not self.is_root():
            if callback(self) == False:
                return
        for child in self.children:
            child.__walk(callback)

    def rec_print(self):
        def print_me(item):
            print str(item)
        self.walk(print_me)

    def write_html(self, f, pageRoot=None, tocRoot=None, indent=0, open=None):
        if pageRoot is None:
            pageRoot = self
        if tocRoot is None:
            # Find the appropriate ToC root
            tocRoot = self.get_first_ancestor(lambda node: node.rootToc, self)
            # Write from the found ToC root
            return tocRoot.write_html(f, pageRoot, tocRoot, indent, open)
        if open is self:
            open = True
        strIndent = '  ' * indent
        if not self.is_root() and not self is tocRoot:
            f.write('%s<li>\n' % strIndent)
            indent += 1
            strIndent = '  ' * indent
            clazz = ''
            if self.has_unskipped_children():
                if not self.linkedTo or ':' in self.linkedTo:
                    # No link, or external link (http://, mailto:, etc.)
                    target = self
                else: # Internal link (a TocEntry id)
                    target = self.get_root().walk_id(self.linkedTo)
                    if target is None:
                        print >> sys.stderr, 'WARNING: Broken link from %s to "%s"' % (self.id, self.linkedTo)
                        target = self
                if target.chunkPage:
                    label = '<a href="%s">%s</a>' % (self.link(pageRoot).encode('utf-8'), self.title.encode('utf-8'))
                else:
                    label = self.title.encode('utf-8')
                f.write('%s<span class="openable">\n' % strIndent)
                f.write('%s  <span class="arrow"><span class="%s"></span></span>%s\n' % (strIndent, 'arrow_opened' if open == True else 'arrow_closed', label))
                f.write('%s</span>\n' % strIndent)
            else:
                f.write('%s<a href="%s">%s</a>\n' % (strIndent, self.link(pageRoot).encode('utf-8'), self.title.encode('utf-8')))
        if self.has_unskipped_children():
            f.write('%s<ul class="menuRetractable%s">\n' % (strIndent, ' opened' if open == True else ''))
            for child in self.children:
                if child.skipToc: continue
                child.write_html(f, pageRoot, tocRoot, indent+1, open)
            f.write('%s</ul>\n' % strIndent)
        if not self.is_root() and not self is tocRoot:
            indent -= 1
            strIndent = '  ' * indent
            f.write('%s</li>\n' % strIndent)



def getNodeTag(node):
    if node.nodeType == minidom.Node.ELEMENT_NODE:
        return node.nodeName
    return None

def getText(node):
    rc = []
    for child in node.childNodes:
        if child.nodeType == node.TEXT_NODE:
            rc.append(child.data)
        else:
            rc.append(getText(child))
    return ''.join(rc)

def getTitle(node):
    for title in node.childNodes:
        if getNodeTag(title) != 'title': continue
        return getText(title)
    return None

def shouldSkipToc(node):
    return 'skip-toc' in node.getAttribute('role')

def shouldChunkToc(node):
    return 'chunk-toc' in node.getAttribute('role')

def shouldChunkPage(node):
    return 'chunk-page' in node.getAttribute('role')

def shouldRootToc(node):
    return 'toc-root' in node.getAttribute('role')

def getLinkedTo(node):
    if not 'section-link' in node.getAttribute('role'):
        return None
    for title in node.childNodes:
        if getNodeTag(title) !=  'title': continue
        for link in title.childNodes:
            if getNodeTag(link) != 'link': continue
            return link.getAttribute('linkend')
        for ulink in title.childNodes:
            if getNodeTag(ulink) != 'ulink': continue
            return ulink.getAttribute('url')

def parseLevels(node, chunkToc, levels, currToc, silent=False):
    sublevels = levels[1:]
    if len(sublevels) == 0: sublevels = levels
    for part in node.childNodes:
        forceSkipToc = False
        if getNodeTag(part) != levels[0]:
            # Allow a few [float] elements to be recognized in the ToC
            # but make sure they don't affect written HTML by setting skipToc
            if getNodeTag(part) in ['simpara', 'bridgehead']:
                forceSkipToc = True
            else:
                continue
        partId = part.getAttribute('id')
        partTitle = getTitle(part)
        childToc = TocEntry(partId, partTitle)
        childToc.skipToc = shouldSkipToc(part) or forceSkipToc
        childToc.linkedTo = getLinkedTo(part)
        childToc.chunkPage = shouldChunkPage(part)
        childToc.chunkToc = shouldChunkToc(part)
        childToc.rootToc = shouldRootToc(part)
        currToc.append(childToc)
        if not silent:
            if auto_generated_id.match(partId) and childToc.linkedTo is None:
                print >> sys.stderr, 'NOTE:', str(childToc), 'has an auto-generated id!'
                if auto_generated_id_conflict.match(partId):
                    print >> sys.stderr, 'WARNING:', str(childToc), 'conflicts with an earlier auto-generated id, such link will be broken!'
        if chunkToc and childToc.chunkToc: continue
        parseLevels(part, chunkToc, sublevels, childToc, silent)

def extractToc(dom, chunkToc, silent=False):
    toc = TocEntry()
    for book in dom.childNodes:
        if getNodeTag(book) != 'book': continue
        parseLevels(book, chunkToc, ['part', 'chapter', 'section'], toc, silent)
        break
    return toc

def tocFromFile(file, chunkToc, silent=False):
    dom = minidom.parse(file)
    return extractToc(dom, chunkToc, silent)



def usage(args):
    print >> sys.stderr, "Usage:", args[0], "-h|--help"
    print >> sys.stderr, "      ", args[0], "FILE [rootId]"
    print >> sys.stderr, "Extracts a Table of Contents from a DocBook."
    print >> sys.stderr, "    FILE    DocBook XML file to extract the ToC from."
    print >> sys.stderr, "    rootId  The id to root the ToC at."

def main(args):
    if len(args) != 2 and len(args) != 3:
        usage(args)
        return 1
    if args[1] == '-h' or args[1] == '--help':
        usage(args)
        return 0
    chunkToc = True
    rootId = None
    if len(args) == 3:
        chunkToc = False
        rootId = args[2]

    toc = tocFromFile(sys.argv[1], chunkToc, False)

    if rootId is not None and rootId != '':
        oldToc = toc
        tocRoot = oldToc.walk_id(rootId)
    else:
        tocRoot = toc
    #tocRoot.rec_print()
    tocRoot.write_html(sys.stdout)

    return 0

if __name__ == '__main__':
    rtn = main(sys.argv)
    sys.exit(rtn)
