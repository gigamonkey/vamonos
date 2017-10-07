from flask import Flask, redirect

app = Flask(__name__)

redirects = {}
redirects['goog'] = 'https://google.com'

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/<shortname>")
def redirection(shortname):
    return redirect(redirects[shortname], code=307, Response=None)
