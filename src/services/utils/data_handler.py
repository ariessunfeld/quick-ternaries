from pathlib import Path
import pandas as pd
from pandas import DataFrame

class DataHandler:

    def __init__(self):
        self._df = None

    def apply_filter(self, df: DataFrame, filter_strategy) -> DataFrame:
        pass

    def load_data(self, filepath: str|Path, sheet: str, header: int):
        pass
        # read in the file accordingly, handling csv and xlsx separately



