"""This module contains functions to help with ternary diagram generation"""

import pandas as pd
import numpy as np

from molmass import Formula
from molmass.molmass import FormulaError

import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Config():
    """"
    Configure data and create a scatter ternary.
    """

    # Initialization and related methods
    def __init__(self,
                 dataframe: pd.DataFrame,
                 colormap: str = None,
                 cmin: float = None,
                 cmax: float = None,
                 symbol:   str = None,
                 size:     str = None):
        """
        Initialize the Config object with the provided arguments.

        Arguments:
            file: A Pandas Dataframe containing all of the data to plot.
            colormap: The name of the column to use for a colormap.
            symbol: The name of the column to use for point symbols.
            size: The name of the column to use for point sizes.
        """

        # This has all the major oxides, but if you ever need to plot
        # something else, just add the element to the mass dict.
        major_oxides = ["Al2O3", "MnO", "MgO", "SiO2", "CaO", "Na2O", "K2O", "TiO2", "FeOT"]
        # 'FeOT' is handled separately because the `Formula` function
        # doesn't recognize 'FeOT' and instead calls it 'FeO'
        mass_dict = {}
        for oxide in [x for x in major_oxides if x != "FeOT"]:
            mass_dict[oxide] = Formula(oxide).mass
        if "FeOT" in major_oxides:
            mass_dict["FeOT"] = Formula("FeO").mass

        if size:
            if size.replace(".","").isnumeric():
                size = float(size)

        self.major_oxides = major_oxides
        self.mass_dict    = mass_dict
        self.dataframe    = dataframe
        self.colormap     = colormap
        self.cmin         = cmin
        self.cmax         = cmax
        self.symbol       = symbol
        self.size         = size

    # Data processing and calculation methods
    def _wtp_to_molar(
            self,
            file: str,
            formulas_list: list,
            masses_dict: dict,
            comp_data: pd.DataFrame
            ) -> dict:
        """
        Returns a dict with mole percents for each apex's chemical 
        formula for specific data for an observation point.

        Arguments:
            file: The target filename
            formulas_list: A list of lists, each with the constituent chemicals in a formula.
                ex: formulas_list = [[Al2O3], ['CaO','Na2O','K2O']] 
                    represents the two formulas: "Al2O3" and "CaO+Na2O+K2O"
            masses_dict: A dict with grams/mol values for various oxides.
            comp_data: A df with composition data and headers that 
                       superset the oxides in formulas_list.
        Returns:
            formula_mole_percent: A dict with mole percents for each apex's chemical 
                                  formula for specific data for an observation point.
        """

        # Get the corresponding row from the comp_data sheet
        df_temp = comp_data[comp_data["File"].eq(file)]

        # Go through the list of formulas passed into the
        # function and get the percentage normalization
        percentage_normalization = sum(float(list(df_temp[element])[0])
                                       for formula in formulas_list
                                       for element in formula)

        # Normalize these percentages and put normalized vals into dict with elements as keys
        element_percents = {
            element: 100 * float(list(df_temp[element])[0]) / percentage_normalization
            for formula in formulas_list 
            for element in formula
        }

        # Get the amt. moles for each of these elements based on the percentage, assuming wt = 1kg
        # This uses the formula mols = wt / mlr wt
        element_moles = {
            element: normed_wt_percent / masses_dict[element]
            for element, normed_wt_percent in element_percents.items()
        }

        # Get the total molar amt for normalization
        molar_normalization = sum(element_moles.values())

        # Calculate the molar percents for each element to 3 sig. figs.
        element_mole_percent = {
            element: round(100 * molar_value / molar_normalization,3)
            for element, molar_value in element_moles.items()
        }

        # Add together the constituent components of each
        # formula to get the percentages for each apex
        formula_mole_percent = {
            tuple(formula): sum(element_mole_percent[element] for element in formula) 
            for formula in formulas_list
        }

        return formula_mole_percent

    def _ternary_data(
            self,
            formula_list: list,
            apices: list,
            hover_data: list
            ) -> list:
        """
        Collect data to be plotted on the ternary diagram.

        Arguments:
            formula_list: A list of the apex formulas.
            apices: A list of the apex names.
            hover_data: A list of column headers from your input data file to include
                        in the figures hover data (only accessible through html files).
        
        Returns:
            data_list: A Pandas Dataframe containing the data to include in the ternaries.
        """

        dataframe = self.dataframe
        mass_dict = self.mass_dict
        colormap  = self.colormap
        symbol    = self.symbol
        size      = self.size

        for apex in zip(formula_list,apices):
            # The total weight percent for each apex
            dataframe[f"{apex[1]}-wt%"] = np.sum(dataframe[apex[0]], axis=1)

        data_list = []
        for _, row in dataframe.iterrows():

            mole_percents = self._wtp_to_molar(row["File"], formula_list, mass_dict, dataframe)
            mole_percents = list(mole_percents.values())
            # mole_percents = list(map(lambda x: round(x,5), mole_percents))

            data = {
                "File": row["File"],
                "Target": row["Target"],
                "Target:obs": f"{row['Target']}:{row['Observation Point']}",
                apices[0]: mole_percents[0],
                apices[1]: mole_percents[1],
                apices[2]: mole_percents[2],
                "Norm factor": 100,
                **{f"{apex}-wt%": round(row[f"{apex}-wt%"], 5) for apex in apices},
                **{f"{oxide}-wt%": round(row[f"{oxide}"], 5) for apex in formula_list for oxide in apex}
            }

            if colormap:
                data.update({colormap: row[colormap]})
            if symbol:
                data.update({symbol: row[symbol]})
            if size:
                if isinstance(size,str):
                    data.update({size: row[size]})
                else:
                    data.update({"Size": size})
            if hover_data:
                for datum in hover_data:
                    data.update({datum: row[datum]})
            data_list.append(data)

        dataframe = pd.DataFrame(data_list)

        if colormap:
            # Reorder df so higher colormap values are plotted on top of lower ones.
            dataframe = dataframe.sort_values(by=colormap, ascending=True)
        if isinstance(size,str):
            # Reorder df so that larger points are plotted behind smaller points.
            dataframe = dataframe.sort_values(by=size, ascending=False)

        return dataframe

    # Plotting methods
    def graph_ternary(
            self,
            title: str,
            formula_list: list,
            apices: list,
            hover_data: list = None
            ) -> go.Scatterternary:
        """
        Create a ternary diagram using Plotly Express.

        Arguments:
            title: A title for the plot
            formula_list: A list of the apex formulas.
            apices: A list of the apex names.
            hover_data: A list of column headers from your input data file to 
                        include in the figures hover data (only accessible through html files).

        Returns:
            fig: A Plotly Express ternary scatter plot.
        """
        colormap = self.colormap
        cmin     = self.cmin
        cmax     = self.cmax
        symbol   = self.symbol
        size     = self.size

        data = self._ternary_data(formula_list, apices, hover_data)

        wtp_hover = []
        for apex in formula_list:
            for oxide in apex:
                wtp_hover.append(f"{oxide}-wt%")
        hover_data = wtp_hover + hover_data if hover_data else wtp_hover

        # Create a subplot for ternary plot
        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'ternary'}]])
        
        # Prepare the custom data for hover in a way compatible with go.Scatterternary
        custom_data = data[hover_data] if hover_data else None

        # Initialize the hover data with <Target>:<Obs point>, bolded and with a larger font size
        hover_template = "<span style='font-size: 14px;'><b>%{text}</b></span><br>"

        # Add the rest of the hover data
        for i, header in enumerate(hover_data):
            hover_template += f"<br><b>{header}:</b> %{{customdata[{i}]}}"

        hover_template += "<extra></extra>" # Disable the text that says "Trace 0"

        # Define default marker properties
        marker_props = dict(
            symbol=symbol,
            size=size,
            line=dict(width=0.3, color='Black')
        )

        # If colormap is provided, update marker properties with colormap info
        if colormap:
            marker_props.update(
                color=data[colormap],
                colorscale='matter',
                cmin=cmin, cmax=cmax,
                line=dict(color='rgba(0, 0, 0, 0)'),
                showscale=True,
                colorbar=dict(
                    title=colormap+"-wt%",
                    titleside='top'
                )
            )

        trace = go.Scatterternary(
            a=data[apices[0]],
            b=data[apices[1]],
            c=data[apices[2]],
            mode='markers',
            text=data["Target:obs"],  # for hover info
            marker=marker_props,
            customdata=custom_data.values,
            hovertemplate=hover_template
        )

        fig.add_trace(trace)

        # Configure the layout of the ternary plot
        fig.update_layout(
            ternary={
                'sum': 1,
                # Min creates a buffer to prevent problems plotting points on the border of the ternary
                'aaxis': {'title': apices[0], 'min': 0.01, 'linewidth': 2, 'ticks': 'outside'},
                'baxis': {'title': apices[1], 'min': 0.01, 'linewidth': 2, 'ticks': 'outside'},
                'caxis': {'title': apices[2], 'min': 0.01, 'linewidth': 2, 'ticks': 'outside'},
            },
            title=dict(
                text=title,
                x=0.5,  # Center alignment of title
                y=0.95,  # Position the title a little higher to avoid overlap with the plot
                xanchor='center',
                yanchor='top'
            ),
            legend_orientation='h'
        )

        return fig


def parse_ternary_type(t_type: str, 
                       custom_t_type: list[str]=None,
                       use_custom_apex_names: bool=False,
                       custom_apex_names: list[str]=None) -> tuple(list[str]):
    """
    Parse the apice oxides to use in the final ternary.
    
    Arguments:
        t_type: Ternary type. Either a default type (ie "Al2O3 CaO+NaO+K2O FeOT+MgO", 
                "SiO2+Al2O3 CaO+NaO+K2O FeOT+MgO", or "Al2O3 CaO+Na2O K2O") or "Custom"
        custom_t_type: Custom ternary apex values. 
                       Example: [["SiO2"], ["Al2O3"], ["CaO","MgO"]]
        use_custom_apex_names: Bool to use custom apex names
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

    if use_custom_apex_names:
        apex_names = custom_apex_names
    else:
        apex_names = formula_list
    
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
