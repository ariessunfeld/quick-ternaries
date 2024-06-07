"""Contains the widgets for the Cartesian plot Start Setup view

- X axis column(s)
- Y axis columns(s)
  (these should be implemented with add/remove lists, like the custom apices for Ternary start setup)

- Title
- X axis label
- Y axis label

- Heatmap option
  (this should contain the column-selection option for the heatmap, like in Ternary start setup)

- Custom hover data option
  (same as Ternary start setup)

Note that this file does NOT include the Loaded Data view or the Add Data button,
because those should be part of the Control Panel on ANY start setup view, regardless of Plot Mode

Further note that default Cartesian plot types are not included here
"""

from PySide6.QtWidgets import (
    QWidget,
)


class CartesianStartSetupView(QWidget):
    pass

