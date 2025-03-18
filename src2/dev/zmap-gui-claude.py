import sys
import os
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import plotly.graph_objects as go

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QHBoxLayout, QDialog
)
from PySide6.QtCore import QUrl, QObject, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings

# ---------------------------------------------------------
# Handler exposed via QWebChannel to receive JS callbacks.
# ---------------------------------------------------------
class PlotHandler(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    @Slot(str, str, str)
    def cellDoubleClicked(self, facies, target, other):
        print(f"Double clicked cell: facies={facies}, target={target}, other={other}")
        self.main_window.generate_scatter_plot(facies, target, other)

# ---------------------------------------------------------
# Main application window.
# ---------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Correlation Heatmap Viewer")
        self.resize(1000, 800)

        # Initialize file path and plot list.
        self.csv_path = None
        self.heatmap_files = []
        self.current_index = 0

        # Main widget and layout.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top control buttons.
        btn_layout = QHBoxLayout()
        self.btnBrowse = QPushButton("Browse CSV")
        self.btnGenerate = QPushButton("Generate Plots")
        self.btnPrev = QPushButton("Prev")
        self.btnNext = QPushButton("Next")
        btn_layout.addWidget(self.btnBrowse)
        btn_layout.addWidget(self.btnGenerate)
        btn_layout.addWidget(self.btnPrev)
        btn_layout.addWidget(self.btnNext)
        main_layout.addLayout(btn_layout)

        # QWebEngineView for displaying the plots.
        self.webView = QWebEngineView()
        
        # Configure WebEngine settings to allow JavaScript and external content
        settings = self.webView.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        main_layout.addWidget(self.webView)

        # Connect signals.
        self.btnBrowse.clicked.connect(self.browse_file)
        self.btnGenerate.clicked.connect(self.generate_plots)
        self.btnPrev.clicked.connect(self.prev_plot)
        self.btnNext.clicked.connect(self.next_plot)

        # Set up QWebChannel for communication from JS.
        self.channel = QWebChannel()
        self.handler = PlotHandler(self)
        self.channel.registerObject("pyHandler", self.handler)
        self.webView.page().setWebChannel(self.channel)

    def browse_file(self):
        # Let the user select a CSV file.
        file_name, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.csv_path = file_name
            print(f"Selected CSV: {self.csv_path}")

    def generate_plots(self):
        if not self.csv_path:
            print("No CSV file selected!")
            return

        # Hardcoded elements list.
        elements = ['SiO2', 'TiO2', 'Al2O3', 'FeOT', 'MgO', 'CaO', 'Na2O', 'K2O', 'MnO']

        # Read the CSV.
        df = pd.read_csv(self.csv_path)
        if 'Facies' not in df.columns:
            print("CSV must have a 'Facies' column.")
            return

        # Get sorted facies values.
        facies_list = sorted(df['Facies'].unique())

        # Group the data by facies and compute pairwise Spearman correlations.
        correlations = {}
        pvals = {}
        for facies, group in df.groupby('Facies'):
            data = group[elements].dropna()
            corr_matrix, p_matrix = spearmanr(data)
            corr_df = pd.DataFrame(corr_matrix, index=elements, columns=elements)
            pval_df = pd.DataFrame(p_matrix, index=elements, columns=elements)
            correlations[facies] = corr_df
            pvals[facies] = pval_df

        # Ensure plots folder exists.
        plots_dir = "plots"
        if not os.path.exists(plots_dir):
            os.makedirs(plots_dir)

        # Reset heatmap files list.
        self.heatmap_files = []

        # Create one heatmap for each target element.
        for target in elements:
            other_elements = [e for e in elements if e != target]
            z_matrix = []
            customdata = []  # will hold [facies, otherElement] for each cell.
            for other in other_elements:
                row = []
                row_custom = []
                for facies in facies_list:
                    r = correlations[facies].loc[target, other]
                    p = pvals[facies].loc[target, other]
                    # Only display r if significant.
                    if p <= 0.05:
                        row.append(r)
                    else:
                        row.append(None)
                    row_custom.append([facies, other])
                z_matrix.append(row)
                customdata.append(row_custom)

            # Build the heatmap figure.
            fig = go.Figure(data=go.Heatmap(
                z=z_matrix,
                x=facies_list,
                y=other_elements,
                customdata=customdata,
                colorscale='RdBu',  # cool-warm colorscale.
                zmin=-1,
                zmax=1,
                showscale=True,
                hoverongaps=False
            ))

            fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False)
            fig.update_xaxes(showgrid=False)
            fig.update_layout(
                title=f"Spearman's R: {target} vs Other Elements",
                xaxis_title="Facies",
                yaxis_title="Element",
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(l=50, r=50, t=50, b=50)
            )

            # Prepare custom JavaScript to capture double-click events.
            js_code = """
<script>
function setupDoubleClick() {
    var myPlot = document.getElementById('plot');
    var targetInfoEl = document.getElementById('targetElementInfo');
    
    if (!targetInfoEl) {
        console.error("Target element info div not found!");
        setTimeout(setupDoubleClick, 100);  // retry
        return;
    }
    
    var targetElement = targetInfoEl.innerText;
    console.log("Target element:", targetElement);  // Debug output
    
    if(myPlot && myPlot.on) {
        var lastClickTime = 0;
        myPlot.on('plotly_click', function(data) {
            var currentTime = new Date().getTime();
            if(currentTime - lastClickTime < 300) {
                 if(data.points.length > 0) {
                      var point = data.points[0];
                      var facies = point.customdata[0];
                      var otherElement = point.customdata[1];
                      console.log("Double clicked:", facies, targetElement, otherElement);  // Debug output
                      if (window.pyHandler && window.pyHandler.cellDoubleClicked) {
                          window.pyHandler.cellDoubleClicked(facies, targetElement, otherElement);
                      } else {
                          console.error("pyHandler not available");  // Debug output
                      }
                 }
            }
            lastClickTime = currentTime;
        });
        console.log("Double-click handler set up successfully");  // Debug output
    } else {
        console.error("Plot element not ready:", myPlot);  // Debug output
        setTimeout(setupDoubleClick, 100);  // retry
    }
}

// Make sure the page is fully loaded before trying to set up the handler
if (document.readyState === "complete") {
    setupDoubleClick();
} else {
    window.addEventListener('load', function() {
        setTimeout(setupDoubleClick, 500);  // Give a bit more time after load
    });
}
</script>
"""
            # Generate HTML with Plotly and inject the JavaScript and target info div.
            html_str = fig.to_html(include_plotlyjs=True, full_html=True, div_id="plot", config={"doubleClick": False})
            
            # Inject a hidden div before the closing body tag
            target_div = f'<div id="targetElementInfo" style="display:none;">{target}</div>'
            html_str = html_str.replace("</body>", f"{target_div}\n{js_code}\n</body>")

            # Write to file.
            file_path = os.path.join(plots_dir, f"heatmap_{target}.html")
            with open(file_path, "w") as f:
                f.write(html_str)
            self.heatmap_files.append(os.path.abspath(file_path))
            print(f"Generated plot for {target} at {file_path}")

        # After generating all plots, start with the first one.
        self.current_index = 0
        self.load_current_plot()

    def load_current_plot(self):
        if not self.heatmap_files:
            return
        file_path = self.heatmap_files[self.current_index]
        url = QUrl.fromLocalFile(file_path)
        self.webView.setUrl(url)
        print(f"Loaded plot: {file_path}")

    def next_plot(self):
        if not self.heatmap_files:
            return
        self.current_index = (self.current_index + 1) % len(self.heatmap_files)
        self.load_current_plot()

    def prev_plot(self):
        if not self.heatmap_files:
            return
        self.current_index = (self.current_index - 1) % len(self.heatmap_files)
        self.load_current_plot()

    def generate_scatter_plot(self, facies, target, other):
        """Generate a scatter plot (with best-fit line) for the given facies and element pair,
           then display it in a free-standing QDialog."""
        if not self.csv_path:
            return

        print(f"Generating scatter plot for: facies={facies}, target={target}, other={other}")

        # Read the CSV and filter by facies.
        df = pd.read_csv(self.csv_path)
        df_f = df[df['Facies'] == facies]
        if df_f.empty:
            print(f"No data for facies: {facies}")
            return

        # Get data for the two elements.
        try:
            x_data = df_f[target]
            y_data = df_f[other]
        except KeyError:
            print(f"Columns {target} and/or {other} not found in CSV.")
            return

        # Compute the best fit line.
        coeffs = np.polyfit(x_data, y_data, 1)
        slope, intercept = coeffs
        x_line = np.array([x_data.min(), x_data.max()])
        y_line = slope * x_line + intercept

        # Compute correlation coefficient
        r_value = np.corrcoef(x_data, y_data)[0, 1]

        # Create scatter plot figure.
        scatter_fig = go.Figure()
        scatter_fig.add_trace(go.Scatter(
            x=x_data, y=y_data, mode='markers', name='Data'
        ))
        scatter_fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode='lines', 
            name=f'Best Fit (r = {r_value:.3f})'
        ))
        scatter_fig.update_layout(
            title=f"Scatter: {target} vs {other} for Facies {facies}",
            xaxis_title=target,
            yaxis_title=other,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=50, r=50, t=50, b=50)
        )

        # Write the scatter plot to an HTML file.
        plots_dir = "plots"
        scatter_file = os.path.join(plots_dir, "scatter_temp.html")
        scatter_html = scatter_fig.to_html(include_plotlyjs=True, full_html=True, div_id="plot")
        with open(scatter_file, "w") as f:
            f.write(scatter_html)

        # Open a new dialog with a QWebEngineView to show the scatter plot.
        scatter_dialog = QDialog(self)
        scatter_dialog.setWindowTitle(f"Scatter Plot: {target} vs {other} (Facies {facies})")
        layout = QVBoxLayout(scatter_dialog)
        scatter_view = QWebEngineView()
        
        # Configure WebEngine settings for the scatter view
        settings = scatter_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        layout.addWidget(scatter_view)
        scatter_view.setUrl(QUrl.fromLocalFile(os.path.abspath(scatter_file)))
        scatter_dialog.resize(800, 600)
        scatter_dialog.exec()

# ---------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
