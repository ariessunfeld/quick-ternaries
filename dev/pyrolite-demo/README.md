# Overview

This folder contains a demonstration of how to use pyrolite to obtain a confidence region at 1-sigma (setting a contour line to cover 68% of the points), then extracting and converting that contour line data into a format compatible with Plotly, and plotting it.

`main.py` expects the presence of a file called `df8.csv` which has columns `A`, `B`, and `C`.

# Setup

To run `main.py`, make a new virtual environment by running `python3.11 -m venv venv` and then installing the necessary packages with `source venv/bin/activate` followed by `pip install -r pyro_demo_reqs.txt`.
