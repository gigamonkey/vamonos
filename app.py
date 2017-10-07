from flask import Flask, redirect, render_template

app = Flask(__name__)

redirects = {}
redirects['goog'] = 'https://google.com'

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/<shortname>")
def redirection(shortname):
    if shortname in redirects:
        return redirect(redirects[shortname], code=307, Response=None)
    else:
        return render_template('missing.html', shortname=shortname)
