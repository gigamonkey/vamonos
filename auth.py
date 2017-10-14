#!/usr/bin/env python3

from base64 import b64decode
from os import urandom
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json

discovery_url = 'https://accounts.google.com/.well-known/openid-configuration'
config_file   = 'oauth-config.json'

def init(url, file):
    disco  = discovery(discovery_url)
    config = oauth_config(config_file)
    return disco, config['web']

def oauth_config(file):
    with open(file) as f:
        return json.load(f)

def discovery(url):
    with urlopen(url) as f:
        return json.loads(f.read().decode('utf-8'))

def authentication_url(auth_endpoint, client_id, uri, state, nonce):

    args = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'openid email',
        'redirect_uri': uri,
        'state': state,
        'login_hint': 'sub',
        'nonce': nonce
    }

    return auth_endpoint + '?' + urlencode(args)

def postback(token_endpoint, code, client_id, client_secret, redirect_uri):
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    body = bytes(urlencode(data), 'utf-8')
    r = Request(token_endpoint, data=body, method='POST')

    try:
        with urlopen(r) as f:
            if f.getcode() == 200:
                resp = json.loads(f.read().decode('utf-8'))
                resp['jwt'] = decode_jwt(resp['id_token'])
                return resp
            else:
                return None

    except HTTPError as e:
        return None


def decode_jwt(jwt):

    def decode(x, text=True):
        bs = b64decode(pad(x))
        return json.loads(bs.decode('utf-8')) if text else bs.hex()

    def pad(s):
        return s + ('=' * (4 - (len(s) % 4) % 4))

    header, payload, mac = jwt.split('.')

    return {
        'header': decode(header),
        'payload': decode(payload),
        'mac': decode(mac, text=False)
    }


if __name__ == '__main__':

    disco, config = init(discovery_url, config_file)

    if False:
        auth_endpoint = disco['authorization_endpoint']
        client_id     = config['client_id']
        uri           = config['redirect_uris'][0]
        state         = urandom(16).hex()
        nonce         = urandom(8).hex()
        url = authentication_url(auth_endpoint, client_id, uri, state, nonce)
        print(url)
    else:
        token_endpoint = disco['token_endpoint']
        code           = '4/WpX4nJlQMeJQPR-s8Y7rSKTtmGeYB2_kOEaDJ32oKXA'
        client_id      = config['client_id']
        client_secret  = config['client_secret']
        uri            = config['redirect_uris'][0]

        postback(token_endpoint, code, client_id, client_secret, uri)
