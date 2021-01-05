import os
import json

from config import CONFIG_PATH, CHART_CACHE_PATH

from pprint import pformat
from markupsafe import escape

from flask import Flask, request, render_template


app = Flask(__name__)


@app.route("/")
def index():
    with open(CHART_CACHE_PATH) as f:
        chart = f.read()

    return render_template(
        "index.njk",
        plot=chart,
    )


@app.route("/api")
def api():
    return render_template("api.njk")


@app.route("/api", methods=["POST"])
def api_target_add():
    email = str(escape(request.form.get("email")))
    token = str(escape(request.form.get("token")))

    # identify clicked button
    mode = "config"
    if escape(request.form.get("add")) == "":
        mode = "add"
    if escape(request.form.get("remove")) == "":
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
