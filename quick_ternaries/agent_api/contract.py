"""Shared, Qt-independent read contract and safe diagnostics."""

TRACE_SECTIONS = {
    "appearance": (
        "trace_color", "point_shape", "point_size", "point_on", "line_on",
        "line_style", "line_thickness", "outline_color", "outline_thickness",
        "exclude_from_legend", "show_advanced_settings_on",
    ),
    "heatmap": (
        "heatmap_on", "heatmap_use_advanced", "heatmap_column", "heatmap_min",
        "heatmap_max", "heatmap_colorscale", "heatmap_reverse_colorscale",
        "heatmap_log_transform", "heatmap_sort_mode", "heatmap_bar_orientation",
        "heatmap_colorbar_x", "heatmap_colorbar_y", "heatmap_colorbar_len",
        "heatmap_colorbar_thickness",
    ),
    "sizemap": ("sizemap_on", "sizemap_column", "sizemap_sort_mode", "sizemap_min", "sizemap_max"),
    "transforms": (
        "convert_from_wt_to_molar", "vertical_offset_on", "vertical_offset_value",
        "vertical_exaggeration_on", "vertical_exaggeration_factor", "vertical_line_only",
        "vertical_line_x_value", "min_max_normalize",
    ),
    "contour": (
        "contour_level", "contour_percentile", "density_contour_on", "density_contour_color",
        "density_contour_thickness", "density_contour_percentile", "density_contour_name",
        "density_contour_multiple", "density_contour_percentiles", "density_contour_line_style",
    ),
    "apex_colors": ("custom_colorscale_on", "apex_red_mapping", "apex_green_mapping", "apex_blue_mapping"),
}
SECTION_NAMES = ("identity", *TRACE_SECTIONS, "filters")
EXCLUDED = [
    "data_rows", "full_file_paths", "rendered_points_and_render_status",
    "contour_source_points_and_error_entries", "uncommitted_editor_text",
    "setup_scaling_formulas_advanced_settings_and_other_labels",
]


class ApiError(ValueError):
    """A stable code with a fixed, credential-free explanation."""

    def __init__(self, code, message, status=400):
        self.code, self.status = code, status
        super().__init__(message)


def coverage(included):
    return {"included": list(included), "excluded": EXCLUDED,
            "partial": True, "values": "committed_model_settings",
            "truncated_means": "returned_values_shortened_not_missing_features"}
