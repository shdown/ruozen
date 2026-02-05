#!/usr/bin/env python3

# (c) 2026 shdown
# This code is licensed under MIT license (see LICENSE.MIT for details)

import urllib.request
import urllib.parse
import json
import os
import settings
import sys


BASE = f'http://localhost:{settings.PORT}'


def make_post_request_raw(path, fields):
    url = BASE + path
    in_data = urllib.parse.urlencode(fields).encode('utf8')
    req = urllib.request.Request(url, in_data)
    resp = urllib.request.urlopen(req)
    out_data = resp.read()
    return json.loads(out_data)


def make_post_request(path, fields, extract_field=None):
    data = make_post_request_raw(path, fields)

    if not data['ok']:
        error_code = data['error_code']
        error_msg = data['error_msg']
        raise ValueError(f'bad response: {error_code} {error_msg}')

    if extract_field is not None:
        return data[extract_field]
    else:
        return None


def main():
    new_uid = make_post_request('/api/uid/new', {}, 'uid')

    make_post_request('/api/uid/pending/set', {
        'new_uid': new_uid,
    })

    os.system(f'{settings.BROWSER} {BASE}?quick_run_uid={new_uid}')


if __name__ == '__main__':
    main()
