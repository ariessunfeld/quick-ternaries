"""Ternary HTML file maker"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

from src.services.ternary.plot_maker import TernaryPlotMaker
from src.services.ternary.exceptions import (
    TraceMolarConversionException,
    TraceFilterFloatConversionException,
    BootstrapTraceContourException,
    TraceMissingColumnException
)

if TYPE_CHECKING:
    from src.models.ternary import TernaryModel

class BaseHtmlMaker:

    def __init__(self):
        self.plot_maker = None

class TernaryHtmlMaker(BaseHtmlMaker):
    
    def __init__(self):
        self.plot_maker = TernaryPlotMaker()

    def make_html(self, model: 'TernaryModel'):
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
                                        return {pointIndex: pt.customdata[pt.customdata.length - 1], curveNumber: pt.curveNumber};  // the index is the last item in customdata
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
            msg += f"The error message is: {err.message}"
            QMessageBox.critical(None, 'Error applying filter', msg)
        except BootstrapTraceContourException as err:
            msg = f"An error occured while trying to calculate the confidence region in Trace {err.trace_id}.\n\n"
            msg += f"The confidence region could not be computed with sufficient smoothness.\n\n"
            msg += f"Sometimes this is due to large uncertainties or large percentiles."
            QMessageBox.critical(None, err.message, msg)
        except TraceMissingColumnException as err:
            msg = f"An error occured while trying to parse data for Trace {err.trace_id}.\n\n"
            msg += f"The Plot Type chosen in the Start Setup menu expects the datafile\n" 
            msg += f"for Trace {err.trace_id} to include the following columns: {err.column}.\n\n"
            msg += f"Please select the 'Custom' Plot Type or choose a different datafile."
            QMessageBox.critical(None, err.message, msg)
