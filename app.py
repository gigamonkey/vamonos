from collections import defaultdict
from flask import Flask, redirect, render_template, request
import re

# We use HTTP 307 in order to continue to get a chance to see people
# using go links, mainly so the redirection can change.

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = defaultdict(dict)
redirects['goog'][0] = 'https://www.google.com/'
redirects['goog'][1] = 'https://www.google.com/search?q={}'

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

    return render_template('name.html', name=name, patterns=redirects[name], error=error)

@app.route("/<name>/", defaults={'rest': None})
@app.route("/<name>/<path:rest>")
def redirection(name, rest):
    name = ''.join(filter(str.isalnum, name))
    args = rest.split('/') if rest else []
    if len(args) in redirects[name]:
        return redirect(redirects[name][len(args)].format(*args), code=307)
    else:
        return redirect('/_/' + name)

def count_args(pattern):
    numbered_pats = re.findall('{\d+}', pattern)
    auto_pats     = re.findall('{}', pattern)

    if numbered_pats and auto_pats:
        raise ValueError("Can't mix explictly numbered and auto-numbered patterns.")
    elif numbered_pats:
        return 1 + max(int(x.strip('{}')) for x in numbered_pats)
    else:
        return len(auto_pats)
