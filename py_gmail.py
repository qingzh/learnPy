# -*- coding:utf-8 -*-
'''
Things about Gmail

1. What's the difference betweein standard `imaplib` and google `imaplib`


'''

import imaplib
import json
import urllib2
import base64
from xml.dom.minidom import parse
from oauth2client.client import SignedJwtAssertionCredentials
from httplib2 import Http
from apiclient.discovery import build
import os

reldir = os.path.dirname(os.path.relpath(__file__))
CLIENT_SECRET_FILE = os.path.join(reldir, 'gmail_service.json')
OAUTH_SCOPE = "https://mail.google.com"
GMAIL_ADDRESS = ''


def jwt_oauth2():
    '''
    https://developers.google.com/identity/protocols/OAuth2ServiceAccount
    '''
    with open(CLIENT_SECRET_FILE) as f:
        data = json.loads(f.read())
    private_key = data['private_key']
    client_email = data['client_email']
    credentials = SignedJwtAssertionCredentials(
        client_email,   private_key, scope=OAUTH_SCOPE, sub=GMAIL_ADDRESS)

    http_auth = credentials.authorize(Http())
    try:
        gmail_service = build('gmail', 'v1', http=http_auth)
        threads = gmail_service.users().messages().list(
            userId='me').execute()
    except Exception as e:
        return e


def get_unseen_mails(username, password):
    '''
    >>> obj.select()
    ('OK', ['3921'])

    >>> obj.search(None, 'UnSeen')
    ('OK', ['13 14 24 31 33 48 52 53 54 60 63 64 65 67 69 112 113 114 115 120 144 145 146 148 150 155 825 1216 2760 3177 3178 3471 3482 3491 3588 3589 3590 3594 3607 3609 3617 3619 3622 3628 3632 3633 3641 3645 3646 3647 3648 3655 3656 3657 3658 3659 3660 3661 3662 3663 3664 3665 3666 3667 3718 3719 3720 3721 3722 3723 3724 3725 3727 3728 3729 3730 3746 3751 3752 3753 3754 3755 3756 3757 3759 3760 3761 3762 3763 3764 3765 3766 3767 3768 3769 3770 3771 3772 3775 3776 3784 3785 3786 3787 3788 3789 3790 3791 3792 3793 3794 3795 3796 3797 3798 3799 3800 3801 3802 3803 3804 3805 3806 3807 3808 3809 3810 3811 3812 3813 3817 3823 3829 3830 3831 3832 3833 3834 3835 3837 3838 3839 3840 3841 3842 3843 3844 3845 3846 3847 3848 3849 3850 3851 3852 3853 3854 3855 3856 3857 3858 3859 3860 3861 3862 3863 3864 3865 3866 3867 3868 3869 3870 3871 3872 3873 3874 3877 3879 3880 3886 3888 3889 3894 3895 3896 3897 3898 3899 3900 3901 3902 3903 3905 3906 3907 3908 3909 3910 3911 3912 3913 3914 3915 3916 3917 3918 3919 3920 3921'])

    '''
    obj = imaplib.IMAP4_SSL('imap.gmail.com', '993')
    obj.login(username, password)
    obj.select()
    obj.search(None, 'UnSeen')


def gmail_unread_count(username, password):
    """
    Takes a Gmail username and password and returns the unread
    messages count as an integer.
    """
    # Build the authentication string
    b64auth = base64.encodestring("%s:%s" % (username, password))
    auth = "Basic " + b64auth

    # Build the request
    req = urllib2.Request("https://mail.google.com/mail/feed/atom/")
    req.add_header("Authorization", auth)
    handle = urllib2.urlopen(req)

    # Build an XML dom tree of the feed
    dom = parse(handle)
    handle.close()

    # Get the "fullcount" xml object
    count_obj = dom.getElementsByTagName("fullcount")[0]
    # get its text and convert it to an integer
    return int(count_obj.firstChild.wholeText)
