import json

from time import time
from datetime import timedelta

from config import QUEUE_PATH

import oneagent
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from plotly.utils import PlotlyJSONEncoder
from plotly.subplots import make_subplots

from loguru import logger

oneagent.initialize()
sdk = oneagent.get_sdk()


def create_chart(last_n_days=None):
    render_start = time()

    with sdk.trace_custom_service("readChartData", "PingPongMailMonitor"):
        data = _read_chart_data(last_n_days=last_n_days)
    df = data["df"]

    fig = make_subplots(
        rows=len(data["targets"]), cols=1,
        shared_xaxes=True, vertical_spacing=0.01
    )

    for i, target in enumerate(data["targets"]):
        # the latency line plot
        fig.add_trace(
            go.Scattergl(
                x=df.index, y=df[target], name=target,
                mode="lines", connectgaps=False,
            ), col=1, row=i + 1,
        )

        # the expired mails scatter dots (place the dot at the median latency)
        expired_times = data["expired"][target].index
        expired_median = np.full(data["expired"][target].shape[0], df[target].median())
        fig.add_trace(
            go.Scattergl(
                x=expired_times, y=expired_median, name="expired mail",
                mode="markers", showlegend=False, marker=dict(size=10, color="red"),
            ), col=1, row=i + 1,
        )

        # y axis title and cap upper range to 60 minutes
        fig.update_yaxes(title_text="RTT", col=1, row=i + 1,
                         range=[0, min(60, df[target].max())])

        # center the legend at the bottom
        fig.update_layout(legend=dict(
            orientation="h",
            xanchor="center", yanchor="top",
            x=0.5, y=-0.05))

    # clear height and width for a auto-scaled figure
    fig.update_layout(
        height=None, width=None,
        template="plotly_dark")

    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)

    render_time = timedelta(seconds=time() - render_start)
    logger.info(f"chart computation took {render_time} (for {last_n_days} days)")

    return graph_json


def _read_chart_data(last_n_days=None):
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
        df_.sort_index(inplace=True)

        # set timeout values to NaN and convert to seconds
        df_.loc[df_[target] == -1, target] = np.nan
        df_[target] /= 1000 * 60

        # get a view on all the failed mails
        expired[target] = df_.loc[df_[target].isnull(), :].copy()

        # insert NaN rows if there is no datapoint recorded
        # for longer than twice the median distance
        # to visually indicate an monitoring outage with plotly then
        assert df_.index.is_monotonic_increasing
        diffs = df_.index.to_series().diff()
        gaps = np.flatnonzero(diffs >= diffs.median() * 2)
        for gap in gaps:
            # insert an NaN between the last two points that we saw
            a, b = df_.index[gap - 1], df_.index[gap]
            midpoint = (b - a) / 2 + a
            df_.loc[midpoint, target] = np.nan

        # sort timestamps (otherwise, plotly will not sort them)
        df_.sort_index(inplace=True)

        # add temporary frame
        latencies.append(df_)

    # merge all columns
    df = pd.concat(latencies)

    # possibly truncate the entire range
    if last_n_days is not None:
        cutoff = pd.Timestamp.today() - timedelta(days=last_n_days)
        df = df[df.index >= cutoff]

    df.sort_index()
    return dict(targets=targets, df=df, expired=expired)
