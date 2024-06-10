"""Contains the widgets for the Depth Profiles plot Start Setup view

- Single singleshots file (from among loaded data, this can be a combobox)
- Target (auto-filling line-edit)
- Title
- X Axis label (default: shot number)
- Y Axis label (default: MOC wt%)
- X Axis start (default: 1)
- Checkbox for masking X axis up to shot __
  - if checked, options for mask color and opacity with grey, medium transparent defaults
- Checkbox for adding mean composition horizontal line
  - if checked, asks which element to use (from among those chosen in the added Traces)

Note: Traces will represent different elements/oxides
Note: Arrows below the Web Engine will allow users to switch between different points, since shot number is on x axis 
Note: along with arrows < and >, we will have Save and Save All buttons. These can be over where the usual Save button is
"""