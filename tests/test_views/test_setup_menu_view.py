from types import SimpleNamespace

from quick_ternaries.views.setup_menu_view import SetupMenuView


def test_dependency_condition_supports_case_insensitive_tuple_values():
    section_model = SimpleNamespace(legend_position="Custom")

    assert SetupMenuView._dependency_condition_met(
        section_model, ("legend_position", "custom")
    )
