import os
import json

import config
from chart import create_chart

from pprint import pformat
from markupsafe import escape

from flask import Flask, request, render_template

app = Flask(__name__)

cfg = config.Config(config.CONFIG_PATH)


@app.route("/")
def index():
    try:
        # try using a custom range selection
        time_range = int(escape(request.args.get("range")))
        if time_range <= 0:
            time_range = None
    except ValueError:
        time_range = cfg.default_dashboard_days

    # either serve from the cache or re-compute the entire graph
    if time_range == cfg.default_dashboard_days:
        with open(config.CHART_CACHE_PATH) as f:
            chart = f.read()
    else:
        chart = create_chart(last_n_days=time_range)

    return render_template(
        "index.njk",
        plot=chart,
        time_range=time_range,
        receive_timeout=cfg.receive_timeout
    )


@app.route("/api")
def api():
    return render_template("api.njk")


@app.route("/api", methods=["POST"])
def api_post():
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
    with open(config.CONFIG_PATH, "r") as f:
        data = json.load(f)
        if mode == "add":
            if email not in data["targets"]:
                data["targets"].append(email)
        elif mode == "remove":
            if email in data["targets"]:
                data["targets"].remove(email)

    # store new configuration
    if mode == "add" or mode == "remove":
        with open(config.CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)

    return render_template("api.njk", config=pformat(data, indent=4))
