"""
Module to provide plotting functionality
"""

# plotly is only needed in debug/calibration modes — imported lazily inside plot_data()

webroot = "./"


def plot_data(samples, title, ct_selection=None, old_wave=None, sample_rate=None):
    # Plots the raw sample data from the individual CT channels and the AC voltage channel.
    import plotly  # noqa: PLC0415 — deferred: only used in debug/calibration modes
    import plotly.graph_objs as go  # noqa: PLC0415
    from plotly.subplots import make_subplots  # noqa: PLC0415

    if ct_selection is not None:
        # Make plot for a single CT channel
        ct_old = old_wave["ct" + str(ct_selection + 1)]
        ct = samples["ct" + str(ct_selection + 1)]
        voltage = samples["vac"]
        x = list(range(len(voltage)))
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=x, y=ct_old, mode="lines", name=str(ct_selection + 1).upper()), secondary_y=False)
        fig.add_trace(
            go.Scatter(x=x, y=ct, mode="lines", name=f"Phase corrected ct wave ({str(ct_selection + 1).upper()})"),
            secondary_y=False,
        )
        fig.add_trace(go.Scatter(x=x, y=voltage, mode="lines", name="AC Voltage Wave"), secondary_y=True)

    else:
        # Make plot for all CT channels
        ct1 = samples.samples_ct1
        ct2 = samples.samples_ct2
        ct3 = samples.samples_ct3
        ct4 = samples.samples_ct4
        ct5 = samples.samples_ct5
        ct6 = samples.samples_ct6
        voltage = samples.samples_vac
        x = list(range(len(voltage)))

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=x, y=ct1, mode="lines", name="ct1"), secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=ct2, mode="lines", name="ct2"), secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=ct3, mode="lines", name="ct3"), secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=ct4, mode="lines", name="ct4"), secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=ct5, mode="lines", name="ct5"), secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=ct6, mode="lines", name="ct6"), secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=voltage, mode="lines", name="AC Voltage"), secondary_y=True)

        if "vWave_ct1" in samples.samples:
            fig.add_trace(
                go.Scatter(x=x, y=samples["vWave_ct1"], mode="lines", name="New V wave (ct1)"), secondary_y=True
            )
            fig.add_trace(
                go.Scatter(x=x, y=samples["vWave_ct2"], mode="lines", name="New V wave (ct2)"), secondary_y=True
            )
            fig.add_trace(
                go.Scatter(x=x, y=samples["vWave_ct3"], mode="lines", name="New V wave (ct3)"), secondary_y=True
            )
            fig.add_trace(
                go.Scatter(x=x, y=samples["vWave_ct4"], mode="lines", name="New V wave (ct4)"), secondary_y=True
            )
            fig.add_trace(
                go.Scatter(x=x, y=samples["vWave_ct5"], mode="lines", name="New V wave (ct5)"), secondary_y=True
            )
            fig.add_trace(
                go.Scatter(x=x, y=samples["vWave_ct6"], mode="lines", name="New V wave (ct6)"), secondary_y=True
            )

    fig.update_layout(
        title=title,
        xaxis_title="Sample Number",
        yaxis_title="ADC Value (CTs)",
        yaxis2_title="ADC Value (Voltage)",
    )

    div = plotly.offline.plot(fig, show_link=False, output_type="div", include_plotlyjs="cdn")
    home_link = '<a href="/">Back to Index</a>'
    div = home_link + div
    if sample_rate:
        div += f"<p>Sample Rate: {sample_rate} KSPS</p>"

    with open(f"{webroot}/{title.replace(' ', '_')}.html", "w") as f:
        f.write(div)
