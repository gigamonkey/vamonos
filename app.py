from flask import Flask, redirect

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/goog")
def goog():
    return redirect("https://google.com", code=307, Response=None)
