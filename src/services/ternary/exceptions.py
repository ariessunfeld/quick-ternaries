class TraceMolarConversionException(Exception):
    """Exception raised for errors in molar conversion"""
    def __init__(self, trace_id: str, column: str, bad_formula: str, message: str):
        self.trace_id = trace_id
        self.column = column
        self.bad_formula = bad_formula
        self.message = message


class TraceFilterFloatConversionException(Exception):
    """Exception raised for errors converting filter values"""
    def __init__(self, trace_id: str, filter_id: str, message: str):
        self.trace_id = trace_id
        self.filter_id = filter_id
        self.message = message


class BootstrapTraceContourException(Exception):
    """Exception raised when contour calculation fails"""
    def __init__(self, trace_id: str, message: str):
        self.trace_id = trace_id
        self.message = message
