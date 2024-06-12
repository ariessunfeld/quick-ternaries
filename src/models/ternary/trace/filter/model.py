from typing import Optional, List, Union

class FilterModel:
    
    CATEGORICAL_OPERATIONS = ['Equals', 'One of']
    NUMERICAL_COMPARISON = ['<', '≤', '>', '≥']
    NUMERICAL_RANGE = ['a < x < b', 'a ≤ x ≤ b', 'a < x ≤ b', 'a ≤ x < b']
    NUMERICAL_OPERATIONS = CATEGORICAL_OPERATIONS + NUMERICAL_COMPARISON + NUMERICAL_RANGE

    def __init__(
            self, 
            available_columns: Optional[List[str]] = None,
            selected_column: Optional[str] = None,
            available_filter_operations: List[str] = None,
            selected_filter_operation: str = None,
            available_one_of_filter_values: Optional[List[str]] = None,
            selected_one_of_filter_values: Optional[List[str]] = None,
            filter_values: Optional[Union[str, float]] = None,
            filter_value_a: Optional[float] = None,
            filter_value_b: Optional[float] = None):
        
        self._available_columns = available_columns
        self._selected_column = selected_column
        self._available_filter_operations = available_filter_operations or self.CATEGORICAL_OPERATIONS
        self._selected_filter_operation = selected_filter_operation or self.CATEGORICAL_OPERATIONS[0]
        self._available_one_of_filter_values = available_one_of_filter_values
        self._selected_one_of_filter_values = selected_one_of_filter_values
        self._filter_values = filter_values
        self._filter_value_a = filter_value_a
        self._filter_value_b = filter_value_b

    @property
    def available_columns(self) -> Optional[List[str]]:
        return self._available_columns

    @available_columns.setter
    def available_columns(self, value: Optional[List[str]]):
        self._available_columns = value

    @property
    def selected_column(self) -> Optional[str]:
        return self._selected_column

    @selected_column.setter
    def selected_column(self, value: Optional[str]):
        self._selected_column = value

    @property
    def available_filter_operations(self) -> List[str]:
        return self._available_filter_operations

    @available_filter_operations.setter
    def available_filter_operations(self, value: List[str]):
        self._available_filter_operations = value

    @property
    def selected_filter_operation(self) -> str:
        return self._selected_filter_operation

    @selected_filter_operation.setter
    def selected_filter_operation(self, value: str):
        self._selected_filter_operation = value

    @property
    def available_one_of_filter_values(self) -> Optional[List[str]]:
        return self._available_one_of_filter_values

    @available_one_of_filter_values.setter
    def available_one_of_filter_values(self, value: Optional[List[str]]):
        self._available_one_of_filter_values = value

    @property
    def selected_one_of_filter_values(self) -> Optional[List[str]]:
        return self._selected_one_of_filter_values

    @selected_one_of_filter_values.setter
    def selected_one_of_filter_values(self, value: Optional[List[str]]):
        self._selected_one_of_filter_values = value

    @property
    def filter_values(self) -> Optional[Union[str, float]]:
        return self._filter_values

    @filter_values.setter
    def filter_values(self, value: Optional[Union[str, float]]):
        self._filter_values = value

    @property
    def filter_value_a(self) -> Optional[float]:
        return self._filter_value_a

    @filter_value_a.setter
    def filter_value_a(self, value: Optional[float]):
        self._filter_value_a = value

    @property
    def filter_value_b(self) -> Optional[float]:
        return self._filter_value_b

    @filter_value_b.setter
    def filter_value_b(self, value: Optional[float]):
        self._filter_value_b = value

    def __str__(self) -> str:
        return str(self.__dict__)
