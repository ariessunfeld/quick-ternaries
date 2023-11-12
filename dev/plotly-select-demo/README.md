# Overview

This folder contains a demo for how to connect a plotly ternary view inside a GUI in such a way that when points get selected with the Lasso tool on the Plotly plot, these points can be accessed and modified within Python.

# Usage

This demo contains a GUI with two buttons. The first button is Load Data. Click this and select the dataframe `df8.csv`. The code assumes the csv you select will have columns A, B, C for ternary data. 

After loading, the data will appear plotted on your ternary diagram in the GUI. Hover over the ternary and select the Lasso tool. Then use it to select one or more points on the ternary diagram. Then click `Change Color`. A color-picker will appear. Select the target color and then hit `Ok`. The points you selected will change to that color.

# Setup

To run this demo, make a virtual environment with `python3.11 -m venv venv`, activate it with `source venv/bin/activate`, and install the packages with `pip install -r select_demo_reqs.txt`. Then run `python main.py`.

