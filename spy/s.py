#!/usr/bin/env python3

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

SPY_DEFAULT_CONFIG_FILE = '~/.spyrc'
SPY_DEFAULT_DATA_DIR = '~/.sPy/'
DEFAULT_SITE_TYPE = 'text'


VERBOSE = False
QUIET = False

class ImproperlyConfigured(Exception):
    pass


def slugify(value):
    value = value.encode('ascii', 'ignore').decode('utf-8')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)



class Mailer(object):
    """Singleton pattern"""
    class NotSingle(Exception):
        pass
    __instance = None
    def __init__(self):
        if self.__class__.__instance is None:
            self.__class__.__instance = self
        else:
            raise self.__class__.NotSingle()
    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            return cls()
        else:
            return cls.__instance


class Site(object):

    def __init__(self, name, location, slug, mailer):
        self.name = name
        self.location = location
        self.mailer = mailer
        self.slug = slug
        self.filename = os.path.expanduser(os.path.join(SPY_DEFAULT_DATA_DIR,
                                                    self.slug))
        self.diff = None

#    def check(self):
#        try:
#            f = open(self.filename, 'r')
#        except IOError:
#            f = open(self.filename, 'w')
#            f.write(self.content())
#            f.close()
#        else:
#            new = self.download_new_content()
#            old = f.read()
#            result = list(unified_diff(old.splitlines(), new.splitlines(),
#                fromfile='old version', tofile='new version'))
#            f.close()
#            if result:
#                f = open(self.filename, 'w')
#                f.write(new)
#                f.close()
#                print('\n'.join(result))
#                # TODO: mail
#                import smtplib
#
#                s = smtplib.SMTP('localhost')
#                msg = 'From: %s\r\nTo: %s\r\nSubject: Website %s has changed\r\n%s' % ('seler@tyrion', 'rselewonko@gmail.com', self.name, '\n'.join(result))

#                s.sendmail('seler@tyrion', 'rselewonko@gmail.com', msg.encode('ascii', 'ignore'))
#                s.quit()

    def download_new_content(self):
        pass

    def get_new_content(self):
        return self.new_content

    def set_new_content(self, value):
        self.new_content = value

    def download_old_content(self):
        f = open(self.get_filename(), 'r')
        return f.read()

    def get_old_content(self):
        return self.old_content

    def set_old_content(self, value):
        self.old_content = value

    def parse_new_content(self, content):
        return content

    def compare(self):
        if self.new_content != self.old_content:
            if VERBOSE:
                sys.stdout.write('site "%s" has changed\n' % self.get_name())
            self.diff = 'there is a difference'
            self.save_new_content()
        else:
            if VERBOSE:
                sys.stdout.write('site "%s" has NOT changed\n' % self.get_name())

    def save_new_content(self):
        f = open(self.filename, 'w')
        f.write(self.new_content)
        f.close()

    def get_location(self):
        return self.location
    
    def get_filename(self):
        return self.filename
    
    def get_name(self):
        return self.name

    def has_changed(self):
        return bool(self.diff)

    def prepare_notification(self):
        pass

class AbstractProxy(object):
    """Proxy pattern"""

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


class TextSite(AbstractProxy):
    "cokolwiek trescia tekstowa"
    def compare(self):
        diff = unified_diff(self.get_old_content().splitlines(),
                            self.get_new_content().splitlines(),
                            fromfile='old version',
                            tofile='new version')
        diff = list(diff)
        if diff:
            self.diff = '\n'.join(diff)
            self.save_new_content()
            if VERBOSE:
                sys.stdout.write('site "%s" has changed\n' % self.get_name())
                sys.stdout.write(self.diff)
                sys.stdout.write('\n')
        else:
            if VERBOSE:
                sys.stdout.write('site "%s" has NOT changed\n' % self.get_name())



class HTMLSite(AbstractProxy):
    "cokolwiek trescia html"
    def __init__(self, *args, **kwargs):
        if not QUIET:
            sys.stdout.write('WARNING! HTMLSite is not implemented yet. Using default Site behaviour.\n')
        super(HTMLSite, self).__init__(*args, **kwargs)


class BinarySite(AbstractProxy):
    """cokolwiek tylko do sprawdzenia czy sie zmienilo z poprzednim;
    sprawdzane na podstawie hasha md5 lub sha1"""
    def parse_new_content(self, content):
        hash = hashlib.md5(content.encode('utf-8'))
        return hash.hexdigest()
        

class AbstractDecorator(object):
    """Decorator pattern"""

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


class OnlineSiteDecorator(AbstractDecorator):
    def download_new_content(self):
        response = urlopen(self.subject.get_location())
        content = response.read()
        return self.subject.parse_new_content(content.decode('latin2')) # FIXME


class OfflineSiteDecorator(AbstractDecorator):
    def download_new_content(self):
        f = open(self.subject.get_location())
        return self.subject.parse_new_content(f.read())


class NewSiteDecorator(AbstractDecorator):
    def __init__(self, *args, **kwargs):
        super(NewSiteDecorator, self).__init__(*args, **kwargs)
        if not os.path.exists(self.subject.get_filename()):
            # there's no file, so it's new site
            # download content, save it and quit
            if VERBOSE:
                sys.stdout.write('new site "%s"\n' % self.subject.get_name())
            new_content = self.subject.download_new_content()
            f = open(self.subject.get_filename(), 'w')
            f.write(new_content)
            f.close()


class SiteFactory(object):
    """Factory pattern"""
    def get_site(self, section):
        type = section.get('type', DEFAULT_SITE_TYPE).lower()
        location = section.get('location')
        site = section.get('site', 'online')
    
        if type == 'text':
            site_class = TextSite
        if type == 'html':
            site_class = HTMLSite
        if type == 'binary':
            site_class = BinarySite

        site_object = site_class(section.name, location, slugify(section.name), None)
        # chain of decorators :D 
        if site == 'offline':
            site_object = OfflineSiteDecorator(site_object)
        elif site == 'online':
            site_object = OnlineSiteDecorator(site_object)

        site_object = NewSiteDecorator(site_object)

        return site_object


class SPy(object):
    """Facade pattern"""
    def __init__(self):
        self.sites = None

    def get_sites(self):
        self.sites = []
        site_factory = SiteFactory()
        for section in self.config.sections():
            if not section == 'SPY':
                self.sites.append(site_factory.get_site(self.config[section]))

    def configure(self, cfg_file=None):
        if not cfg_file:
            cfg_file = os.path.expanduser(SPY_DEFAULT_CONFIG_FILE)
        self.config = configparser.ConfigParser()
        self.config.read(cfg_file)

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
        pass


def main():
    if VERBOSE:
        sys.stdout.write('verbose mode on\n\n')

    spy = SPy()
    spy.configure()
    spy.get_sites()
    spy.spy()
    spy.notify()

if __name__ == "__main__":
    if '-v' in sys.argv:
        VERBOSE = True
    if '-q' in sys.argv:
        QUIET = True
    main()
