from flask import Flask, redirect, render_template, request

app = Flask(__name__)

app.config['DEBUG'] = True

redirects = {}
redirects['goog'] = 'https://google.com'

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/API/create/", methods=['POST'])
def create():
    return request.form['url']

@app.route("/<shortname>")
def redirection(shortname):
    if shortname in redirects:
        return redirect(redirects[shortname], code=307, Response=None)
    else:
        return render_template('missing.html', shortname=shortname)
