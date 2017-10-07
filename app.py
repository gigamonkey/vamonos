from collections import defaultdict
from flask import Flask, redirect, render_template, request
import re

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = defaultdict(dict)
redirects['goog'][0] = 'https://www.google.com/'
redirects['goog'][1] = 'https://www.google.com/search?q={}'

@app.route("/$create$/", methods=['POST'])
def create():
    name    = request.form['name']
    pattern = request.form['url']
    redirects[name][count_args(pattern)] = pattern
    return redirect('/' + request.form['name'], code=302)


@app.route("/<name>/", defaults={'rest': None})
@app.route("/<name>/<path:rest>")
def redirection(name, rest):
    name = depunctuate(name)
    if name in redirects:
        args = rest.split('/') if rest else []
        return redirect(redirects[name][len(args)].format(*args), code=307)
    else:
        return render_template('missing.html', name=name)


def depunctuate(name):
    return ''.join(filter(str.isalnum, name))


def count_args(pattern):
    return len(re.findall('{\d*}', pattern))
