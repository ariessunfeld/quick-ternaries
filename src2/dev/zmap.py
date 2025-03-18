import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import plotly.graph_objects as go

# Read the CSV file.
# Update the filename to match your CSV.
df = pd.read_csv('../demo-data/_ccam_data.csv')

# Define the list of element columns.
# (Assumes all columns except 'Facies' are the elements of interest;
#  if there are duplicate columns (e.g., two "SiO2") adjust accordingly.)
elements = [col for col in df.columns if col != 'Facies']
elements = ['SiO2', 'TiO2', 'Al2O3', 'FeOT', 'MgO', 'CaO', 'Na2O', 'K2O', 'MnO']

# Group the data by Facies.
facies_groups = df.groupby('Facies')

# Initialize dictionaries to store correlation and p-value DataFrames for each facies.
correlations = {}
pvals = {}

# Loop over each facies group and compute the pairwise Spearman correlation and p-value.
for facies, group in facies_groups:
    # Drop any rows with missing values for the element columns.
    data = group[elements].dropna()
    # Compute the Spearman correlation matrix and the corresponding p-value matrix.
    corr_matrix, p_matrix = spearmanr(data)
    # Convert the results into DataFrames with the element names as both index and columns.
    corr_df = pd.DataFrame(corr_matrix, index=elements, columns=elements)
    pval_df = pd.DataFrame(p_matrix, index=elements, columns=elements)
    correlations[facies] = corr_df
    pvals[facies] = pval_df

# Get a sorted list of unique facies (used as the x-axis in the heatmaps).
facies_list = sorted(df['Facies'].unique())

# For each element (target), create a heatmap comparing it to the other elements.
for target in elements:
    # Define the list of other elements (all except the target element).
    other_elements = [e for e in elements if e != target]
    
    # Build the z-matrix for the heatmap:
    # rows correspond to each "other" element and columns to each facies group.
    # If the p-value is above 0.05, set that cell to None (so that it appears white).
    z_matrix = []
    for other in other_elements:
        row = []
        for facies in facies_list:
            r = correlations[facies].loc[target, other]
            p = pvals[facies].loc[target, other]
            # Only show the correlation if the p-value is 0.05 or below.
            row.append(r if p <= 0.05 else None)
        z_matrix.append(row)
    
    # Create the heatmap using Plotly.
    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=facies_list,
        y=other_elements,
        colorscale='RdBu',  # Using a cool-warm (diverging) colorscale.
        zmin=-1,
        zmax=1,
        showscale=True,
        hoverongaps=False  # Disables hover info for missing cells.
    ))
    
    # Update the layout so that:
    # - The aspect ratio is 1:1 to force cells to be square.
    # - Gridlines are removed.
    # - Backgrounds are white so that cells with None appear white.
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False)
    fig.update_xaxes(showgrid=False)
    fig.update_layout(
        title=f"Spearman's R: {target} vs Other Elements",
        xaxis_title="Facies",
        yaxis_title="Element",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    # Display the heatmap.
    fig.show()
