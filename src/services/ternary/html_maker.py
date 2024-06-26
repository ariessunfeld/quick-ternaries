"""Ternary HTML file maker"""

from src.models.ternary.model import TernaryModel
from src.services.ternary.plot_maker import TernaryPlotMaker
from src.services.ternary.trace_maker import (
    TraceMolarConversionException,
    TraceFilterFloatConversionException
)

from PySide6.QtWidgets import QMessageBox

class TernaryHtmlMaker:
    
    def __init__(self):
        self.plot_maker = TernaryPlotMaker()

    def make_html(self, model: TernaryModel):
        try:
            plot = self.plot_maker.make_plot(model)
            html = plot.to_html()
            javascript = """
                <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
                <script type="text/javascript">
                    document.addEventListener("DOMContentLoaded", function() {
                        new QWebChannel(qt.webChannelTransport, function (channel) {
                            window.plotlyInterface = channel.objects.plotlyInterface;
                            var plotElement = document.getElementsByClassName('plotly-graph-div')[0];
                            plotElement.on('plotly_selected', function(eventData) {
                                if (eventData) {
                                    var indices = eventData.points.map(function(pt) {
                                        return {pointIndex: pt.pointIndex, curveNumber: pt.curveNumber};
                                    });
                                    window.plotlyInterface.receive_selected_indices(indices);
                                }
                            });
                        });
                    });
                </script>
            """
            return html + javascript
        except TraceMolarConversionException as err:
            msg = f"An error occurred while trying to parse the chemical formula for the column '{err.column}' "
            msg += f"in Trace {err.trace_id}.\n\nThe custom chemical formula provided was '{err.bad_formula}'.\n\n"
            msg += f"Please enter a valid formula that can be parsed to compute molar mass, or un-check the "
            msg += f"'convert from wt% to molar' option."
            QMessageBox.critical(None, 'Error parsing formula', msg)
        except TraceFilterFloatConversionException as err:
            msg = f"An error occured while trying to apply a filter in Trace {err.trace_id}.\n\n"
            msg += f"The filter that caused the error is Filter {err.filter_id}\n\n"
            msg += f"The error message is: {err.message}."
            QMessageBox.critical(None, 'Error applying filter', msg)
