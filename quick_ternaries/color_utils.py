"""This module contains color utilities for Plotly ternaries"""

NAMED_CSS_COLORS = [
    'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 
    'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 
    'chartreuse', 'chocolate', 'coral', 'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 
    'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgrey', 'darkgreen', 
    'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 
    'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey', 
    'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 
    'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 
    'ghostwhite', 'gold', 'goldenrod', 'gray', 'grey', 'green', 'greenyellow', 'honeydew', 
    'hotpink', 'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush', 
    'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 
    'lightgray', 'lightgrey', 'lightgreen', 'lightpink', 'lightsalmon', 'lightseagreen', 
    'lightskyblue', 'lightslategray', 'lightslategrey', 'lightsteelblue', 'lightyellow', 
    'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 
    'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 
    'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 
    'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 
    'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 
    'peru', 'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown', 'royalblue', 
    'rebeccapurple', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 
    'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey', 'snow', 
    'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violet', 
    'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen'
]

"""
Ari: 
In plotly, when I'm making a ternary with plotly.graph_objects.figure, 
I have the option to add a heatmap. Usually I give it a continuous numeric 
scale, and it automatically creates a continuous color gradient heatmap of 
my points based on the range and the specific colorscale to use (eg "coolwarm" 
or "matter"). I'm wondering if there's any way to extract these RGB values 
that it generates for the points and put them into a list or a dataframe?
"""

"""
ChatGPT 4:
Plotly doesn't provide a straightforward way to extract the exact RGB values 
it uses to colorize points in a heatmap. These values are calculated and 
applied during rendering, which occurs on the client-side in a web browser 
and is not directly accessible from the Python process that generates the plot.
However, it is possible to reproduce the color mapping process yourself. Here's 
how you could do it:

1. Identify the colormap used in the plot. This is the colorscale attribute of the heatmap.

2. Determine the range of your data. This can be done with functions like np.min and np.max.

3. Normalize your data to the range [0, 1] by subtracting the minimum value and dividing by 
    the maximum value.

4. Map the normalized data to the colorscale.

This process is quite involved and it requires understanding how Plotly's color scales work. Here is an example:
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# let's say your data looks like this
data = np.random.rand(10, 10)

# choose a colorscale
colorscale = px.colors.sequential.Plasma

# find min and max
data_min, data_max = np.min(data), np.max(data)

# normalize data
data_norm = (data - data_min) / (data_max - data_min)

# get number of colors in the colorscale
n_colors = len(colorscale)

# map normalized data to colorscale
rgb_values = [colorscale[int(val*(n_colors-1))] for val in data_norm.flatten()]

# now rgb_values is a list of color strings from the colorscale


"""
Note: The colorscales in Plotly Express (px.colors) are represented as lists of 
CSS-compatible color strings. Some colorscales (like Jet) are represented as a 
list of [number, color] pairs; to use these colorscales, you'll need to interpolate 
between the colors.

Also, this example works for a linear colorscale. If your data or your colorscale 
is not linear, you'll need to adjust the normalization and mapping steps accordingly.
"""


"""
Ari:
I think I'll only be using linear colorscales for now. 
Can you show me how I would do the interpolation?
"""

"""
ChatGPT 4:
Certainly! To perform color interpolation, you'll need a colorscale where each 
color is associated with a number between 0 and 1, represented as pairs of 
[number, color]. Many of Plotly's built-in colorscales are of this format.

For interpolation, we can make use of the matplotlib.colors module, which 
provides a function LinearSegmentedColormap.from_list that creates a colormap 
from a list of colors, which we can use to get the interpolated colors.

Here's an example of how to perform interpolation with a colorscale like that:
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import plotly.graph_objects as go

# Your data. For simplicity, we're just generating some random data.
data = np.random.rand(10, 10)

# Choose a colorscale
colorscale = go.figure_factory._mesh._DEFAULT_A_COLORSCALE  # This is one of Plotly's built-in colorscales

# Convert the colorscale to Matplotlib's format and create a colormap
colors = [color for scale, color in colorscale]
colormap = mcolors.LinearSegmentedColormap.from_list("colormap", colors)

# Normalize data to range [0, 1]
data_min, data_max = np.min(data), np.max(data)
data_norm = (data - data_min) / (data_max - data_min)

# Map the normalized data to the colorscale
rgb_values = colormap(data_norm)

# Now rgb_values is a numpy array of shape (10, 10, 3), where the last dimension represents RGB colors.
