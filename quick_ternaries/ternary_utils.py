"""This module contains functions to help with ternary diagram generation

add_molar_columns accepts a dataframe along with a parameters dictionary
    and performs wt%-to-molar conversion as well as column aggregation
    and returns the same dataframe with additional columns including normalized
    top, left, and right apex columns ready to be plotted on a ternary diagram


"""
import warnings

import pandas as pd
import numpy as np

from molmass import Formula
from molmass.molmass import FormulaError

import plotly.graph_objects as go
import plotly.io as pio

def make_plot_axis(title: str, tickangle: int) -> dict:
    """
    Initialize information for some ternary axis.
    Source: https://plotly.com/python/ternary-plots/
    
    Arguments:
        title: The title for some axis in the ternary.
        tickangle: The angle to rotate the axis' tick marks by.
    """
    return {
        'title': title,
        'titlefont': {'size': 20},
        'tickangle': tickangle,
        'tickfont': {'size': 15},
        'tickcolor': 'rgba(0,0,0,0)',
        'ticklen': 5,
        'showline': True,
        'showgrid': True
    }

def parse_ternary_type(t_type: str, params: dict) -> tuple(list[str]):
    """
    Parse the apice oxides to use in the final ternary.
    
    Arguments:
        t_type: Ternary type. Either a default type (ie "Al2O3 CaO+NaO+K2O FeOT+MgO", 
                "SiO2+Al2O3 CaO+NaO+K2O FeOT+MgO", or "Al2O3 CaO+Na2O K2O") or "Custom"
        params: A dictionary containing keys for each apex whose values correspond to the oxides
                to put on the respective apex.
    Returns:
        (tops, lefts, rights): A tuple containing the oxides to plot on the top, left, and right
                               apices, respectively.

    """
    if t_type != 'Custom':
        top, left, right = t_type.split(' ')
        tops   = top.split('+')
        lefts  = left.split('+')
        rights = right.split('+')
    else:
        tops   = params['top apex selected values']
        lefts  = params['left apex selected values']
        rights = params['right apex selected values']
    return tops, lefts, rights

def get_molar_mass(oxide: str) -> float:
    """
    Obtain the molar mass of an oxide

    Arguments:
        oxide: some oxide formula (ex: Al2O3, MnO, etc.)
    Returns:
        mass: molar mass of input oxide
    """

    mass = np.nan # By default

    if oxide == 'FeOT':
        mass = Formula('FeO').mass
    else:
        try:
            mass = Formula(oxide).mass
        except FormulaError:
            err = 'Encountered a FormulaError trying to calculate the molar mass of'
            err += f' \"{oxide}\". '
            err += f'Ensure all custom apex columns are valid formulae.'
            raise FormulaError(err)
        except ValueError:
            err = 'Encountered a ValueError trying to calculate the molar mass of'
            err += f' \"{oxide}\". '
            err += f'Ensure all custom apex columns are valid formulae.'
            raise ValueError(err)
    return mass

def add_molar_columns(dataframe: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Append columns with molar conversions to the dataframe.
    
    Arguments:
        dataframe: The master datafile with oxide compositions.
        params: 
    Returns:
        temp_df: Original input dataframe with molar conversions appended.
    """

    temp_df = dataframe.copy()

    ternary_type = params['ternary type']
        
    # Get the column names for each apex
    tops, lefts, rights = parse_ternary_type(ternary_type, params)
    
    # Convert all relevant to molar
    for col in tops + lefts + rights:
        mass = get_molar_mass(col)
        try:
            temp_df[f'__{col}_molar'] = temp_df[col] / mass
        except KeyError as err:
            print('Encountered a KeyError while trying to convert column', col, 'to molar')
            print(err)

    # Get normalization values for each row
    temp_df['__molar_normalization'] = sum(temp_df[c] for c in [f'__{col}_molar' for col in tops+lefts+rights])

    # Normalize molar columns by normalization value
    for col in tops + lefts + rights:
        temp_df[f'__{col}_molar_normed'] = temp_df[f'__{col}_molar'] / temp_df['__molar_normalization']

    # Combine vales according to tops/lefts/rights to get apex columns
    temp_df['top_apex_molar_normed'] = sum(
        temp_df[c] for c in [f'__{col}_molar_normed' for col in tops])        
    temp_df['left_apex_molar_normed'] = sum(
        temp_df[c] for c in [f'__{col}_molar_normed' for col in lefts])        
    temp_df['right_apex_molar_normed'] = sum(
        temp_df[c] for c in [f'__{col}_molar_normed' for col in rights])        

    return temp_df # Just for now


def make_ternary_trace(
    dataframe: pd.DataFrame, 
    top_col: str, left_col: str, right_col: str, 
    size_col: str = None, 
    size: float = 4,
    color_col: str = None, 
    use_heatmap: bool = False,
    heatmap_col: str = None,
    cmin: float = None, cmax: float = None,
    colorscale: str = 'matter',
    opacity: float = 1, 
    hoverinfo: str = 'all', 
    trace_hover_title: str = None, 
    pt_hover_titles: list[str] = None) -> go.Scatterternary:
    """
    Create a ternary for some trace.
    
    Arguments:
        dataframe: All data in a given trace.
        top_col:   The name of the column to use for the top   apex.
        left_col:  The name of the column to use for the left  apex.
        right_col: The name of the column to use for the right apex.
        size_col:  The name of the column to use for point sizes.
        size: A constant size to use when plotting all points.
        color_col: The name of the column to use for point color (discrete colormap).
        use_heatmap: Use a heatmap while plotting the points?
        heatmap_col: The name of the column to use for point color (continuous colormap).
        cmin: Lower bound for color domain.
        cmax: Upper bound for color domain.
        colorscale: The name of the px.colors colorscale to use 
                    (ex: "matter", "blues", "viridis", etc.).
        opacity: Point opacity
        hoverinfo: What kind of hover info is displayed. In most cases, this should be set to
                   "all" to display all hover info. In some cases, it can be beneficial to set
                   to "skip" disable hover info.
        trace_hover_title: Hover data title for all point's in the given trace.
                           A resulting legend will be displayed next to the ternary.
        pt_hover_titles: Hover data title(s) for each point. If a single string, 
                         the same string appears over all the data points. If an array of strings,
                         the items are mapped in order to the the data points in (a,b,c).
    Returns:
        trace: A plotly graph_objects Scatterternary object
    """

    marker_dict = {}
    if np.issubdtype(type(size), np.number):
        marker_dict |= {'size': [size] * len(dataframe)}
    if size_col:
        # Override the fixed "size" value with a size column
        marker_dict |= {'size':  dataframe[size_col]}
    if color_col:
        marker_dict |= {'color': dataframe[color_col]}
    if opacity:
        marker_dict |= {'opacity': opacity}

    if use_heatmap and heatmap_col:
        marker_dict |= {'color': dataframe[heatmap_col]}
        marker_dict |= {'colorscale': colorscale}
        marker_dict |= {'colorbar': {'title': heatmap_col}}
        #marker_dict |= {'cmin': 0, 'cmax': 1}

    
    if cmin:
        cmin = float(cmin)
        marker_dict |= {'cmin': cmin}
        # TODO raise appropriate errmsg
    if cmax:
        cmax = float(cmax)
        marker_dict |= {'cmax': cmax}
        # TODO raise appropriate errmsg


    trace = go.Scatterternary(
        a=dataframe[top_col],   # Top
        b=dataframe[left_col],  # Left
        c=dataframe[right_col], # Right
        mode='markers',
        marker=marker_dict,
        hoverinfo=hoverinfo, 
        name = trace_hover_title,
        text =    pt_hover_titles)

    return trace

def plot_ternary(
    traces: list[go.Scatterternary], 
    title: str, 
    top_apex_name:   str, 
    left_apex_name:  str, 
    right_apex_name: str, 
    bordercolor='white') -> go.Figure:
    """
    Create the final ternary to display.
    
    Arguments:
        traces: A list of all traces to overlay onto the final ternary.
        title: Ternary title.
        top_apex_name:   Top apex title.
        left_apex_name:  Left apex title.
        right_apex_name: Right apex title.
        bordercolor: Point border color.
    Returns:
        fig: A plotly graph_object Figure with the Scatterternary traces plotted.
    """

    print('plotting...')
    warnings.filterwarnings(action='ignore', category=RuntimeWarning)

    fig = go.Figure(
        data = traces,
        layout = {'title': title})
    fig.update_traces(
        marker=dict(
            line=dict(
                width=0.2,
                color=bordercolor)),
        selector=dict(
            mode='markers'))
    fig.update_layout(
        {'ternary':
            {'sum': 100,
            'aaxis': make_plot_axis(top_apex_name, 0),
            'baxis': make_plot_axis(f'<br>{left_apex_name}', 60),
            'caxis': make_plot_axis(f'<br>{right_apex_name}', -60)}},
        legend= {'itemsizing': 'constant'})

    return fig