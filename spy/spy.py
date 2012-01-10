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
import smtplib
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from urllib.request import urlopen

from difflib import *

SPY_DEFAULT_CONFIG_FILE = '~/.spyrc'
SPY_DEFAULT_DATA_DIR = '~/.sPy/'
DEFAULT_SITE_TYPE = 'text'


VERBOSE = True
QUIET = False

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


class Mailer(object):
    """
    Singleton pattern.

    Collects, creates and sends notification emails.
    """

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
        """
        Returns instance of Mailer.
        If no instance ever existed it creates one.
        """
        if cls.__instance is None:
            return cls()
        else:
            return cls.__instance

    def configure(self, sender, default_recipients, host, port, username, password, use_tls):
        """
        Configures mailer.
        """
        self.messages = {}
        self.default_recipients = default_recipients
        self.sender = sender
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def prepare_notification(self, name, diff, location, recipients=None):
        """
        Adds single notification about single site.
        """
        if recipients is None:
            recipients = self.default_recipients

        for r in recipients:
            try:
                self.messages[r] += [(name, location, diff)]
            except KeyError:
                self.messages[r] = [(name, location, diff)]

    def make_email(self, sender, recipient, data):
        """
        Creates and returns email message for single recipient.
        """
        subject = "sPy detected changes on "
        text = "Hi.\nThere are changes on things I spy for you.\n\n"
        html = "<html><head><title>sPy</title></head><body><p>Hi.</p><p>There are changes on things I spy for you.</p>"
        
        data_len = len(data) - 1
        for i, d in enumerate(data):
            name, location, diff = d
            subject += name
            text += "%s at %s:\n%s\n\n" % (name, location, diff)
            html += "<p>%s at <a href=\"%s\">%s</a>:</p><pre>%s</pre>" % (name, location, location, diff)
            
            if not i == data_len:  # if not last
                subject += ", "

        subject += "."
        text += "That's all. I'm going back to spying.\nBye"
        html += "<p>That's all. I'm going back to spying.<br>Bye.</p></body></html>"

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        return msg
        

    def make_messages(self):
        """
        Creates messages for all recipients.
        """
        self.emails = []
        for recipient, data in self.messages.items():
            email = self.make_email(self.sender, recipient, data)
            self.emails.append((self.sender, recipient, email))

    def send_messages(self):
        """
        Sends all messages.
        """
        s = smtplib.SMTP('%s:%s' % (self.host, str(self.port)))
        if self.use_tls:
            s.starttls()
        s.login(self.username, self.password)
        for sender, to, msg in self.emails:
            s.sendmail(sender, to, msg.as_string())
        s.quit()



class Site(object):
    """
    Represents single resource
    """

    def __init__(self, name, location, slug, recipients=None):
        self.name = name
        self.location = location
        self.mailer = Mailer.get_instance()
        self.slug = slug
        self.recipients = recipients
        self.filename = os.path.expanduser(os.path.join(SPY_DEFAULT_DATA_DIR,
                                                    self.slug))
        self.diff = None

    def download_new_content(self):
        """
        Dummy. Left for customization in decorators or proxies.
        """
        pass

    def get_new_content(self):
        """
        Returns new (downloaded) content.
        """
        return self.new_content

    def set_new_content(self, value):
        """
        Sets new content from *value*.
        """
        self.new_content = value

    def download_old_content(self):
        """
        Opens old file (downloaded during last check) and returns it's content.
        """
        f = open(self.get_filename(), 'r')
        return f.read()

    def get_old_content(self):
        """
        Return old content.
        """
        return self.old_content

    def set_old_content(self, value):
        """
        Sets old content from *value*.
        """
        self.old_content = value

    def parse_new_content(self, content):
        """
        Parses new content after downloading.
        """
        return content

    def compare(self):
        """
        Checks if new content is different than old content.
        """
        if self.new_content != self.old_content:
            if VERBOSE:
                sys.stdout.write('site "%s" has changed\n' % self.get_name())
            self.diff = 'contents of files are different'
            self.save_new_content()
        else:
            if VERBOSE:
                sys.stdout.write('site "%s" has NOT changed\n' % self.get_name())

    def save_new_content(self):
        """
        Saves new content for future comparisons.
        """
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
        """
        Return ``True`` if resource has changed.
        """
        return bool(self.diff)

    def prepare_notification(self):
        """
        Feeds ``Mailer``.
        """
        self.mailer.prepare_notification(self.name, self.diff, self.location, self.recipients)

    def set_diff(self, value):
        self.diff = value

    def get_diff(self):
        return self.diff

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
            self.subject.download_new_content()
        else:
            return ''
    
    def download_old_content(self):
        """
        If it's new site returns empty string.
        """
        if not self.is_new:
            self.subject.download_old_content()
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
