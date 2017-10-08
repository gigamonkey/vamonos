from collections import defaultdict
from flask import Flask, Response, redirect, request, send_file
import json
import re

# We use HTTP 307 mainly so the redirection can change. This also
# allows us to log the use of links.

# TODO:
#
# - Clean up JSON returned by API.
# - Thread safe external storage of db.

app = Flask(__name__)

app.config['DEBUG'] = True

db = None


@app.before_first_request
def _run_on_start():
    global db
    db = load_db()


#
# Web UI -- single page app that lets a user manage existing names,
# create new names, see stats about what names are used, etc.
#

@app.route("/")
def home():
    return send_file('static/index.html')


#
# The actual redirector.
#

@app.route("/<name>/", defaults={'rest': None})
@app.route("/<name>/<path:rest>")
def redirection(name, rest):
    name = ''.join(filter(str.isalnum, name))
    args = rest.split('/') if rest else []
    if len(args) in db[name]:
        return redirect(db[name][len(args)].format(*args))
    else:
        return send_file('static/index.html')


#
# API - Restful API for CRUDing links.
#

@app.route("/_/")
def all():
    return json_response(new_json(db))


@app.route("/_/<name>", methods=['GET'])
def get_name(name):
    js, code = (db[name], 200) if name in db else ({}, 404)
    return json_response(js, code)


@app.route("/_/<name>", methods=['DELETE'])
def delete_name(name):
    if name in db:
        del db[name]
        save_db(db)
        return json_response({})
    else:
        return json_response({"error": "No such name"}, 404)


@app.route("/_/<name>/<path:pattern>", methods=['PUT'])
def put_pattern(name, pattern):
    error = None
    n = count_args(pattern)
    if n is None:
        # FIXME: there's more well-formedness checking we could do
        # on the pattern.
        error = "Mixed arg types."
    else:
        db[name][n] = pattern
        save_db(db)

    if error:
        return json_response({"error": error}, 400)
    else:
        return json_response(db[name])


@app.route("/_/<name>/<path:pattern>", methods=['DELETE'])
def delete_pattern(name, pattern):
    d = db[name]
    n = count_args(pattern)
    if n is not None and n in d and d[n] == pattern:
        del d[n]
        save_db(db)
        return json_response(db[name])
    else:
        return json_response({"error": "No such pattern"}, 404)



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


def json_response(js, code=200):
    return Response(json.dumps(js), status=code, mimetype='application/json')


#
# DB
#

def save_db(db):
    with open("db.json", "w") as f:
        json.dump(db, f)


def load_db():
    with open("db.json") as f:
        raw = json.load(f)
    db = defaultdict(dict)
    for (name, patterns) in raw.items():
        for (n, pattern) in patterns.items():
            db[name][int(n)] = pattern
    return db


def new_json(old):
    db = []
    for (name, patterns) in old.items():
        item = {'name': name, 'patterns': []}
        for (n, pattern) in patterns.items():
            item['patterns'].append({'pattern': pattern, 'args': int(n)})
        db.append(item)
    return db
