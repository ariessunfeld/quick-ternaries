from typing import Optional

class AdvancedSettingsModel:
    def __init__(
            self,
            opacity: int = 100,
            outline_color: Optional[str] = None,
            outline_thickness: int = 0,
            ):
        self._opacity = opacity
        self._outline_color = outline_color
        self._outline_thickness = outline_thickness

    @property
    def opacity(self) -> int:
        return self._opacity
    
    @opacity.setter
    def opacity(self, value: int):
        self._opacity = value

    @property
    def outline_color(self) -> str:
        return self._outline_color
    
    @outline_color.setter
    def outline_color(self, value: str):
        self._outline_color = value

    @property
    def outline_thickness(self) -> int:
        return self._outline_thickness
    
    @outline_thickness.setter
    def outline_thickness(self, value: int):
        self._outline_thickness = value
