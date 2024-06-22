"""Ternary HTML file maker"""

from src.models.ternary.model import TernaryModel
from src.services.ternary.plot_maker import TernaryPlotMaker

class TernaryHtmlMaker:
    
    def __init__(self):
        self.plot_maker = TernaryPlotMaker()

    def make_html(self, model: TernaryModel):
        plot = self.plot_maker.make_plot(model)
        html = plot.to_html()
        return html