from urllib.parse import quote, unquote
from base64 import b64decode, b64encode
from auth import init, auth_url, postback
from db import DB
from flask import Flask, redirect, request, send_file, session
from flask.json import jsonify
from functools import wraps
from os import urandom
import json
import re

# We use HTTP 307 mainly so the redirection can change. This also
# allows us to log the use of links.

# TODO:
#
# - Harden authentication.

discovery_url = 'https://accounts.google.com/.well-known/openid-configuration'
oauth_config_file = 'oauth-config.json'

app = Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = urandom(12)
db = DB("testdb")

disco, config = init(discovery_url, oauth_config_file)


def authenticated(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('authenticated'):
            return authenticate()

        return f(*args, **kwargs)

    return wrapper


@app.after_request
def add_header(r):
    if app.config['DEBUG']:
        r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        r.headers['Pragma'] = 'no-cache'
        r.headers['Expires'] = '0'
    return r


#
# Web UI -- single page app that lets a user manage existing names,
# create new names, see stats about what names are used, etc.
#

@app.route("/")
@authenticated
def index():
    return send_file('static/index.html')


#
# Authentication endpoint
#

@app.route("/!/auth", methods=['GET'])
def auth():
    "The second step of the OAuth dance."
    args = request.args

    # The browser is redirected to this endpoint by Google and will
    # pass us the state we embedded in the URL we redirected them to
    # in step one of the dance. We need to check that the state we are
    # receiving now is one we handed out before, otherwise anyone
    # could hit this endpoint, pretending to have been redirected
    # here. They probably wouldn't be able to authenticate since they
    # wouldn't have a valid code to give us (which we will then POST
    # to google). It seems sufficient to put the state we are
    # expecting into our session before we redirect them in step one
    # since sessions are not forgeable.

    if 'state' not in session or args['state'] != session['state']:
        return 'Bad state', 401

    token_endpoint = disco['token_endpoint']
    code           = args['code']
    client_id      = config['client_id']
    client_secret  = config['client_secret']
    uri            = config['redirect_uris'][0]

    resp = postback(token_endpoint, code, client_id, client_secret, uri)

    # TODO: Check nonce hasn't been seen before, etc. and then return
    # a redirect to wherever they were trying to go (recorded in
    # state) when we forced the authentication.

    if resp is not None:
        jwt = resp['jwt']['payload']
        session['authenticated'] = True
        session['email'] = jwt['email']
        session['domain'] = jwt['hd'] if 'hd' in jwt else ''
        return redirect(decode_state(session['state']))
    else:
        return jsonify({'args': args, 'response': resp}), 401


@app.route("/!/logout", methods=['GET'])
def logout():
    session['authenticated'] = False
    return "Okay", 200


@app.route("/!/user", methods=['GET'])
@authenticated
def user():
    data = {'email': session['email'], 'domain': session['domain']}
    return jsonify(data), 200


#
# The actual redirector.
#

@app.route("/<name>/", defaults={'rest': None})
@app.route("/<name>/<path:rest>")
@authenticated
def redirection(name, rest):
    name = ''.join(filter(str.isalnum, name))
    args = rest.split('/') if rest else []
    if db.has_pattern(name, len(args)):
        return redirect(db.get_pattern(name, len(args)).format(*args)), 307
    else:
        # TODO: need to check login here.
        return send_file('static/index.html')


#
# API - Restful API for CRUDing links.
#

@app.route("/_/", methods=['GET'])
@authenticated
def get_all():
    return jsonify(jsonify_db(db))


@app.route("/_/<name>", methods=['GET'])
@authenticated
def get_name(name):
    if db.has_name(name):
        return jsonify(jsonify_item(db, name))
    else:
        return jsonify({}), 404


@app.route("/_/<name>", methods=['POST'])
@authenticated
def post_pattern(name):
    pattern = request.form['pattern']
    n = count_args(pattern)
    if n is None:
        # FIXME: there's more well-formedness checking we could do
        # on the pattern.
        return jsonify({"error": "Mixed arg types"}), 400
    else:
        db.set_pattern(name, n, pattern)
        r = jsonify(jsonify_item(db, name))
        r.headers['Location'] = '/_/{}/{}'.format(name, n)
        return r, 201


@app.route("/_/<name>", methods=['DELETE'])
@authenticated
def delete_name(name):
    if db.has_name(name):
        db.delete_name(name)
        return jsonify({})
    else:
        return jsonify({"error": "No such name"}), 404


@app.route("/_/<name>/<int:n>", methods=['DELETE'])
@authenticated
def delete_pattern(name, n):
    if db.get_pattern(name, n):
        db.delete_pattern(name, n)
        return jsonify(jsonify_item(db, name))
    else:
        return jsonify({"error": "No such pattern"}), 404


#
# Utilities
#

def count_args(pattern):
    numbered_pats = re.findall('{\d+}', pattern)
    auto_pats = re.findall('{}', pattern)

    if numbered_pats and auto_pats:
        return None  # Poor man's Maybe
    elif numbered_pats:
        return 1 + max(int(x.strip('{}')) for x in numbered_pats)
    else:
        return len(auto_pats)


def jsonify_db(db):
    "Convert whole db into the JSON we send in API responses."
    return [jsonify_item(db, name) for name in db.names()]


def jsonify_item(db, name):
    "Convert one item into the JSON we send in API responses."
    patterns = [{'pattern': p, 'args': n} for n, p in db.get_patterns(name)]
    return {'name': name, 'patterns': patterns}


def authenticate():
    auth_endpoint = disco['authorization_endpoint']
    client_id = config['client_id']
    uri = config['redirect_uris'][0]

    state = encode_state(request.url)
    nonce = urandom(8).hex()

    session['state'] = state
    return redirect(auth_url(auth_endpoint, client_id, uri, state, nonce)), 302

def encode_state(url):
    return quote(urandom(16).hex() + request.url)

def decode_state(state):
    return unquote(state)[32:]
