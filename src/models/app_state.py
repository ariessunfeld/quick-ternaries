"""Contains Model representing global application state"""

from src.models.ternary.model import TernaryModel
# import more plot mode models here

class AppModel:
    def __init__(self):
        self.ternary_model = TernaryModel()
        self.cartesian_model = None  # TODO
        self.depth_profile_model = None  # TODO
        self.zmap_model = None  # TODO

        self.current_model = self.ternary_model

    def switch_current_model(self, model: str):
        """Switches the `current_model` pointer to `model`"""
        self.current_model = getattr(self, f"{model.lower().replace(' ', '_')}_model")
        if self.current_model is None:
            raise ValueError(
                f"Cannot switch to model: {model} (formatted: {model.lower().replace(' ', '_')})")
