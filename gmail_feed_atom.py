# -*- coding: utf-8 -*-

'''
https://g33k.wordpress.com/category/google/
Swaroop posted a nifty Perl script to check GMail. The script basically parses an Atom feed of the latest 20 mails provided by Google. Since a Python hacker like Swaroop is dabbling in Perl, I thought it was my duty as a Python evangelist (or is it Pythangelist?) to show the people that the same thing can be achieved using Python with equal ease :) The main code is around 50% of the total code. A large portion of the code is used for the pretty printing. Here it is —
'''
# check-gmail.py -- A command line util to check GMail -*- Python -*-

# ======================================================================
# Copyright (C) 2006 Baishampayan Ghose <b.ghose@ubuntu.com>
# Time-stamp: Mon Jul 31, 2006 20:45+0530
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
# ======================================================================
'''
sample output —

ghoseb@trinka:~$ python check-gmail.py
Enter username for New mail feed at mail.google.com: foo.bar
Enter password for foo.bar in New mail feed at mail.google.com:

Gmail - Inbox for foo.bar@gmail.com
You have 20 new mails
+------------------------------------------------------------------------------------+
| Sl.| Subject                                                | Author               |
+------------------------------------------------------------------------------------+
| 0  | Strip Whitespace Middleware[...]                       | Will McCutchen ([...]|
| 1  | [FOSS Nepal] list of free alternatives to windows[...] | Manish Regmi (r[...] |
| 2  | json serialization[...]                                | Gábor Farkas (g[...] |
| 3  | editable=False and "Could not find Formfield or[...]   | Corey (coordt@e[...] |
| 4  | IronPython 1.0 release candidate[...]                  | Jeremy Dunck (j[...] |
| 5  | django server tree organization[...]                   | Kenneth[...]         |
| 6  | Project when using multiple sites[...]                 | Jay Parlar (par[...] |
| 7  | [FOSS Nepal] Neprog (nepali version pogrammer for[...] | ujwal (ujwal2@g[...] |
| 8  | Bug#379789: wrong keymap on Intel MacBook Pro[...]     | Frans Pop (elen[...] |
| 9  | debconf is Level 1?[...]                               | Clytie Siddall ([...]|
| 10 | Weird slowdown with dev server behind nat[...]         | Akatemik (tpiev[...] |
| 11 | Database API question: I am not able to return a[...]  | DavidA (david.a[...] |
| 12 | Bug#379120: lspci present on i386, verify on[...]      | Eddy Petrişor ([...] |
| 13 | New levels of D-I[...]                                 | Eddy Petrişor ([...] |
| 14 | Installed Apps in settings.py[...]                     | limodou (limodo[...] |
| 15 | where u at man ... where can i call you ??????[...]    | Sanjeev[...]         |
| 16 | unable to runser ?[...]                                | Geert[...]           |
| 17 | Bug#380585: debian 3.1 install FD[...]                 | as_hojoe (as_ho[...] |
| 18 | Re: Translated packages descriptions progress[...]     | Michael Bramer ([...]|
| 19 | Loading an url takes 60 sec.[...]                      | and_ltsk (andre[...] |
+------------------------------------------------------------------------------------+
ghoseb@trinka:~$

'''
import urllib             # For BasicHTTPAuthentication
import feedparser         # For parsing the feed
from textwrap import wrap # For pretty printing assistance

_URL = "https://mail.google.com/gmail/feed/atom"


def auth():
    '''The method to do HTTPBasicAuthentication'''
    opener = urllib.FancyURLopener()
    f = opener.open(_URL)
    feed = f.read()
    return feed


def fill(text, width):
    '''A custom method to assist in pretty printing'''
    if len(text) < width:
        return text + ' ' * (width - len(text))
    else:
        return text


def readmail(feed):
    '''Parse the Atom feed and print a summary'''
    atom = feedparser.parse(feed)
    print ""
    print atom.feed.title
    print "You have %s new mails" % len(atom.entries)
    # Mostly pretty printing magic
    print "+" + ("-" * 84) + "+"
    print "| Sl.|" + " Subject" + ' ' * 48 + "|" + " Author" + ' ' * 15 + "|"
    print "+" + ("-" * 84) + "+"
    for i in xrange(len(atom.entries)):
        print "| %s| %s| %s|" % (
            fill(str(i), 3),
            fill(wrap(atom.entries[i].title, 50)[0] + "[...]", 55),
            fill(wrap(atom.entries[i].author, 15)[0] + "[...]", 21))
    print "+" + ("-" * 84) + "+"

if __name__ == "__main__":
    f = auth()  # Do auth and then get the feed
    readmail(f)  # Let the feed be chewed by feedparser
