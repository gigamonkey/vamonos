from db import DB
from flask import Flask, Response, redirect, request, send_file
import json
import re

# We use HTTP 307 mainly so the redirection can change. This also
# allows us to log the use of links.

# TODO:
#
# - Thread safe external storage of db.
# - Use http://fontawesome.io/ icons in Web UI.

app = Flask(__name__)

app.config['DEBUG'] = True

db = None


@app.before_first_request
def _run_on_start():
    global db
    db = DB("db.json")


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
    if db.has_pattern(name, len(args)):
        return redirect(db.get_pattern(name, len(args)).format(*args))
    else:
        return send_file('static/index.html')


#
# API - Restful API for CRUDing links.
#

@app.route("/_/", methods=['GET'])
def get_all():
    return json_response(db.jsonify())


@app.route("/_/<name>", methods=['GET'])
def get_name(name):
    if db.has_name(name):
        return json_response(db.jsonify_item(name))
    else:
        return json_response({}, 404)


@app.route("/_/<name>", methods=['DELETE'])
def delete_name(name):
    if db.has_name(name):
        db.delete_name(name)
        return json_response({})
    else:
        return json_response({"error": "No such name"}, 404)


@app.route("/_/<name>/<path:pattern>", methods=['PUT'])
def put_pattern(name, pattern):
    n = count_args(pattern)
    if n is None:
        # FIXME: there's more well-formedness checking we could do
        # on the pattern.
        return json_response({"error": "Mixed arg types"}, 400)
    else:
        db.set_pattern(name, n, pattern)
        return json_response(db.jsonify_item(name))


@app.route("/_/<name>/<int:n>", methods=['DELETE'])
def delete_pattern(name, n):
    if db.get_pattern(name, n):
        db.delete_pattern(name, n)
        return json_response(db.jsonify_item(name))
    else:
        return json_response({"error": "No such pattern"}, 404)


#
# Utilities
#

def json_response(js, code=200):
    return Response(json.dumps(js), status=code, mimetype='application/json')


def count_args(pattern):
    numbered_pats = re.findall('{\d+}', pattern)
    auto_pats = re.findall('{}', pattern)

    if numbered_pats and auto_pats:
        return None  # Poor man's Maybe
    elif numbered_pats:
        return 1 + max(int(x.strip('{}')) for x in numbered_pats)
    else:
        return len(auto_pats)
