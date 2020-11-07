import os
import json

from chart import create_chart
from config import CONFIG_PATH

from pprint import pformat
from markupsafe import escape

from flask import Flask, request, render_template
from flask.helpers import make_response


app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.njk",
        plot=create_chart(theme=escape(request.args.get("theme"))),
    )


@app.route("/api")
def api():
    return render_template("api.njk", content="A")


@app.route("/api", methods=["POST"])
def api_target_add():
    email = escape(request.form.get("email"))
    token = escape(request.form.get("token"))

    # identify clicked button
    mode = "config"
    if escape(request.form.get("add")) is not None:
        mode = "add"
    if escape(request.form.get("remove")) is not None:
        mode = "remove"

    # check if the token exists
    if os.getenv("API_TOKEN") is None:
        return (
            render_template(
                "api.njk",
                warning="No API_TOKEN environment variable was set in the app",
            ),
            500,
        )

    # check if the token matches
    if token != os.getenv("API_TOKEN"):
        return render_template("api.njk", warning="Wrong token supplied"), 401

    # load old configuration
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
        if mode == "add":
            if email not in data["targets"]:
                data["targets"].append(email)
        elif mode == "remove":
            if email in data["targets"]:
                data["targets"].remove(email)

    # store new configuration
    if mode == "add" or mode == "remove":
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)

    return render_template("api.njk", config=pformat(data, indent=4))
