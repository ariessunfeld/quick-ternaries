from src.models.ternary.setup.model import TernaryStartSetupModel
from src.models.ternary.trace.tab_model import TabModel
from src.models.ternary.plot.model import TernaryRenderPlotModel

class TernaryModel:
    """Container class for ternary models"""
    
    def __init__(self):
        self.start_setup_model = TernaryStartSetupModel()
        self.tab_model = TabModel()
        self.plot_model = TernaryRenderPlotModel()

