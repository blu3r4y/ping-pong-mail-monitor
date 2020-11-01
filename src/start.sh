#!/bin/sh

# start mail monitoring
python monitor.py &

# start frontend
export FLASK_APP=app.py
export FLASK_ENV=production
export FLASK_DEBUG=0
flask run --host=0.0.0.0 --port=80
