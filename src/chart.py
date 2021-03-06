import json

from datetime import timedelta

from config import QUEUE_PATH

import numpy as np
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go

from plotly.utils import PlotlyJSONEncoder
from plotly.subplots import make_subplots


def create_chart(theme=None):
    if theme is None or theme not in pio.templates:
        theme = "plotly_dark"  # see https://plotly.com/python/templates/

    data = _read_chart_data()
    df = data["df"]

    # subplot for each target
    fig = make_subplots(rows=len(data["targets"]), cols=1, shared_xaxes=True, vertical_spacing=0.01)

    for i, target in enumerate(data["targets"]):
        # the latency line plot
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[target],
                name=target,
                mode="lines",
                connectgaps=False,
            ),
            col=1,
            row=i + 1,
        )

        # the expired mails scatter dots (place the dot at the median latency)
        exp_x = data["expired"][target].index
        exp_y = np.full(data["expired"][target].shape[0], df[target].median())
        fig.add_trace(
            go.Scatter(
                x=exp_x,
                y=exp_y,
                name="fail",
                mode="markers",
                showlegend=False,
                marker=dict(size=10, color="red"),
            ),
            col=1,
            row=i + 1,
        )

        # y axis title
        fig.update_yaxes(title_text="RTT", col=1, row=i + 1)

    # clear height and width for a auto-scaled figure
    # and possibly set a supplied theme (or the default)
    fig.update_layout(
        height=None,
        width=None,
        title_text="Ping Pong Mail Monitor (RTT in Minutes - Red Dots are Lost Mails)",
        template=theme,
    )

    graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
    return graphJSON


def _read_chart_data():
    with open(QUEUE_PATH) as f:
        data = json.load(f)

    targets = [e.split(":")[1] for e in data.keys() if e.startswith("latency:")]

    latencies = []  # stores multiple dataframes which are later concatenated
    expired = {}  # stores a view only on the expired mails

    for target in targets:
        df_ = pd.DataFrame.from_dict(data["latency:" + target], orient="index")
        df_.columns = [target]

        # convert latency to datetime dtype
        df_.index = pd.to_datetime(df_.index, unit="ms")

        # set timeout values to NaN and convert to seconds
        df_.loc[df_[target] == -1, target] = np.nan
        df_[target] /= 1000 * 60

        # get a view on all the failed mails
        expired[target] = df_.loc[df_[target].isnull(), :].copy()

        # insert NaN rows if there is no datapoint recorded
        # for longer than twice the median distance
        # to visually indicate an monitoring outage with plotly then
        diffs = df_.index.to_series().diff()
        gaps = diffs[diffs >= diffs.median() * 2].index - timedelta(seconds=1)
        for gap in gaps:
            df_.loc[gap, target] = np.nan

        # sort timestamps (otherwise, plotly will not sort them)
        df_.sort_index(inplace=True)

        # add temporary frame
        latencies.append(df_)

    # merge all columns
    df = pd.concat(latencies)

    return dict(targets=targets, df=df, expired=expired)
