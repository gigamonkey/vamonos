from flask import Flask, redirect, render_template, request

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = {}
redirects['goog'] = 'https://www.google.com/search?q={}'


@app.route("/$create$/", methods=['POST'])
def create():
    redirects[request.form['name']] = request.form['url']
    return redirect('/' + request.form['name'], code=302)


@app.route("/<name>/", defaults={'rest': None})
@app.route("/<name>/<path:rest>")
def redirection(name, rest):
    name = depunctuate(name)
    if name in redirects:
        args = rest.split('/') if rest else []
        return redirect(redirects[name].format(*args), code=307)
    else:
        return render_template('missing.html', name=name)


def depunctuate(name):
    return ''.join(filter(str.isalnum, name))
