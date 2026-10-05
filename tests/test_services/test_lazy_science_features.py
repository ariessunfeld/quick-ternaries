"""Scientific features still work when their dependencies are loaded on demand."""

from pathlib import Path

import numpy as np
import pandas as pd

from quick_ternaries.models.setup_menu_model import SetupMenuModel
from quick_ternaries.services.zmap_plot_maker import ZmapPlotMaker
from quick_ternaries.utils.contour_utils import compute_kde_contours


def test_density_contours_load_their_dependencies_on_use():
    data = np.random.default_rng(42).normal(size=(100, 2))
    success, contours = compute_kde_contours(data, levels=[0.68], grid_points=40)
    assert success
    assert len(contours) == 1
    assert any(len(segment) >= 12 for segment in contours[0])
    assert all(np.isfinite(segment).all() for segment in contours[0])


def test_zmap_computes_correlations_and_writes_heatmaps(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    values = np.arange(12, dtype=float)
    df = pd.DataFrame({"category": ["rock"] * 12, "A": values, "B": values * 2, "C": -values})
    maker = ZmapPlotMaker()
    figures = []
    original_style = maker._apply_styling

    def capture_figure(figure, setup):
        figures.append(figure)
        original_style(figure, setup)

    monkeypatch.setattr(maker, "_apply_styling", capture_figure)
    assert maker._generate_heatmaps(df, "category", ["A", "B", "C"], SetupMenuModel())
    assert len(maker.heatmap_files) == 3
    np.testing.assert_allclose(figures[0].data[0].z, [[1], [-1]])
    for filename, target in maker.heatmap_files:
        html = Path(filename).read_text(encoding="utf-8")
        assert "Plotly.newPlot" in html
        assert f"Spearman's R: {target}" in html
