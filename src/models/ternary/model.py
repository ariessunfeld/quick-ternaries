from src.models.ternary.setup.model import TernaryStartSetupModel
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.models.ternary.plot.model import TernaryRenderPlotModel
from src.models.ternary.trace.molar_conversion_model import TernaryTraceMolarConversionModel

class TernaryModel:
    """Container class for ternary models"""
    
    def __init__(self):
        self.start_setup_model = TernaryStartSetupModel()
        self.tab_model = TraceTabsPanelModel()
        self.plot_model = TernaryRenderPlotModel()
        self.molar_conversion_model = TernaryTraceMolarConversionModel()
