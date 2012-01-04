#!/usr/bin/python3

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
import os
import re
from urllib.request import urlopen

from difflib import *

SPY_DEFAULT_CONFIG_FILE = '~/.spyrc'
SPY_DEFAULT_DATA_DIR = '~/.sPy/'
DEFAULT_SITE_TYPE = 'text'


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

    def __init__(self, name, url, slug, mailer):
        self.name = name
        self.url = url
        self.mailer = mailer
        self.slug = slug
        self.file = os.path.expanduser(os.path.join(SPY_DEFAULT_DATA_DIR,
            self.slug))

    def check(self):
        try:
            f = open(self.file, 'r')
        except IOError:
            f = open(self.file, 'w')
            f.write(self.content())
            f.close()
        else:
            new = self.content()
            old = f.read()
            result = list(unified_diff(old.splitlines(), new.splitlines(),
                fromfile='old version', tofile='new version'))
            f.close()
            if result:
                f = open(self.file, 'w')
                f.write(new)
                f.close()
                print('\n'.join(result))
                # TODO: mail
                import smtplib

                s = smtplib.SMTP('localhost')
                msg = 'From: %s\r\nTo: %s\r\nSubject: Website %s has changed\r\n%s' % ('seler@tyrion', 'rselewonko@gmail.com', self.name, '\n'.join(result))

                s.sendmail('seler@tyrion', 'rselewonko@gmail.com', msg.encode('ascii', 'ignore'))
                s.quit()

    def content(self):
        response = urlopen(self.url)
        content = response.read()
        # TODO: let specify encoding for each site or figureout something bette
        return content.decode('latin2')


class TextSite(Site):
    "cokolwiek trescia tekstowa"
    pass


class HTMLSite(Site):
    "cokolwiek trescia html"
    pass


class BinarySite(Site):
    """cokolwiek tylko do sprawdzenia czy sie zmienilo z poprzednim;
    sprawdzane na podstawie hasha md5 lub sha1"""
    def content(self):
        return ''

class SiteProxy(object):
    """Proxy pattern"""
    def __init__(self, subject):
        self.__subject = subject

    def __getattr__(self, name):
        import pdb
        pdb.set_trace()
#        getattr(self.__subject, name)

class OfflineSiteProxy(SiteProxy):
    pass

class OnlineSiteProxy(SiteProxy):
    pass

class SiteFactory(object):
    """Factory pattern"""
    def get_site(section):
        type = section.get('type', DEFAULT_SITE_TYPE).lower()
        location = section.get('location')
        site = section.get('site', 'online')
    
        if type == 'text':
            site_class = TextSite
        if type == 'html':
            site_class = HTMLSite
        if type == 'binary':
            site_class = BinarySite
    
        if site == 'offline':
            return OfflineSiteProxy(site_class(section.name, location,
                slugify(section.name), None))
        if site == 'online':
            return OnlineSiteProxy(site_class(section.name, location,
                slugify(section.name), None))


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
            site.check()

    def notify(self):
        pass


def main():
    spy = SPy()
    spy.configure()
    spy.get_sites()
    spy.spy()
    spy.notify()

if __name__ == "__main__":
    main()
