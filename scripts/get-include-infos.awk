#!/usr/bin/gawk -f

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

/^include::/ {
    file = SRC_DIR "/" substr($0, 10, length($0)-9-2);
    while (getline line<file != 0) {
        if (match(line, /^(=+ )(.*)$/, a) > 0) {
            level = a[1];
            title = a[2];
            if (match(title, /^<<[^,]*,(.*)>>$/, a) > 0) {
              title = a[1];
            }
            if (match(title, /^\[[^\]]*\]#([^#]*)#/, a) > 0) {
              title = a[1];
            }
            break;
        }
    }
    close(file);
    print $0 " #!prefix=\"" level "\",id-base=\"" ID_PREFIX "\",title=\"" title "\"";
    next;
}

{
    print;
}
