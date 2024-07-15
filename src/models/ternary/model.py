from src.models.ternary.setup import TernaryStartSetupModel
from src.models.ternary.trace import TraceTabsPanelModel, TernaryTraceMolarConversionModel
from src.models.ternary.plot import TernaryRenderPlotModel

class TernaryModel:
    """Container class for ternary models"""
    
    def __init__(self):
        self.start_setup_model = TernaryStartSetupModel()
        self.tab_model = TraceTabsPanelModel()
        self.plot_model = TernaryRenderPlotModel()
        self.molar_conversion_model = TernaryTraceMolarConversionModel()
