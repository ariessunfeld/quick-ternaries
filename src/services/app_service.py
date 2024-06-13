from src.services.ternary.html_maker import TernaryHtmlMaker
# from src.services.cartesian.html_maker import CartesianHtmlMaker
# from src.services.depth_profiles.html_maker import DepthProfilesHtmlMaker
# from src.services.zmaps.html_maker import ZMapsHtmlMaker

class AppService:
    def __init__(self):
        self.html_makers = {
            'ternary': TernaryHtmlMaker(),
            'cartesian': None,  # TODO: Instantiate CartesianHtmlMaker
            'depth_profiles': None,  # TODO: Instantiate DepthProfilesHtmlMaker
            'zmaps': None  # TODO: Instantiate ZMapsHtmlMaker
        }

    def write_html(self, model, plot_mode: str):
        plot_mode = plot_mode.lower()
        html_maker = self.html_makers.get(plot_mode)
        if html_maker is not None:
            return html_maker.make_html(model)
        else:
            raise ValueError(f"Unsupported plot mode: {plot_mode}")
