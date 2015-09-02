import os
import requests


def _gen_files(filename, filetype=None):
    '''
    generate `file` to send files
    multipart/form-data

    Sample usage:
    >>> requests.post(url, files=_gen_file(filename, filetype))

    '''
    basename = os.path.basename(filename)
    if isinstance(basename, unicode):
        basename = basename.encode('utf-8')
    basename = requests.utils.quote(basename)
    if filetype is None:
        filetype = 'application/vnd.ms-excel'
    files = {
        'file': (basename, open(filename, 'rb'), filetype),
        'utilType': (None, 'WuliaoFile'),
        'fileName': (None, '')
    }
    return files
