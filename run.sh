#!/bin/sh

export FLASK_DEBUG=1
export FLASK_APP=alac.py
flask run --host=0.0.0.0 --port=80
