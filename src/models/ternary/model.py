from src.models.ternary.setup import TernaryStartSetupModel
from src.models.ternary.trace import MolarConversionModel
from src.models.utils import TraceTabsPanelModel
from src.models.ternary.plot import TernaryRenderPlotModel

from src.models.utils import DataLibrary

class TernaryModel:
    """Container class for ternary plotting"""
    
    def __init__(self):
        self.start_setup_model = TernaryStartSetupModel()
        self.molar_conversion_model = MolarConversionModel()

        self.data_library = None
        self.tab_model = None

    def set_data_library(self, data_library: DataLibrary):
        self.data_library = data_library

    def set_tab_model(self, tab_model: TraceTabsPanelModel):
        self.tab_model = tab_model
