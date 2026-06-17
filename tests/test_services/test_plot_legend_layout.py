from quick_ternaries.models.setup_menu_model import SetupMenuModel
from quick_ternaries.services.cartesian_plot_maker import CartesianPlotMaker
from quick_ternaries.services.ternary_plot_maker import TernaryPlotMaker


def test_cartesian_layout_applies_custom_legend_settings():
    setup_model = SetupMenuModel()
    settings = setup_model.advanced_settings
    settings.legend_position = "custom"
    settings.legend_x = 1.2
    settings.legend_y = 0.4
    settings.legend_coordinate_reference = "paper"
    settings.legend_xanchor = "left"
    settings.legend_yanchor = "middle"
    settings.legend_orientation = "horizontal"

    layout = CartesianPlotMaker()._create_layout(setup_model)

    assert layout.legend.x == 1.2
    assert layout.legend.y == 0.4
    assert layout.legend.xref == "paper"
    assert layout.legend.yref == "paper"
    assert layout.legend.xanchor == "left"
    assert layout.legend.yanchor == "middle"
    assert layout.legend.orientation == "h"


def test_ternary_layout_applies_legend_position_preset():
    setup_model = SetupMenuModel()
    setup_model.advanced_settings.legend_position = "bottom-center"

    layout = TernaryPlotMaker()._create_layout(setup_model)

    assert layout.legend.x == 0.5
    assert layout.legend.y == 0.0
    assert layout.legend.xanchor == "center"
    assert layout.legend.yanchor == "bottom"
