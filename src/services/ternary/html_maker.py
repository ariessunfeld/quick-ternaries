"""Ternary HTML file maker"""

from src.models.ternary.model import TernaryModel
from src.services.ternary.plot_maker import TernaryPlotMaker
from src.services.ternary.trace_maker import TraceMolarConversionException

from PySide6.QtWidgets import QMessageBox

class TernaryHtmlMaker:
    
    def __init__(self):
        self.plot_maker = TernaryPlotMaker()

    def make_html(self, model: TernaryModel):
        try:
            plot = self.plot_maker.make_plot(model)
            html = plot.to_html()
            return html
        except TraceMolarConversionException as err:
            msg = f"An error occurred while trying to parse the chemical formula for the column '{err.column}' "
            msg += f"in Trace {err.trace_id}.\n\nThe custom chemical formula provided was '{err.bad_formula}'.\n\n"
            msg += f"Please enter a valid formula that can be parsed to compute molar mass, or un-check the "
            msg += f"'convert from wt% to molar' option."
            QMessageBox.critical(None, 'Error parsing formula', msg)
