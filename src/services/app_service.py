from pathlib import Path
from typing import Dict

from PySide6.QtCore import QUrl

from src.services.ternary.html_maker import TernaryHtmlMaker, BaseHtmlMaker
# from src.services.cartesian.html_maker import CartesianHtmlMaker
# from src.services.depth_profiles.html_maker import DepthProfilesHtmlMaker
# from src.services.zmaps.html_maker import ZMapsHtmlMaker

class AppService:
    def __init__(self):
        self.html_makers: Dict[str, BaseHtmlMaker] = {
            'ternary': TernaryHtmlMaker(),
            'cartesian': None,  # TODO: Instantiate CartesianHtmlMaker
            'depth_profiles': None,  # TODO: Instantiate DepthProfilesHtmlMaker
            'zmaps': None  # TODO: Instantiate ZMapsHtmlMaker
        }

    def write_html(self, model, plot_mode: str) -> QUrl:
        plot_mode = plot_mode.lower()
        html_maker = self.html_makers.get(plot_mode)
        if html_maker is not None:
            html = html_maker.make_html(model)
            
            if html:
                current_directory = Path(__file__).parent
                save_path = current_directory / '..' / 'resources' / 'ternary.html'
                save_path.parent.mkdir(parents=True, exist_ok=True)

                # Save the HTML content to the file
                with save_path.open('w', encoding='utf-8') as file:
                    file.write(html)

                html_object = QUrl.fromLocalFile(str(save_path.resolve()))

                return html_object
        
        else:
            raise ValueError(f"Unsupported plot mode: {plot_mode}")
