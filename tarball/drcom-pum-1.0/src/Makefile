##
## drcom-client PUM v1.0, Python User Mode
##
##               Makefile
##
## Copyright (c) 2009, drcom-client Team
##
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public
## License as published by the Free Software Foundation; either
## version 2.1 of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
#
## You should have received a copy of the GNU General Public
## License along with this program; if not, write to the
## Free Software Foundation, Inc., 59 Temple Place - Suite 330,
## Boston, MA 02111-1307, USA.

BINDIR ?= $(DESTDIR)/usr/bin
SRCDIR ?= $(DESTDIR)/usr/share/drcom/src/python-user-mode
INSTALLDIR ?= $(DESTDIR)/usr/share/drcom/src/kmod
REMOVEDIR ?= $(DESTDIR)/lib/modules/$(shell uname -r)/extra
## FIXME: archlinux not /etc/init.d/ but /etc/rc.d/
INITDIR ?= $(DESTDIR)/etc/init.d

.PHONY: all clean install uninstall

all:

clean:
	@rm -f $(BINDIR)/drcomclient
	@rm -rf $(SRCDIR)
	@rm -rf $(INSTALLDIR)
	@rm -rf $(REMOVEDIR)/drcom.ko
	@rm -f $(INITDIR)/drcom

install:
	@mkdir -p $(INITDIR)
	@install -m 755 scripts/drcom $(INITDIR)
	@mkdir -p $(BINDIR)
	@install -m 755 scripts/drunlevel scripts/drcom scripts/mkdrcom $(BINDIR)
	@mkdir -p $(BINDIR)
	@install -m 755 python-user-mode/drcomclient $(BINDIR)
	@mkdir -p $(SRCDIR)
	@install -m 755 python-user-mode/drcomclient $(SRCDIR)
	@mkdir -p $(INSTALLDIR)
	@install -m 644 kmod/drcom.c kmod/daemon_kernel.h kmod/Makefile $(INSTALLDIR)

uninstall:	clean
