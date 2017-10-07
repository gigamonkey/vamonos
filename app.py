from flask import Flask, redirect, render_template, request

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = {}
redirects['goog'] = 'https://google.com'

@app.route("/API/create/", methods=['POST'])
def create():
    redirects[request.form['name']] = request.form['url']
    return redirect('/' + request.form['name'], code=302)

@app.route("/<name>")
def redirection(name):
    if name in redirects:
        return redirect(redirects[name], code=307)
    else:
        return render_template('missing.html', name=name)
