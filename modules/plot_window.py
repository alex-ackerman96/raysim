from PyQt6.QtWidgets import  QLineEdit, QPushButton, QCheckBox, QGridLayout, QSlider, QFrame, QLabel, QGroupBox, QScrollArea, QTabWidget, QSpacerItem, QRadioButton, QMessageBox, QFileDialog
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from elements.surfaces import SphericalSurface
from elements.surfaces import AsphericSurface
from elements.lens import Lens
from rays.ray import Ray

class PlotWindow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout
        self.frame_layout = QGridLayout()                                                                                       
        self.setLayout(self.frame_layout)
        
        # Scroll area for plots
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Create plot widgets
        self.cross_section_plot = self.CrossSectionPlot(self)
        self.spot_size_plot = self.SpotSizePlot(self)
        self.wavefront_plot = self.WavefrontPlot(self)

        # Add plots to scroll area
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.cross_section_plot, "2D Cross Section")
        self.tabs.addTab(self.spot_size_plot, "Spot Size")
        self.tabs.addTab(self.wavefront_plot, "Wavefront")
        self.scroll_area.setWidget(self.tabs)

        # Add scroll area to layout
        self.frame_layout.addWidget(self.scroll_area, 0, 0)

    def add_surface(self, surface):
        # Add surface to the cross-section plot
        self.cross_section_plot.ax.plot(surface.center[2], surface.center[1], 'bo')  # Example: plot surface center
        self.cross_section_plot.canvas.draw()


    class CrossSectionPlot(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.layout = QGridLayout()
            self.setLayout(self.layout)
            self.fig, self.ax = plt.subplots()
            self.canvas = FigureCanvas(self.fig)
            self.layout.addWidget(self.canvas, 0, 0)

    class SpotSizePlot(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.layout = QGridLayout()
            self.setLayout(self.layout)
            self.fig, self.ax = plt.subplots()
            self.canvas = FigureCanvas(self.fig)
            self.layout.addWidget(self.canvas, 0, 0)

    class WavefrontPlot(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.layout = QGridLayout()
            self.setLayout(self.layout)
            self.fig, self.ax = plt.subplots()
            self.canvas = FigureCanvas(self.fig)
            self.layout.addWidget(self.canvas, 0, 0)