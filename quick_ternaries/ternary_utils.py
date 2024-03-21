"""This module contains functions to help with ternary diagram generation"""

import pandas as pd
import numpy as np

from molmass import Formula
from molmass.molmass import FormulaError

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from PySide6.QtWidgets import QInputDialog

class MolarMassCalculator:
    def __init__(self, formula_list: list, conversion_mapping: dict):
        self.formula_list = formula_list
        self.conversion_mapping = conversion_mapping
        # Flatten the list of formulas for easier processing
        self.all_formulae = [formula for apex in formula_list for formula in apex]

    # def _get_molar_mass(self, formula) -> float:
    #     """
    #     Obtain the molar mass of an oxide

    #     Arguments:
    #         formula: some oxide formula (ex: Al2O3, MnO, etc.)
    #     Returns:
    #         formula_mass: molar mass of input formula

    #     Raises:
    #         Exception: Propagates any exception raised during molar mass calculation.
    #     """

    #     formula_mass = np.nan # Default value if formula not recognized

    #     if formula == 'FeOT':
    #         formula_mass = Formula('FeO').mass
    #     else:
    #         try:
    #             formula_mass = Formula(formula).mass
    #         except FormulaError as e:
    #             print(f'Error processing "{formula}": {e}')
    #     return formula_mass
    
    def _get_molar_mass(self, initial_formula):
        """
        Attempts to parse a chemical formula. If parsing fails, prompts the user
        to input a correct formula via a GUI dialog.

        Parameters:
        - initial_formula: Initial formula string to parse.

        Returns:
        - A valid Formula object, or None if the user cancels the input dialog.
        """
        try:
            # FeOT special case (use molar mass of FeO)
            if initial_formula == 'FeOT':
                return Formula('FeO').mass
            # User override special case
            if initial_formula in self.conversion_mapping:
                return Formula(self.conversion_mapping[initial_formula]).mass
            # Generic case
            return Formula(initial_formula).mass
        except FormulaError:
            # Show input dialog to ask user for a correct formula
            corrected_formula, ok = QInputDialog.getText(None, "Correct the Formula",
                                                        "Could not parse the formula. Please enter a valid formula:",
                                                        text=initial_formula)
            if ok and corrected_formula:
                self.conversion_mapping[initial_formula] = corrected_formula
                return self._get_molar_mass(corrected_formula)  # Recursively validate the new input
            else:
                return None
        
    def add_molar_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Append columns with molar conversions to the dataframe.
        """

        # Add molar mass columns
        for formula in self.all_formulae:
            formula_mass = self._get_molar_mass(formula)
            try:
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
                 apex_names: list,
                 conversion_mapping: dict):
        """
        Initialize the Trace object with a list of formulas, a list of apex names, and a mapping for conversions

        Args:
            formula_list: List of elemental formulas for top, left, and right apices.
            apex_names: Names of the apices.
            conversion_mapping: Dict mapping column names to molar-convertible formulae
        """

        self.formula_list = formula_list
        self.apex_names = apex_names
        self.conversion_mapping = conversion_mapping
        self.molar_mass_calculator = MolarMassCalculator(formula_list, conversion_mapping)

    def _trace_data(self,
                    dataframe: pd.DataFrame,
                    size: float,
                    hover_cols: list,
                    convert_wtp_to_molar: bool=True) -> pd.DataFrame:
        """
        Collect trace data into a dictionary.

        Returns:
            dict: A dictionary containing the data to include in the ternaries.
        """
        formula_list = self.formula_list
        apex_names = self.apex_names
    
        for apex in formula_list:
            for formula in apex: 
                if formula not in list(dataframe.columns):
                    raise KeyError(f"{formula} not found in data columns. Please check data or change Ternary Type.")
        # if any(formula not in list(dataframe.columns) for formula in formula_list):
        #     raise KeyError("")
        data_preprocess = self.molar_mass_calculator
        if convert_wtp_to_molar:
            dataframe = data_preprocess.add_molar_columns(dataframe)
        else:
            dataframe = data_preprocess.rename_molar_columns(dataframe)
        dataframe = data_preprocess.data_normalization(dataframe)

        # Summing up the weight percent for each apex
        for apex in zip(self.formula_list, apex_names):
            dataframe[f"{apex[1]}-wt%"] = np.sum(dataframe[apex[0]], axis=1)

        trace_data = {
            apex_names[0]: dataframe["top_apex_molar_normed"],
            apex_names[1]: dataframe["left_apex_molar_normed"],
            apex_names[2]: dataframe["right_apex_molar_normed"],
            **{f"{apex}-wt%":    round(dataframe[f"{apex}-wt%"], 5) for apex in apex_names},
            **{f"{formula}-wt%": round(dataframe[f"{formula}"],  5) for apex in formula_list for formula in apex},
            'color': dataframe['color']
            }

        if size:
            if isinstance(size, str):
                trace_data.update({size: dataframe[size]})
            else:
                trace_data.update({"size": size})
        if hover_cols:
            for datum in hover_cols:
                trace_data.update({datum: dataframe[datum]})

        trace_data = pd.DataFrame(trace_data)

        if dataframe['color'].dtype.kind in 'biufc': # If the color column is numeric
            # Reorder df so higher colormap values are plotted on top of lower ones.
            trace_data = trace_data.sort_values(by='color', ascending=True)
        if isinstance(size,str):
            # Reorder df so that larger points are plotted behind smaller points.
            trace_data = trace_data.sort_values(by="size", ascending=False)

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
                   cmin:float=None,cmax:float=None,
                   hover_cols:list=None,
                   convert_wtp_to_molar:bool=True) -> go.Scatterternary:
        """
        Create a Plotly Scatterternary trace with the specified properties.

        Args:
            dataframe:
            symbol: Marker symbol.
            size: Marker size.
            cmin: Minimum value for color scale.
            cmax: Maximum value for color scale.
            hover_cols: Columns to include in hover information.

        Returns:
            Scatterternary: A Plotly Scatterternary trace object.
        """
        dataframe = dataframe.copy()

        trace_data = self._trace_data(dataframe,
                                      size,
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
            
        marker_props['color'] = trace_data['color']

        # Update marker properties for color mapping
        if dataframe['color'].dtype.kind in 'biufc':
            marker_props.update({
                "colorscale": 'matter',
                "cmin": cmin, 
                "cmax": cmax,
                "line": dict(color='rgba(0, 0, 0, 0)'),
                "showscale": True,
                "colorbar": dict(
                    # title=f"{colormap}-wt%",
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

    def _configure_layout(self):
        """
        Configure the layout of the ternary plot.
        """
        line_style = dict(linecolor='grey', linewidth=1, ticks='outside')
        
        if self.enable_darkmode:
            line_style.update(tickcolor='white', linecolor='white')

        self.fig.update_layout(
            ternary={
                'sum': 1,
                'aaxis': dict(title=self.apex_names[0], **line_style),
                'baxis': dict(title=self.apex_names[1], **line_style),
                'caxis': dict(title=self.apex_names[2], **line_style),
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
            # plot_bgcolor  = 'rgba(0, 0, 0, 0)',
            # paper_bgcolor = 'rgba(0, 0, 0, 0)',
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

def get_apex_names(t_type: list[str],
                   apex_names: list[str]=None) -> list[str]:
    """
    Parse the apice oxides to use in the final ternary.
    
    Arguments:
        t_type: Ternary type. Example: [["SiO2"], ["Al2O3"], ["CaO","MgO"]]
        apex_names: 
    Returns:
        apex_names: The names of the apices to plot

    """

    for i in range(3):
        if not apex_names[i]:
            apex_names[i] = "+".join(t_type[i])

    return apex_names

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
