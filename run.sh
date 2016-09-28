#!/bin/tcsh

setenv FLASK_DEBUG 0
setenv FLASK_APP alac.py
flask run --host=0.0.0.0
