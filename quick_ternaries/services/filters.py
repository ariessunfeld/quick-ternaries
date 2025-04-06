"""This module contains the strategy classes for implementing each Filter operation"""

from typing import Dict
from abc import ABC, abstractmethod

import pandas as pd

class FilterStrategy(ABC):

    @abstractmethod
    def filter(self, data: pd.DataFrame, params: Dict):
        pass


class EqualsFilterStrategy(FilterStrategy):
    """X == value"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[data[params['column']] == params['value 1']].copy()


class OneOfFilterStrategy(FilterStrategy):
    """X is in [*values]"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[data[params['column']].isin(params['selected values'])].copy()


class ExcludeOneFilterStrategy(FilterStrategy):
    """X != value"""
    
    def filter(self, data: pd.DataFrame, params: Dict):
        return data[data[params['column']] != params['value 1']].copy()


class ExcludeMultipleFilterStrategy(FilterStrategy):
    """X is not in [*values]"""
    
    def filter(self, data: pd.DataFrame, params: Dict):
        return data[~data[params['column']].isin(params['selected values'])].copy()


class GreaterThanFilterStrategy(FilterStrategy):
    """X > value"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[data[params['column']] > float(params['value 1'])].copy()


class LessThanFilterStrategy(FilterStrategy):
    """X < value"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[data[params['column']] < float(params['value 1'])].copy()


class GreaterEqualFilterStrategy(FilterStrategy):
    """X >= value"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[data[params['column']] >= float(params['value 1'])].copy()


class LessEqualFilterStrategy(FilterStrategy):
    """X <= value"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[data[params['column']] <= float(params['value 1'])].copy()


class LTLTFilterStrategy(FilterStrategy):
    """value1 < X < value2"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[
            (data[params['column']] > params['value a']) &\
            (data[params['column']] < params['value b'])].copy()


class LELEFilterStrategy(FilterStrategy):
    """value1 <= X <= value2"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[
            (data[params['column']] >= params['value a']) &\
            (data[params['column']] <= params['value b'])].copy()


class LELTFilterStrategy(FilterStrategy):
    """value1 <= X < value2"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[
            (data[params['column']] >= params['value a']) &\
            (data[params['column']] <  params['value b'])].copy()


class LTLEFilterStrategy(FilterStrategy):
    """value1 < X <= value2"""

    def filter(self, data: pd.DataFrame, params: Dict):
        return data[
            (data[params['column']] >  params['value a']) &\
            (data[params['column']] <= params['value b'])].copy()
