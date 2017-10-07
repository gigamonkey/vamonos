from collections import defaultdict
from flask import Flask, redirect, render_template, request
import json
import re

# We use HTTP 307 mainly so the redirection can change. This also
# allows us to log the use of links.

# TODO:
#
# - Delete patterns and whole names.
# - Move to static frontend with API.
# - External storage of db. (Real db)

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = None

@app.before_first_request
def _run_on_start():
    global redirects
    redirects = load_db()

@app.route("/")
def home():
    names = [ (n, sorted(d.items())) for (n, d) in sorted(redirects.items()) ]
    return render_template('home.html', names=names)

@app.route("/_/<name>", methods=['GET', 'POST'])
def manage(name):
    error = None
    if request.method == 'POST':
        pattern = request.form['url']
        try:
            # FIXME: there's more well-formedness checking we could do
            # on the pattern.
            redirects[name][count_args(pattern)] = pattern
        except ValueError as e:
            error = str(e)
        save_db(redirects)

    patterns = sorted(redirects[name].items())
    return render_template('name.html', name=name, patterns=patterns, error=error)

@app.route("/<name>/", defaults={'rest': None})
@app.route("/<name>/<path:rest>")
def redirection(name, rest):
    name = ''.join(filter(str.isalnum, name))
    args = rest.split('/') if rest else []
    url  = redirects[name][len(args)].format(*args) if len(args) in redirects[name] else '/_/' + name
    return redirect(url)

def count_args(pattern):
    numbered_pats = re.findall('{\d+}', pattern)
    auto_pats     = re.findall('{}', pattern)

    if numbered_pats and auto_pats:
        raise ValueError("Can't mix explictly numbered and auto-numbered patterns.")
    elif numbered_pats:
        return 1 + max(int(x.strip('{}')) for x in numbered_pats)
    else:
        return len(auto_pats)


#
# DB
#

def save_db(db):
    with open("db.json", "w") as f: json.dump(db, f)

def load_db():
    with open("db.json") as f: raw = json.load(f)
    db = defaultdict(dict)
    for (name, patterns) in raw.items():
        for (n, pattern) in patterns.items():
            db[name][int(n)] = pattern
    return db
