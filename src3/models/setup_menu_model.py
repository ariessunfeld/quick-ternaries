from dataclasses import dataclass, field, asdict

from src3.models.data_library_model import DataLibraryModel
from src3.models.axis_members_model import AxisMembersModel
from src3.models.plot_labels_model import PlotLabelsModel
from src3.models.column_scaling_model import ColumnScalingModel
from src3.models.chemical_formula_model import ChemicalFormulaModel
from src3.models.advanced_setup_menu_model import AdvancedPlotSettingsModel

@dataclass
class SetupMenuModel:
    data_library: DataLibraryModel = field(default_factory=DataLibraryModel)
    axis_members: AxisMembersModel = field(default_factory=AxisMembersModel)
    plot_labels: PlotLabelsModel = field(default_factory=PlotLabelsModel)
    column_scaling: ColumnScalingModel = field(default_factory=ColumnScalingModel)
    chemical_formulas: ChemicalFormulaModel = field(default_factory=ChemicalFormulaModel)
    advanced_settings: AdvancedPlotSettingsModel = field(default_factory=AdvancedPlotSettingsModel)

    def to_dict(self):
        """Convert the model to a dictionary for serialization."""
        result = asdict(self)
        result['data_library'] = self.data_library.to_dict()
        return result

    @classmethod
    def from_dict(cls, d: dict):
        """Create a model from a dictionary."""
        return cls(
            data_library=DataLibraryModel.from_dict(d.get("data_library", {})),
            plot_labels=PlotLabelsModel(**d.get("plot_labels", {})),
            axis_members=AxisMembersModel(**d.get("axis_members", {})),
            column_scaling=ColumnScalingModel(**d.get("column_scaling", {})),
            chemical_formulas=ChemicalFormulaModel(**d.get("chemical_formulas", {})),
            advanced_settings=AdvancedPlotSettingsModel(
                **d.get("advanced_settings", {})
            ),
        )
