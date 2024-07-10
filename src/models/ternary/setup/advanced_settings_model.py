from typing import Optional

class AdvancedSettingsModel:
    def __init__(
            self,
            background_color: str = '#e3ecf7', # plotly's default figure color
            gridline_step_size: int = 20,
            ternary_sum: int = 100,
            gridline_color: str = 'rgba(255,255,255,255)',
            paper_color: str = 'rgba(255,255,255,0)',
            title_font: str = 'Open Sans',
            title_font_size: int = 17,
            axis_font: str = 'Open Sans',
            axis_font_size: int = 12,
            tick_font: str = 'Open Sans',
            tick_font_size: int = 14
            ):
        self._background_color = background_color
        self._gridline_step_size = gridline_step_size
        self._ternary_sum = ternary_sum
        self._gridline_color = gridline_color
        self._paper_color = paper_color
        self._title_font = title_font
        self._title_font_size = title_font_size
        self._axis_font = axis_font
        self._axis_font_size = axis_font_size
        self._tick_font = tick_font
        self._tick_font_size = tick_font_size

    @property
    def background_color(self) -> str:
        return self._background_color

    @background_color.setter
    def background_color(self, value: str):
        self._background_color = value

    @property
    def gridline_step_size(self) -> int:
        return self._gridline_step_size

    @gridline_step_size.setter
    def gridline_step_size(self, value: int):
        self._gridline_step_size = value

    @property
    def ternary_sum(self) -> int:
        return self._ternary_sum

    @ternary_sum.setter
    def ternary_sum(self, value: int):
        self._ternary_sum = value

    @property
    def gridline_color(self) -> str:
        return self._gridline_color

    @gridline_color.setter
    def gridline_color(self, value: str):
        self._gridline_color = value

    @property
    def paper_color(self) -> str:
        return self._paper_color

    @paper_color.setter
    def paper_color(self, value: str):
        self._paper_color = value

    @property
    def title_font(self) -> str:
        return self._title_font

    @title_font.setter
    def title_font(self, value: str):
        self._title_font = value

    @property
    def title_font_size(self) -> int:
        return self._title_font_size

    @title_font_size.setter
    def title_font_size(self, value: int):
        self._title_font_size = value

    @property
    def axis_font(self) -> str:
        return self._axis_font

    @axis_font.setter
    def axis_font(self, value: str):
        self._axis_font = value

    @property
    def axis_font_size(self) -> int:
        return self._axis_font_size

    @axis_font_size.setter
    def axis_font_size(self, value: int):
        self._axis_font_size = value

    @property
    def tick_font(self) -> str:
        return self._tick_font
    
    @tick_font.setter
    def tick_font(self, value: str):
        self._tick_font = value

    @property
    def tick_font_size(self) -> int:
        return self._tick_font_size
    
    @tick_font_size.setter
    def tick_font_size(self, value: int):
        self._tick_font_size = value