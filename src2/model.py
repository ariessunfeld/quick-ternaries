from typing import List, Optional, Any, Callable


def ternary(func: Callable) -> Callable:
    """Decorator indicating the property belongs to 'ternary' plots."""
    func._is_ternary = True
    return func

def cartesian(func: Callable) -> Callable:
    """Decorator indicating the property belongs to 'cartesian' plots."""
    func._is_cartesian = True
    return func

def histogram(func: Callable) -> Callable:
    """Decorator indicating the property belongs to 'histogram' plots."""
    func._is_histogram = True
    return func


class DataFile:
    pass



class Trace:
    """Represents a data trace
    
    Contains all the editable attributes for all plot types
    attributes are decorated with plot type membership
    """

    schema_version = '1.0.0'

    @classmethod
    def from_json(data):
        pass # TODO

    def __init__(self, name: str):
        
        """
        Initializes the trace with all the private attriutes
        (and their default values) that appear in the union 
        of all plot types supported by the application
        (e.g. Ternary, Cartesian, Histogram, etc)
        """
        self._name = name
        self._schema_version = Trace.schema_version

        self._point_size = 6  # relevant to ternary and cartesian, not histogram
        self._color = 'blue'  # relevant to ternary, cartesian, and histogram plot types
        self._point_shapes = ['circle', 'square', ...]  # relevant to ternary and cartesian, not histogram
        self._point_shape = 'circle'  # relevant to ternary and cartesian, not histogram
        self._selected_datafile = None  # Relevant to all
        self._available_datafiles = []  # Relevant to all

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, new: str):
        self._name = new

    @property
    def point_size(self) -> int:
        return self._point_size
    
    @point_size.setter
    def point_size(self, new: int):
        self._point_size = new

    

    # Add properties for the other attributes
    # Somehow use decorators to classify them as members of different plot types
    # Want to be able to decorate with @ternary and @cartesian, for example, 
    # to show that these should be available under those plot types
    # Whole idea is to reuse as much as possible of the trace model when switching
    # plot types in the app
    # Should be able to easily access all of the attributes that correspond to a specific plot type
    # so that when it is selected in the app, those attributes are displayed in the GUI
    


class Tab:
    """Represents a tab in the Quick Ternaries application.
    
    A Tab has a name, an ID, and a reference to a Trace object that
    defines the underlying data/plot configuration for that tab.
    """

    def __init__(self, name: str, _id: int, trace: Optional[Trace] = None):
        self.name = name
        self.id = _id
        # if no trace was passed in, create one with default name
        self.trace = trace if trace is not None else Trace(self.name)


class TabMenu:

    """Represents the tab menu for the Quick Ternaries application
    
    This menu consists of a list of tabs. It always contains the Setup Menu
    tab. Tabs can be added, removed, and reordered, with the exception of
    the Setup Menu. There is also a notion of the Active tab, or Current tab.
    """

    def __init__(self, tabs: Optional[List[Tab]]):

        if tabs is None:
            tabs = ...