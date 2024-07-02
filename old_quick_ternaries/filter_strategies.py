from abc import ABC, abstractmethod

class FilterStrategy(ABC):

    @abstractmethod
    def filter(self, data, params):
        pass

class EqualsFilterStrategy(FilterStrategy):
    """X == value"""

    def filter(self, data, params):
        return data[data[params['column']] == params['value 1']].copy()


class OneOfFilterStrategy(FilterStrategy):
    """X is in [*values]"""

    def filter(self, data, params):
        return data[data[params['column']].isin(params['selected values'])].copy()

class GreaterThanFilterStrategy(FilterStrategy):
    """X > value"""

    def filter(self, data, params):
        return data[data[params['column']] > float(params['value 1'])].copy()


class LessThanFilterStrategy(FilterStrategy):
    """X < value"""

    def filter(self, data, params):
        return data[data[params['column']] < float(params['value 1'])].copy()


class GreaterEqualFilterStrategy(FilterStrategy):
    """X >= value"""

    def filter(self, data, params):
        return data[data[params['column']] >= float(params['value 1'])].copy()


class LessEqualFilterStrategy(FilterStrategy):
    """X <= value"""

    def filter(self, data, params):
        return data[data[params['column']] <= float(params['value 1'])].copy()


class BetweenFilterStrategy(FilterStrategy):
    """value1 < X < value2"""

    def filter(self, data, params):
        return data[
            (data[params['column']] > params['value 1']) &\
            (data[params['column']] < params['value 2'])].copy()


class BetweenEqualFilterStrategy(FilterStrategy):
    """value1 <= X <= value2"""

    def filter(self, data, params):
        return data[
            (data[params['column']] >= params['value 1']) &\
            (data[params['column']] <= params['value 2'])].copy()

class BetweenLowerEqualFilterStrategy(FilterStrategy):
    """value1 <= X < value2"""

    def filter(self, data, params):
        return data[
            (data[params['column']] >= params['value 1']) &\
            (data[params['column']] < params['value 2'])].copy()

class BetweenHigherEqualFilterStrategy(FilterStrategy):
    """value1 < X <= value2"""

    def filter(self, data, params):
        return data[
            (data[params['column']] > params['value 1']) &\
            (data[params['column']] <= params['value 2'])].copy()
