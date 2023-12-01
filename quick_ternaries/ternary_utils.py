"""This module contains functions to help with ternary diagram generation"""

import pandas as pd
import numpy as np

from molmass import Formula
from molmass.molmass import FormulaError

import plotly.graph_objects as go
from plotly.subplots import make_subplots

class MolarMassCalculator:
    def __init__(self, formula_list):
        self.formula_list = formula_list
        # Flatten the list of formulas for easier processing
        self.all_formulae = [formula for apex in formula_list for formula in apex]

    def _get_molar_mass(self, formula) -> float:
        """
        Obtain the molar mass of an oxide

        Arguments:
            formula: some oxide formula (ex: Al2O3, MnO, etc.)
        Returns:
            formula_mass: molar mass of input formula

        Raises:
            Exception: Propagates any exception raised during molar mass calculation.
        """

        formula_mass = np.nan # Default value if formula not recognized

        if formula == 'FeOT':
            formula_mass = Formula('FeO').mass
        else:
            try:
                formula_mass = Formula(formula).mass
            except Exception as e:
                raise Exception(f'Error processing "{formula}": {e}')
        return formula_mass
        
    def add_molar_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Append columns with molar conversions to the dataframe.
        """

        # Add molar mass columns
        for formula in self.all_formulae:
            try:
                formula_mass = self._get_molar_mass(formula)
                molar_col_name = f'__{formula}_molar'
                dataframe[molar_col_name] = dataframe[formula] / formula_mass
            except KeyError:
                print(f'KeyError: Column "{formula}" not found in dataframe.')
            except Exception as e:
                print(f'Error processing formula "{formula}": {e}')

        return dataframe

    def rename_molar_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Rename columns to conform to future API
        """
        # Add molar mass columns
        for formula in self.all_formulae:
            molar_col_name = f'__{formula}_molar'
            dataframe[molar_col_name] = dataframe[formula]

        return dataframe

    def data_normalization(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data
        """

        # Calculate normalization values and normalize molar columns
        molar_columns = [f'__{formula}_molar' for formula in self.all_formulae]
        dataframe['__molar_normalization'] = dataframe[molar_columns].sum(axis=1)

        for col in molar_columns:
            normed_col_name = f'{col}_normed'
            dataframe[normed_col_name] = dataframe[col] / dataframe['__molar_normalization']

        # Combine values according to formula_list to get apex columns
        apex_positions = ["top", "left", "right"]
        for position, apex in zip(apex_positions, self.formula_list):
            normed_cols = [f'__{formula}_molar_normed' for formula in apex]
            dataframe[f'{position}_apex_molar_normed'] = dataframe[normed_cols].sum(axis=1)

        return dataframe

class Trace:
    def __init__(self,
                 formula_list: list,
                 apex_names: list):
        """
        Initialize the Trace object with a dataframe, a list of formulas, and apex names.

        Args:
            dataframe: The master datafile with oxide compositions.
            formula_list: List of elemental formulas for top, left, and right apices.
            apex_names: Names of the apices.
        """

        self.formula_list = formula_list
        self.apex_names = apex_names
        self.molar_mass_calculator = MolarMassCalculator(formula_list)

    def _trace_data(self,
                    dataframe: pd.DataFrame,
                    symbol: str,
                    size: float,
                    colormap: str,
                    hover_cols: list,
                    convert_wtp_to_molar: bool=True) -> pd.DataFrame:
        """
        Collect trace data into a dictionary.

        Returns:
            dict: A dictionary containing the data to include in the ternaries.
        """
        formula_list = self.formula_list
        apex_names = self.apex_names
    
        if convert_wtp_to_molar:
            dataframe = self.molar_mass_calculator.add_molar_columns(dataframe)
        else:
            dataframe = self.molar_mass_calculator.rename_molar_columns(dataframe)
        dataframe = self.molar_mass_calculator.data_normalization(dataframe)

        # Summing up the weight percent for each apex
        for apex in zip(self.formula_list, apex_names):
            dataframe[f"{apex[1]}-wt%"] = np.sum(dataframe[apex[0]], axis=1)

        trace_data = {
            apex_names[0]: dataframe["top_apex_molar_normed"],
            apex_names[1]: dataframe["left_apex_molar_normed"],
            apex_names[2]: dataframe["right_apex_molar_normed"],
            **{f"{apex}-wt%":    round(dataframe[f"{apex}-wt%"], 5) for apex in apex_names},
            **{f"{formula}-wt%": round(dataframe[f"{formula}"],  5) for apex in formula_list for formula in apex}
            }
        
        if colormap:
            trace_data.update({colormap: dataframe[colormap]})
        if size:
            if isinstance(size, str):
                trace_data.update({size: dataframe[size]})
            else:
                trace_data.update({"Size": size})
        if hover_cols:
            for datum in hover_cols:
                trace_data.update({datum: dataframe[datum]})

        trace_data = pd.DataFrame(trace_data)

        if colormap:
            # Reorder df so higher colormap values are plotted on top of lower ones.
            trace_data = trace_data.sort_values(by=colormap, ascending=True)
        if isinstance(size,str):
            # Reorder df so that larger points are plotted behind smaller points.
            trace_data = trace_data.sort_values(by=size, ascending=False)

        return trace_data

    def _hover_menu(self, data:pd.DataFrame, hover_cols:list) -> tuple:
        """
        Generate hover data and template for a Plotly trace.

        Args:
            data: Data to be used for the hover information.
            hover_cols: List of column names to include in hover information.

        Returns:
            hover_data, hover_template: The data to include in the hover menu along with its associated HTML formatting.
        """

        # Prepare hover columns
        wtp_hover = [f"{formula}-wt%" for apex in self.formula_list for formula in apex]
        hover_cols = wtp_hover + hover_cols if hover_cols else wtp_hover

        # Construct hover template
        hover_template = ""
        for i, header in enumerate(hover_cols):
            hover_template += f"<br><b>{header}:</b> %{{customdata[{i}]}}"

        hover_template += "<extra></extra>" # Disable default hover text (ex: "Trace 0")

        # Structure hover data
        hover_data = data[hover_cols].values

        return hover_data, hover_template

    def make_trace(self,
                   dataframe: pd.DataFrame,
                   name: str=None,
                   symbol: str=None,
                   size: float=None,
                   color: str=None,
                   colormap: str=None,
                   cmin:float=None,cmax:float=None,
                   hover_cols:list=None,
                   convert_wtp_to_molar:bool=True) -> go.Scatterternary:
        """
        Create a Plotly Scatterternary trace with the specified properties.

        Args:
            dataframe:
            symbol: Marker symbol.
            size: Marker size.
            colormap: Name of the column to use for color mapping.
            color: Static marker color.
            cmin: Minimum value for color scale.
            cmax: Maximum value for color scale.
            hover_cols: Columns to include in hover information.

        Returns:
            Scatterternary: A Plotly Scatterternary trace object.
        """
        dataframe = dataframe.copy()

        trace_data = self._trace_data(dataframe,
                                      symbol,
                                      size,
                                      colormap,
                                      hover_cols,
                                      convert_wtp_to_molar)

        # Define default marker properties
        marker_props = {
            "symbol": symbol,
            "line": dict(width=0.3, color='Black')
        }

        # Apply dynamic sizing based on a DataFrame column
        if isinstance(size, str) and size in trace_data.columns:
            marker_props["size"] = trace_data[size]
        elif isinstance(size, (int, float)):
            marker_props["size"] = size
            
        if color:
            marker_props["color"] = color
        # Update marker properties for color mapping
        elif colormap:
            marker_props.update({
                "color": trace_data[colormap],
                "colorscale": 'matter',
                "cmin": cmin, 
                "cmax": cmax,
                "line": dict(color='rgba(0, 0, 0, 0)'),
                "showscale": True,
                "colorbar": dict(
                    title=f"{colormap}-wt%",
                    titleside='top'
                )
            })

        hover_data, hover_template = self._hover_menu(trace_data, hover_cols)

        trace = go.Scatterternary(
            a=trace_data[self.apex_names[0]],
            b=trace_data[self.apex_names[1]],
            c=trace_data[self.apex_names[2]],
            name=name,
            mode='markers',
            marker=marker_props,
            customdata=hover_data,
            hovertemplate=hover_template
            )
        
        return trace
    
class TernaryGraph:
    def __init__(self, title: str, apex_names: list, enable_darkmode: bool = False):
        """
        Initialize a TernaryGraph object.

        Args:
            title: A title for the plot.
            apex_names: A list of the apex names.
            enable_darkmode: Boolean to enable or disable dark mode for the plot.
        """
        self.title = title
        self.apex_names = apex_names
        self.enable_darkmode = enable_darkmode
        self.fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'ternary'}]])

    def add_trace(self, trace: go.Scatterternary):
        """
        Add a trace to the ternary plot.

        Args:
            trace: Plotly GO Scatterternary trace object.
        """
        self.fig.add_trace(trace)

    def format_chemical_formula(self, formula):
        """
        Format chemical formula with subscripts.

        Args:
            formula (str): The chemical formula.

        Returns:
            str: Formatted formula with HTML-like subscripts.
        """
        formatted_formula = ''
        for char in formula:
            if char.isdigit():
                formatted_formula += f'<sub>{char}</sub>'
            else:
                formatted_formula += char
        return formatted_formula

    def _configure_layout(self):
        """
        Configure the layout of the ternary plot.
        """
        line_style = dict(linecolor='grey', min=0.01, linewidth=2, ticks='outside')
        
        if self.enable_darkmode:
            line_style.update(tickcolor='white', linecolor='white')

        formatted_apex_names = [self.format_chemical_formula(name) for name in self.apex_names]

        self.fig.update_layout(
            ternary={
                'sum': 1,
                'aaxis': dict(title=formatted_apex_names[0], **line_style),
                'baxis': dict(title=formatted_apex_names[1], **line_style),
                'caxis': dict(title=formatted_apex_names[2], **line_style),
                # 'bgcolor':'rgba(0, 0, 0, 0)',
            },
            title=dict(
                text=self.title,
                x=0.5,
                y=0.95,
                xanchor='center',
                yanchor='top'
            ),
            legend_orientation='h',
            plot_bgcolor  = 'rgba(0, 0, 0, 0)',
            paper_bgcolor = 'rgba(0, 0, 0, 0)',
            font=dict(color='white' if self.enable_darkmode else 'black'),
            # Adjust figure padding so it fits in the render window
            margin=dict(l=100, r=100, t=100, b=100),
            # Colorbar adjustments
            coloraxis_colorbar=dict(
                x=1.05,  # Positioning colorbar to the right of the plot
                xpad=20  # Adding padding between plot and colorbar
            )
        )

        # Adjust figure padding so it fits in the render window
        self.fig.update_layout(
            margin=dict(l=100, r=100, t=100, b=100)
        )

    def show(self):
        """
        Show the configured ternary plot.
        """
        self._configure_layout()
        self.fig.show()

    def to_html(self):
        """
        Convert the ternary plot to HTML.

        Returns:
            str: HTML representation of the ternary plot.
        """
        self._configure_layout()
        return self.fig.to_html(include_plotlyjs=True)

def parse_ternary_type(t_type: str, 
                       custom_t_type: list[str]=None,
                       custom_apex_names: list[str]=None) -> tuple(list[str]):
    """
    Parse the apice oxides to use in the final ternary.
    
    Arguments:
        t_type: Ternary type. Either a default type (ie "Al2O3 CaO+NaO+K2O FeOT+MgO", 
                "SiO2+Al2O3 CaO+NaO+K2O FeOT+MgO", or "Al2O3 CaO+Na2O K2O") or "Custom"
        custom_t_type: Custom ternary apex values. 
                       Example: [["SiO2"], ["Al2O3"], ["CaO","MgO"]]
        custom_apex_names: 
    Returns:
        (tops, lefts, rights): A tuple containing the oxides to plot on the top, left, and right
                               apices, respectively.

    """

    if t_type == 'Custom':
        formula_list = custom_t_type
        formula_list = ["+".join(apex) for apex in formula_list]
    else:
        formula_list = t_type.split(' ')

    apex_names = custom_apex_names

    for i in range(3):
        if not apex_names[i]:
            apex_names[i] = formula_list[i]

    formula_list = [apex.split("+") for apex in formula_list]

    return formula_list, apex_names

def create_title(formula_list: list[list[str]], title: str=None)->str:
    """
    Create a string title to use in the ternary figure. If none is given, a default title will be 
    generated.

    Args:
        formula_list: The formula list used when creating the ternary. 
        title: A custom title to use in the ternary
    Returns:
        title: A string title to use in the ternary figure
    """

    def apex_abbr(formula_list:list[list[str]]) -> str:
        """
        Abbreviate the names of the apices.

        Ex: ["Al2O3", ["CaO","Na2O","K2O"], ["FeOT","MgO"]] -> "A CNK FM"

        Args:
            formula_list: The formula list used when creating the ternary. 
        Returns:
            t_type_abbr: The abbreviated ternary type
        """
        t_type_abbr = [[ox[0] if ox!="MnO" else "Mn" for ox in apex] for apex in formula_list]
        t_type_abbr = " ".join(["".join(apex) for apex in t_type_abbr])
        return t_type_abbr
    
    if not title:
        title = apex_abbr(formula_list) + " Ternary Diagram"

    return title
