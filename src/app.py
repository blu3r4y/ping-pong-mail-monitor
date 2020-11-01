import os
import json

from config import CONFIG_PATH

from pprint import pformat
from markupsafe import escape

from flask import Flask, request, render_template
from flask.helpers import make_response


app = Flask(__name__)


@app.route("/")
def index():
    template = """
    Not implemented yet.
    """
    return template


@app.route("/target/add/<mail>")
def target_add(mail):
    mail = str(escape(mail))

    if os.getenv("API_TOKEN") is None:
        return make_response("no API_TOKEN environment variable set", 500)
    if request.args.get("token") != os.getenv("API_TOKEN"):
        return make_response("wrong API_TOKEN", 401)

    # load old configuration
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
        if mail not in data["targets"]:
            data["targets"].append(mail)

    # store new configuration
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

    return render_template(
        "target.html", title="JKU OEH Mail Monitor", content=pformat(data, indent=4)
    )


@app.route("/target/remove/<mail>")
def target_remove(mail):
    mail = str(escape(mail))

    if os.getenv("API_TOKEN") is None:
        return make_response("no API_TOKEN environment variable set", 500)
    if request.args.get("token") != os.getenv("API_TOKEN"):
        return make_response("wrong API_TOKEN", 401)

    # load old configuration
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
        if mail in data["targets"]:
            data["targets"].remove(mail)

    # store new configuration
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

    return render_template(
        "target.html", title="JKU OEH Mail Monitor", content=pformat(data, indent=4)
    )
