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

# JK: grep pattern s.py

# TODO: gdyby zapewnić, że tylko raz da się uruhomić skrypt to by był singleton pattern

import configparser
import os
import re
from urllib.request import urlopen

from difflib import *

SPY_DEFAULT_CONFIG_FILE = '~/.spyrc'
SPY_DEFAULT_DATA_DIR = '~/.sPy/'

class ImproperlyConfigured(Exception):
    pass

def slugify(value):
    value = value.encode('ascii', 'ignore').decode('utf-8')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)

class Site(object):

    def __init__(self, name, url, slug, mailer):
        self.name = name
        self.url = url
        self.mailer = mailer
        self.slug = slug
        self.file = os.path.expanduser(os.path.join(SPY_DEFAULT_DATA_DIR, self.slug))

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
            result = list(unified_diff(old.splitlines(), new.splitlines(), fromfile='old version', tofile='new version'))
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


class SPy(object):
    """Facade pattern???"""
    def __init__(self):
        self.configure()
        self.spy()

    def configure(self, cfg_file=None):
        if not cfg_file:
            cfg_file = os.path.expanduser(SPY_DEFAULT_CONFIG_FILE)
        config = configparser.ConfigParser()
        config.read(cfg_file)
        self.sites = []
        # jakby fora zamknąć w klasę to by było Factory pattern
        for section in config.sections():
            if not section == 'GLOBAL':
                try:
                    slug = config[section]['slug']
                except KeyError:
                    slug = slugify(section)
                try:
                    url = config[section]['url']
                except KeyError:
                    raise ImproperlyConfigured('Site %s has not url specified' % section)
                site = Site(section, url, slug, None)
                self.sites.append(site)
    def spy(self):
        for site in self.sites:
            site.check()



if __name__ == "__main__":
    SPy()
