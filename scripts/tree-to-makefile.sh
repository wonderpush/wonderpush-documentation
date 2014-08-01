#!/bin/bash

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

SCRIPTS_DIR="$(dirname "$0")"
SRCDIR="$SCRIPTS_DIR/.."

find "$SRCDIR" -type f -name '*.asciidoc' -not -name 'main*.asciidoc' | while read f; do
    f="${f#$SRCDIR/}"
    if [ -d "${f%.asciidoc}" ]; then
        echo "ASCIIDOC_FOLDER_FILES += \$(SRCDIR)/$f"
        echo "HTML_FOLDER_FILES += \$(HTML_BUILDDIR)/${f%.asciidoc}.html"
    else
        echo "ASCIIDOC_REGULAR_FILES += \$(SRCDIR)/$f"
        echo "HTML_REGULAR_FILES += \$(HTML_BUILDDIR)/${f%.asciidoc}.html"
    fi
    echo "\$(HTML_BUILDDIR)/${f%.asciidoc}.html: \$(SRCDIR)/$f"
    # Add include dependencies
    dirname="$(dirname "$f")/"
    if [ "$dirname" = "./" ]; then
        dirname=""
    fi
    sed -n -r -e 's|^include::([^\[]*)\[.*$|$(HTML_BUILDDIR)/'"${f%.asciidoc}"'.html: $(SRCDIR)/'"$dirname"'\1|p' "$SRCDIR/$f"
done
