.. sPy documentation master file, created by
   sphinx-quickstart on Mon Jan  9 16:33:09 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to sPy's documentation!
===============================

sPy is Python based script tracking changes at any online or offline location.
After detecting changes it sends emails notyfying about differences.

Source
======

Source is available as mercurial repository at bitbucket. To download latest code run::

    hg clone https://bitbucket.org/seler/spy

Structure
=========

.. automodule:: spy
   :members:
   :undoc-members:
   :private-members:

User's guide
============

Configuration
-------------

Config file should be under ``~/.spyrc``. For full example see ``.spyrc`` in sources.

SPY section
~~~~~~~~~~~

SPY section is about email. Here's an example::

    [SPY]
    email_from = sPy <selerto@gmail.com>
    email_to = Rafa Selewoko <rselewonko@gmail.com>, Zenek Mietek <selerto@gmail.com>
    smtp_host = smtp.gmail.com
    smtp_port = 587
    smtp_username = selerto@gmail.com
    smtp_password = *******
    smtp_tls = True

Sites sections
~~~~~~~~~~~~~~

Each section that's name is not ``SPY`` represents site to check. Here's an example::

    [Rozkład zajęć]
    # choices are text, html, binary
    type = html
    # choices are online or offilne
    site = online
    # starts with ``http`` if online, with ``/`` if offline
    location = http://www.degra.wi.pb.edu.pl/rozklady/rozklad.php?page=st

    # slug is only required if you want to check each site separately
    slug = rozkladzajec
    

Running sPy
-----------

To check all sites::

    ./spy.py or python3 /location/of/spy.py

To check specified sites::

    python3 /location/of/spy.py site1_slug site2_slug

It's the best to run sPy from **cron** or **Windows Task Sheduler**.

Requirements
============

* python3

License
=======

sPy: Python based script tracking changes at any url
Copyright (C) 2011  Rafał Selewońko <rafal@selewonko.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
