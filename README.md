# Vámonos

Simple link redirector. Because the world for sure needs another one of these.

This one does have a few features that I care about:

- Names can have multiple patterns. E.g. go/goog can redirect to http://google.com while go/goog/foo redirects to https://www.google.com/search?q=foo. (We fall back to the no-arg pattern if there isn't a pattern defined for the number of elements after the name on the path.)
- Supports OAuth authentication with your Google account.

## Setup

```bash
virtualenv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```
