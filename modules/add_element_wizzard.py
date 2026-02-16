######################################################################################################################################################################################
#   IMPORTS (built-in, third-party, custom)   ########################################################################################################################################
######################################################################################################################################################################################
import os
import sys
import ctypes

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import pyqtSignal, QEvent, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QGroupBox, QComboBox, QPushButton, QLabel, QRadioButton, QButtonGroup, QFrame, QLineEdit

from data.appdata import AppData


######################################################################################################################################################################################
# AUTHORSHIP METADATA   ##############################################################################################################################################################
######################################################################################################################################################################################
__author__ = "Alex Ackerman"
__company__ = "Avicena Tech"
__copyright__ = "Copyright 2024, Avicena Tech"
__credits__ = ["Alex Ackerman"]
__license__ = "GPL"
__version__ = "0.0.0"
__date__ = "November 24, 2023"
__maintainer__ = "Alex Ackerman"
__email__ = "alex.a@avicena.tech"
__status__ = "Development"

######################################################################################################################################################################################
#   RESOURCES   ######################################################################################################################################################################
######################################################################################################################################################################################
# Get the root directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Construct the path to the 'resources' directory
resources_dir = os.path.join(root_dir, 'resources')
# Convert the path to an absolute path
resources_dir = os.path.abspath(resources_dir)

sys.path.append(resources_dir)

darktheme_path = os.path.join(resources_dir, 'dark.qss')
lighttheme_path = os.path.join(resources_dir, 'light.qss')

with open(darktheme_path, 'r') as f:
    darktheme = f.read()
    
with open(lighttheme_path, 'r') as f:
    lighttheme = f.read()

theme = darktheme

# LOGO_ICON_PATH = os.path.join(os.getcwd(), "resources/avicena_bordered.ico")
LOGO_ICON_PATH = "main/resources/avicena_bordered.ico"

class AddElementDialog(QWidget):
    """
    This window is a QWidget. If it has no parent, it will appear as a free-floating window. 
    """
    window_closed = pyqtSignal()

    def __init__(self, parent = None):
        """
        Initialize the about window widget.
        Args:
            parent (QWidget): The parent widget of the about window.
        """
        super().__init__(parent)
        self.company = AppData.company
        self.appname = AppData.appname + " - Add New Element"                                                           # Application name
        self.version = AppData.version                                                                                  # Application version
        self.appid = self.company.lower() + "." + self.appname.replace(" ", "_").lower() + "." + self.version           # Company, product, version
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.appid)                                       # App icon in system tray
        # Get dimensions of primary screen
        primary_screen = QApplication.primaryScreen()
        screen_width = primary_screen.size().width()
        screen_height = primary_screen.size().height()
        # Set default screen dimensions based on primary screen resolution
        default_window_width = int(screen_width * 0.4)
        default_window_height = int(screen_height * 0.4)
        self.resize(default_window_width, default_window_height)
        #Set window icon
        self.setWindowIcon(QIcon(LOGO_ICON_PATH))
        self.setStyleSheet(theme)
        self.setWindowTitle("Add New Element")
        self.window_layout = QGridLayout()
        self.setLayout(self.window_layout)

        self.frame = QFrame(self)
        self.frame_layout = QGridLayout(self.frame)
        self.frame.setLayout(self.frame_layout)
        self.window_layout.addWidget(self.frame, 0, 0)

        self.surfacetype_group = QGroupBox("Surface Type")
        self.surfacetype_group.setFixedSize(400, 200)
        self.surfacetype_layout = QGridLayout()
        self.surfacetype_group.setLayout(self.surfacetype_layout)

        self.spherical_radio = QRadioButton("Spherical Surface")
        self.aspheric_radio = QRadioButton("Aspheric Surface")
        self.planar_radio = QRadioButton("Planar Surface")

        self.surfacetype_layout.addWidget(self.spherical_radio, 0, 0)
        self.surfacetype_layout.addWidget(self.aspheric_radio, 0, 1)
        self.surfacetype_layout.addWidget(self.planar_radio, 0, 2)

        self.surfacetype_buttongroup = QButtonGroup()
        self.surfacetype_buttongroup.addButton(self.spherical_radio)
        self.surfacetype_buttongroup.addButton(self.aspheric_radio)
        self.surfacetype_buttongroup.addButton(self.planar_radio)
        self.surfacetype_buttongroup.buttonClicked.connect(self.surfacetype_selected)

        self.concave_radio = QRadioButton("Concave")
        self.convex_radio = QRadioButton("Convex")
        self.surfacetype_layout.addWidget(self.concave_radio, 1, 0)
        self.surfacetype_layout.addWidget(self.convex_radio, 1, 2)

        self.frame_layout.addWidget(self.surfacetype_group, 0, 0, 1, 2)

        self.surface_profile_group = QGroupBox("Surface Profile")
        self.surface_profile_layout = QGridLayout()
        self.surface_profile_group.setLayout(self.surface_profile_layout)
        self.radius_label = QLabel("Radius of Curvature (R):")
        self.radius_input = QLineEdit()
        self.surface_profile_layout.addWidget(self.radius_label, 0, 0)
        self.surface_profile_layout.addWidget(self.radius_input, 0, 1)
        self.conic_constant_label = QLabel("Conic Constant (k):")
        self.conic_constant_input = QLineEdit()
        self.surface_profile_layout.addWidget(self.conic_constant_label, 1, 0)
        self.surface_profile_layout.addWidget(self.conic_constant_input, 1, 1)
        self.frame_layout.addWidget(self.surface_profile_group, 1, 0, 1, 1)

    def surfacetype_selected(self, button):
        self.surftype = button.text()
        if self.surftype == "Spherical Surface":
            self.concave_radio.setDisabled(False)
            self.convex_radio.setDisabled(False)
            self.radius_input.setDisabled(False)
            self.conic_constant_input.setDisabled(True)
        elif self.surftype == "Planar Surface":
            self.radius_input.setDisabled(True)
            self.conic_constant_input.setDisabled(True)
            self.concave_radio.setDisabled(True)
            self.convex_radio.setDisabled(True)
        else:
            self.radius_input.setDisabled(False)
            self.conic_constant_input.setDisabled(False)
            self.concave_radio.setDisabled(False)
            self.convex_radio.setDisabled(False)

    def nextbutton_clicked(self):
        print(f"next button clicked: {self.stepcount}")
        self.stepcount += 1
        self.clear_wizzard()
        self.update_wizzard()
        print(self.stepcount)

    def backbutton_clicked(self):
        print(f"back button clicked: {self.stepcount}")
        self.stepcount -= 1
        self.clear_wizzard()
        self.update_wizzard()
        print(self.stepcount)

    def clear_wizzard(self):
        for i in reversed(range(self.window_layout.count())):
            item = self.window_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QGroupBox):
                self.window_layout.removeItem(item)
                widget.setParent(None)

    def update_wizzard(self):
        if self.stepcount == 1:
            if self.devicetype == None:
                self.nextbutton.setEnabled(False)
            self.window_layout.addWidget(self.devicetype_group, 0, 0, 1, 2)
        if self.stepcount == 2:
            self.window_layout.addWidget(self.backplane_group, 0, 0, 1, 2)        
        if self.stepcount == 3:
            self.window_layout.addWidget(self.led_group, 0, 0, 1, 2)

    def closeEvent(self, event: QEvent):
        """
        Handle the close event of the about window.
        Args:
            event (QEvent): The close event of the about window.
        """
        self.window_closed.emit()
        event.accept()