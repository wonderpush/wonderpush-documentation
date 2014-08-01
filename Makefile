#!/usr/bin/make -f

all:

#
# Folders
#

SRCDIR             ?= $(CURDIR)
SCRIPTS_DIR        ?= $(SRCDIR)/scripts
CONF_DIR           ?= $(SRCDIR)/confs
BUILDDIR           ?= $(SRCDIR)/build
HTML_BUILDDIR      ?= $(BUILDDIR)/html

#
# System commands
#

ASCIIDOC ?= asciidoc
CP       ?= cp
DIRNAME  ?= dirname
ENV      ?= env
FIND     ?= find
RM       ?= rm

#
# Tools
#

#http://stackoverflow.com/a/786530/508831
#reverse = $(if $(1),$(call reverse,$(wordlist 2,$(words $(1)),$(1)))) $(firstword $(1))
#http://stackoverflow.com/a/14260762/508831
reverse = $(if $(wordlist 2,2,$(1)),$(call reverse,$(wordlist 2,$(words $(1)),$(1))) $(firstword $(1)),$(1))

#
# Local scripts
#

TREE_TO_MAKEFILE           := $(SCRIPTS_DIR)/tree-to-makefile.sh
TOC                        := $(ENV) LINK_ROOT=$(LINK_ROOT) $(SCRIPTS_DIR)/toc.py
REWRITE                    := $(ENV) LINK_ROOT=$(LINK_ROOT) $(SCRIPTS_DIR)/rewrite.py
ID_FROM_RELPATH            := $(SCRIPTS_DIR)/id-from-relpath.sh
SHIFT_TITLE_LEVELS         := $(SCRIPTS_DIR)/shift-title-levels.awk
GET_INCLUDE_INFOS          := $(SCRIPTS_DIR)/get-include-infos.awk
INCLUDE_WITH_INFO_TO_TITLE := $(SCRIPTS_DIR)/include-with-info-to-title.sed

ASCIIDOC_ARGS := \
	--attribute encoding=utf-8 \
	--attribute source-highlighter=highlight \
	--attribute imagesdir=$(LINK_ROOT)img \
	--attribute icons \
	--attribute iconsdir=$(LINK_ROOT)img/icons \
	--attribute toc \
	--attribute disable-javascript \
	--attribute linkattrs \
	--conf-file $(CONF_DIR)/links.conf

#
# Auto-generated part
#

ASCIIDOC_REGULAR_FILES :=
ASCIIDOC_FOLDER_FILES :=
define newline


endef
$(eval $(subst #,$(newline),$(shell $(TREE_TO_MAKEFILE) | tr '\n' '#')))

#
# Manipulated files
#

FULLTOC       := $(BUILDDIR)/fulltoc.html
TOC_FILE      := $(HTML_BUILDDIR)/toc.html
DOCBOOK_FILE  := $(BUILDDIR)/index.xml
DOCBOOK_STAMP := $(DOCBOOK_FILE).stamp
HTML_FILES    := $(HTML_REGULAR_FILES) $(HTML_FOLDER_FILES) $(TOC_FILE)

#
# Phony targets
#

.PHONY: all test clean distclean FORCE

all: $(TOC_FILE) $(HTML_FILES)

test:

clean:
	$(RM) -f $(DOCBOOK_FILE) $(DOCBOOK_STAMP) $(FULLTOC) $(HTML_FILES)
	-rmdir $(call reverse, $(sort $(dir $(HTML_FILES)))) $(BUILDDIR)

FORCE:

#
# File targets
#

$(FULLTOC): $(DOCBOOK_FILE)
	@echo "Checking if ToC changed"
	@mkdir -p "$$(dirname "$@")"
	$(TOC) "$(DOCBOOK_FILE)" '' > "$@.new"
	cmp -s "$@" "$@.new" || touch $(DOCBOOK_STAMP)
	mv "$@.new" "$@"

$(DOCBOOK_STAMP): FORCE
	$(MAKE) "$(FULLTOC)"
	@mkdir -p "$$(dirname "$@")"
	[ -f "$@" ] || touch "$@"

$(DOCBOOK_FILE): main-html.asciidoc $(ASCIIDOC_REGULAR_FILES) $(ASCIIDOC_FOLDER_FILES)
	@echo "Building docbook"
	@mkdir -p "$$(dirname "$@")"
	@$(ASCIIDOC) --backend docbook -o "$@" "$<"

$(TOC_FILE): $(DOCBOOK_STAMP)
	@echo "Building ToC"
	@mkdir -p "$$(dirname "$@")"
	@$(TOC) "$(DOCBOOK_FILE)" > "$@"

$(HTML_REGULAR_FILES): $(DOCBOOK_STAMP)

$(HTML_REGULAR_FILES):
	@echo "Building $@"
	@mkdir -p "$$(dirname "$@")"
	@$(SHIFT_TITLE_LEVELS) "$<" \
	| $(ASCIIDOC) --backend html5 $(ASCIIDOC_ARGS) -o - - \
	| ( cd $(SRCDIR) && $(REWRITE) $(DOCBOOK_FILE) "$(subst $(SRCDIR)/,,$<)" > "$@" ) || ( rm "$@" && false )

$(HTML_FOLDER_FILES): $(DOCBOOK_STAMP)

$(HTML_FOLDER_FILES):
	@echo "Building $@"
	@mkdir -p "$$(dirname "$@")"
	@$(GET_INCLUDE_INFOS) -v SRC_DIR="$$($(DIRNAME) "$<")" -v ID_PREFIX="$$($(ID_FROM_RELPATH) --base "$(subst $(SRCDIR)/,,$<)")" "$<" \
	| $(INCLUDE_WITH_INFO_TO_TITLE) \
	| $(SHIFT_TITLE_LEVELS) \
	| $(ASCIIDOC) --backend html5 $(ASCIIDOC_ARGS) -o - - \
	| ( cd $(SRCDIR) && $(REWRITE) $(DOCBOOK_FILE) "$(subst $(SRCDIR)/,,$<)" > "$@" ) || ( rm "$@" && false )
