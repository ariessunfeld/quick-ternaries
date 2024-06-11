"""Contains Model representing global application state"""

from src.models.ternary.model import TernaryModel
# import more plot mode models here

class AppModel:
    def __init__(self):
        self.ternary_model = TernaryModel()
        # more plot mode models here
