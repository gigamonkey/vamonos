from collections import defaultdict
from flask import Flask, redirect, render_template, request
import re

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = defaultdict(dict)
redirects['goog'][0] = 'https://www.google.com/'
redirects['goog'][1] = 'https://www.google.com/search?q={}'

@app.route("/_/<name>", methods=['GET'])
def show(name):
    return render_template('name.html', name=name, patterns=redirects[name])

@app.route("/_/<name>", methods=['POST'])
def create(name):
    pattern = request.form['url']
    try:
        redirects[name][count_args(pattern)] = pattern
        return redirect('/_/' + name)
    except ValueError as e:
        return str(e)

@app.route("/<name>/", defaults={'rest': None})
@app.route("/<name>/<path:rest>")
def redirection(name, rest):
    name = depunctuate(name)
    if name in redirects:
        args = rest.split('/') if rest else []
        return redirect(redirects[name][len(args)].format(*args), code=307)
    else:
        return redirect('/_/' + name)


def depunctuate(name):
    return ''.join(filter(str.isalnum, name))


def count_args(pattern):
    numbered_pats = re.findall('{\d+}', pattern)
    auto_pats     = re.findall('{}', pattern)

    if numbered_pats and auto_pats:
        raise ValueError("Can't mix explictly numbered and auto-numbered patterns.")
    elif numbered_pats:
        return 1 + max(int(x.strip('{}')) for x in numbered_pats)
    else:
        return len(auto_pats)
