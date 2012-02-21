# -*- coding: utf-8 -*-

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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


