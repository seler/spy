#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#    sPy: Python based script tracking changes at any url
#    Copyright (C) 2011  Rafał Selewońko <rafal@selewonko.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import configparser
import hashlib
import os
import re
import sys

from urllib.request import urlopen

from difflib import *

from spy.mailer import Mailer
from spy.site import Site

SPY_DEFAULT_CONFIG_FILE = '~/.spyrc'
SPY_DEFAULT_DATA_DIR = '~/.sPy/'
DEFAULT_SITE_TYPE = 'text'


VERBOSE = False
QUIET = True

class ImproperlyConfigured(Exception):
    pass

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = value.encode('ascii', 'ignore').decode('utf-8')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)


class AbstractProxy(object):
    """
    Proxy pattern
    
    Default proxy interface to ``Site``.
    """

    def __init__(self, *args, **kwargs):
        self.subject = Site(*args, **kwargs)

    def download_new_content(self):
        return self.subject.download_new_content()

    def get_new_content(self):
        return self.subject.get_new_content()

    def set_new_content(self, value):
        return self.subject.set_new_content(value)

    def download_old_content(self):
        return self.subject.download_old_content()

    def get_old_content(self):
        return self.subject.get_old_content()

    def set_old_content(self, value):
        return self.subject.set_old_content(value)

    def parse_new_content(self, content):
        return self.subject.parse_new_content(content)

    def compare(self):
        return self.subject.compare()

    def save_new_content(self):
        return self.subject.save_new_content()

    def notify(self):
        return self.subject.notify()

    def get_location(self):
        return self.subject.get_location()
    
    def get_filename(self):
        return self.subject.get_filename()
    
    def get_name(self):
        return self.subject.get_name()

    def has_changed(self):
        return self.subject.has_changed()

    def prepare_notification(self):
        return self.subject.prepare_notification()

    def set_diff(self, value):
        return self.subject.set_diff(value)

    def get_diff(self):
        return self.subject.get_diff()


class TextSite(AbstractProxy):
    """
    Extends default ``Site`` behaviour providing more information (unified diff)
    about changes in text resource.
    """
    def compare(self):
        """
        Compares files using ``difflib.unified_diff``.
        """
        diff = unified_diff(self.get_old_content().splitlines(),
                            self.get_new_content().splitlines(),
                            fromfile='old version',
                            tofile='new version')
        diff = list(diff)
        if diff:
            self.set_diff('\n'.join(diff))
            self.save_new_content()
            if VERBOSE:

                sys.stdout.write('site "%s" has changed\n' % self.get_name())
                sys.stdout.write(self.get_diff())
                sys.stdout.write('\n')
        else:
            if VERBOSE:
                sys.stdout.write('site "%s" has NOT changed\n' % self.get_name())



class HTMLSite(AbstractProxy):
    """
    Extends default Site behaviour providing more information
    about changes in html resource.
    """
    def __init__(self, *args, **kwargs):
        if not QUIET:
            sys.stdout.write('WARNING! HTMLSite is not implemented yet. Using default Site behaviour.\n')
        super(HTMLSite, self).__init__(*args, **kwargs)


class BinarySite(AbstractProxy):
    """
    Extends default Site behaviour providing md5 hash check for binary files.
    """
    def parse_new_content(self, content):
        """
        Instead of comparing md5 hashes it will prepare new content as
        hashes to conserve space and speedup script.
        """
        hash = hashlib.md5(content.encode('utf-8'))
        return hash.hexdigest()
        

class AbstractDecorator(object):
    """
    Decorator pattern.

    Default interface for ``Site``.
    """

    def __init__(self, subject):
        self.subject = subject

    def download_new_content(self):
        return self.subject.download_new_content()

    def get_new_content(self):
        return self.subject.get_new_content()

    def set_new_content(self, value):
        return self.subject.set_new_content(value)

    def download_old_content(self):
        return self.subject.download_old_content()

    def get_old_content(self):
        return self.subject.get_old_content()

    def set_old_content(self, value):
        return self.subject.set_old_content(value)

    def parse_new_content(self, content):
        return self.subject.parse_new_content(content)

    def compare(self):
        return self.subject.compare()

    def save_new_content(self):
        return self.subject.save_new_content()

    def notify(self):
        return self.subject.notify()

    def get_location(self):
        return self.subject.get_location()
    
    def get_filename(self):
        return self.subject.get_filename()
    
    def get_name(self):
        return self.subject.get_name()

    def has_changed(self):
        return self.subject.has_changed()

    def prepare_notification(self):
        return self.subject.prepare_notification()

    def set_diff(self, value):
        return self.subject.set_diff(value)

    def get_diff(self):
        return self.subject.get_diff()


class OnlineSiteDecorator(AbstractDecorator):
    """
    Provides access to content online.
    """
    def download_new_content(self):
        response = urlopen(self.subject.get_location())
        content = response.read()
        return self.subject.parse_new_content(content.decode('ascii', errors='ignore'))


class OfflineSiteDecorator(AbstractDecorator):
    """
    Provides access to content offline.
    """
    def download_new_content(self):
        f = open(self.subject.get_location())
        return self.subject.parse_new_content(f.read())


class NewSiteDecorator(AbstractDecorator):
    """
    Supports initial check for new sites.
    """
    def __init__(self, *args, **kwargs):
        super(NewSiteDecorator, self).__init__(*args, **kwargs)
        self.is_new = False
        if not os.path.exists(self.subject.get_filename()):
            # there's no file, so it's new site
            # download content, save it and quit
            self.is_new = True
            if VERBOSE:
                sys.stdout.write('new site "%s"\n' % self.subject.get_name())
            new_content = self.subject.download_new_content()
            f = open(self.subject.get_filename(), 'w')
            f.write(new_content)
            f.close()

    def download_new_content(self):
        """
        If it's new site returns empty string.
        """
        if not self.is_new:
            return self.subject.download_new_content()
        else:
            return ''
    
    def download_old_content(self):
        """
        If it's new site returns empty string.
        """
        if not self.is_new:
            return self.subject.download_old_content()
        else:
            return ''


class SiteFactory(object):
    """
    Factory pattern.
    """
    def get_site(self, section):
        """
        Generates ``Site`` object.
        """
        type = section.get('type', DEFAULT_SITE_TYPE).lower()
        location = section.get('location')
        site = section.get('site', 'online')
    
        if type == 'text':
            site_class = TextSite
        if type == 'html':
            site_class = HTMLSite
        if type == 'binary':
            site_class = BinarySite

        site_object = site_class(section.name, location, getattr(section, 'slug', slugify(section.name)), None)
        # chain of decorators :D 
        if site == 'offline':
            site_object = OfflineSiteDecorator(site_object)
        elif site == 'online':
            site_object = OnlineSiteDecorator(site_object)

        site_object = NewSiteDecorator(site_object)

        return site_object


class SPy(object):
    """
    Facade pattern.
    """
    def __init__(self, site_slugs=None):
        self.sites = None
        self.site_slugs = site_slugs

    def get_sites(self):
        self.sites = []
        site_factory = SiteFactory()
        for section in self.config.sections():
            if not section == 'SPY':
                if self.site_slugs:
                    if self.config[section].get('slug', slugify(section)) not in self.site_slugs:
                        continue
                self.sites.append(site_factory.get_site(self.config[section]))

    def configure(self):
        cfg_file = os.path.expanduser(SPY_DEFAULT_CONFIG_FILE)
        self.config = configparser.ConfigParser()
        self.config.read(cfg_file)

    def initialize_mailer(self):
        conf = self.config['SPY']
        sender = conf['email_from']
        default_recipients = conf['email_to'].split(',')
        host = conf['smtp_host']
        port = conf['smtp_port']
        username = conf['smtp_username']
        password = conf['smtp_password']
        use_tls = conf['smtp_tls']
        mailer = Mailer.get_instance()
        mailer.configure(sender, default_recipients, host, port, username, password, use_tls)

    def spy(self):
        for site in self.sites:
            new_content = site.download_new_content()
            site.set_new_content(new_content)
            old_content = site.download_old_content()
            site.set_old_content(old_content)
            site.compare()
            if site.has_changed():
                site.prepare_notification()

    def notify(self):
        mailer = Mailer.get_instance()
        mailer.make_messages()
        mailer.send_messages()

    def run(self):
        """
        Runs everything.
        """
        self.configure()
        self.initialize_mailer()
        self.get_sites()
        self.spy()
        self.notify()


def main():
    """
    Parses system args and runs ``SPy``.
    """
    args = list(sys.argv[1:])

    # what's left in ``args`` are slugs of sites to check
    if args:
        site_slugs = args
    else:
        site_slugs = None

    spy = SPy(site_slugs)
    spy.run()

if __name__ == "__main__":
    main()
