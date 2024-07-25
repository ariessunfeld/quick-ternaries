"""Contains Model representing global application state"""

from src.models.utils import DataLibrary

from src.models.ternary import TernaryModel
# from src.models.cartesian import CartesianModel
# from src.models.corrplot import CorrplotModel
# from src.models.depth_profiles import DepthProfileModel
# from src.models.zmaps import ZmapModel
# from src.models.roseplot import RoseplotModel

from src.models.utils import TabsPanelModel
# import more plot mode models here

class AppModel:
    def __init__(self):

        self.data_library = DataLibrary()
        self.tab_model = TabsPanelModel()

        self.ternary_model = TernaryModel()
        self.cartesian_model = None  # TODO
        self.depth_profile_model = None  # TODO
        self.zmap_model = None  # TODO

        self.current_model = self.ternary_model
        self.current_model_name = 'ternary'

        self.setup_references()

    def setup_references(self):
        self.ternary_model.set_data_library(self.data_library)
        self.ternary_model.set_tab_model(self.tab_model)
        # TODO add similar lines for other plot types

    def switch_current_model(self, model: str):
        """Switches the `current_model` pointer to `model`"""
        str_fmt = f"{model.lower().replace(' ', '_')}_model"
        self.current_model = getattr(self, str_fmt)
        self.current_model_name = str_fmt.rstrip('_model')
        if self.current_model is None:
            raise ValueError(
                f"Cannot switch to model: {model} (formatted: {str_fmt})")
