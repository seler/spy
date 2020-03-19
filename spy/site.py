# -*- coding: utf-8 -*-
import sys
import os

from spy.mailer import Mailer

SPY_DEFAULT_CONFIG_FILE = '~/.spyrc'
SPY_DEFAULT_DATA_DIR = '~/.sPy/'
DEFAULT_SITE_TYPE = 'text'
VERBOSE = True


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
        self.filename = os.path.expanduser(
            os.path.join(SPY_DEFAULT_DATA_DIR, self.slug))
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
