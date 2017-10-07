from collections import defaultdict
from flask import Flask, redirect, render_template, request
import re

# We use HTTP 307 mainly so the redirection can change. This also
# allows us to log the use of links.

# TODO:
#
# - External storage of db. (JSON)
# - Move to static frontend with API.
# - External storage of db. (Real db)

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = defaultdict(dict)
redirects['goog'][0] = 'https://www.google.com/'
redirects['goog'][1] = 'https://www.google.com/search?q={}'

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
