######################################################################################################################################################################################
#   IMPORTS (built-in, third-party, custom)   ########################################################################################################################################
######################################################################################################################################################################################
import os
import sys
import ctypes

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import pyqtSignal, QEvent, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QGroupBox, QComboBox, QPushButton, QLabel, QRadioButton, QButtonGroup

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
        self.appname = AppData.appname + " - New DUT Wizzard"                                                           # Application name
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
        self.setWindowTitle("New DUT Wizzard")
        self.window_layout = QGridLayout()
        self.setLayout(self.window_layout)

        self.stepcount = 0
        self.devicetype = None
        self.backplane = None

    #     #############################################################################################################################################################
    #     self.devicetype_group = QGroupBox("Device Type")
    #     self.devicetype_group.setFixedSize(800, 400)
    #     self.devicetype_group_layout = QGridLayout()
    #     self.devicetype_group.setLayout(self.devicetype_group_layout)
    #     self.asic_tx = QRadioButton("Active TX (ASIC)")
    #     self.asic_tx.clicked.connect(self.set_asic_tx)
    #     self.asic_rx = QRadioButton("Active RX (ASIC)")
    #     self.asic_rx.clicked.connect(self.set_asic_rx)
    #     self.asic_duplex = QRadioButton("Active duplex (ASIC)")
    #     self.asic_duplex.clicked.connect(self.set_asic_duplex)
    #     self.passive_tx = QRadioButton("Passive TX")
    #     self.passive_tx.clicked.connect(self.set_passive_tx)
    #     self.passive_rx = QRadioButton("Passive RX")
    #     self.passive_rx.clicked.connect(self.set_passive_rx)
    #     self.backplane_button_group = QButtonGroup()
    #     self.backplane_button_group.addButton(self.asic_tx)
    #     self.backplane_button_group.addButton(self.asic_rx)
    #     self.backplane_button_group.addButton(self.asic_duplex)
    #     self.backplane_button_group.addButton(self.passive_tx)
    #     self.backplane_button_group.addButton(self.passive_rx)
    #     self.devicetype_group_layout.addWidget(self.passive_tx, 1, 0, 1, 1)
    #     self.devicetype_group_layout.addWidget(self.passive_rx, 2, 0, 1, 1)
    #     self.devicetype_group_layout.addWidget(self.asic_tx, 3, 0, 1, 1)
    #     self.devicetype_group_layout.addWidget(self.asic_rx, 4, 0, 1, 1)
    #     self.devicetype_group_layout.addWidget(self.asic_duplex, 5, 0, 1, 1)

    #     #############################################################################################################################################################
    #     self.backplane_group = QGroupBox("Backplane")
    #     self.backplane_group.setFixedSize(800, 400)
    #     self.backplane_group_layout = QGridLayout()
    #     self.backplane_group.setLayout(self.backplane_group_layout)
    #     self.backplane_selection = QComboBox()
    #     self.passive_tx_backplane_options = list(passive.backplanes.keys())
    #     self.backplane_selection.clear()
    #     self.backplane_selection.activated.connect(self.set_backplane)
    #     self.backplane_group_layout.addWidget(self.backplane_selection, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    #     self.backplane_img = QLabel(self.backplane_group)
    #     self.backplane_group_layout.addWidget(self.backplane_img, 0, 1, 2, 2, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
    #     #############################################################################################################################################################
    #     self.led_group = QGroupBox("LEDs")
    #     self.led_group.setFixedSize(800, 400)
    #     #############################################################################################################################################################
    #     self.nextbutton = QPushButton("Next")
    #     self.nextbutton.setFixedHeight(30)
    #     self.nextbutton.setFixedWidth(100)
    #     self.nextbutton.clicked.connect(self.nextbutton_clicked)
    #     self.window_layout.addWidget(self.nextbutton, 1, 1, 1, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    #     self.backbutton = QPushButton("Back")
    #     self.backbutton.setFixedHeight(30)
    #     self.backbutton.setFixedWidth(100)
    #     self.backbutton.clicked.connect(self.backbutton_clicked)
    #     self.window_layout.addWidget(self.backbutton, 1, 0, 1, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    
    # def set_asic_tx(self):
    #     self.devicetype = "asic-tx"
    #     print(self.devicetype)
    #     self.backplane_img.clear()
    #     self.backplane_img.setPixmap(QPixmap())
    #     self.backplane_selection.clear()
    #     self.nextbutton.setEnabled(True)

    # def set_asic_rx(self):
    #     self.devicetype = "asic-rx"
    #     print(self.devicetype)
    #     self.backplane_img.clear()
    #     self.backplane_img.setPixmap(QPixmap())
    #     self.backplane_selection.clear()
    #     self.nextbutton.setEnabled(True)

    # def set_asic_duplex(self):
    #     self.devicetype = "asic-duplex"
    #     print(self.devicetype)
    #     self.backplane_img.clear()
    #     self.backplane_img.setPixmap(QPixmap())
    #     self.backplane_selection.clear()
    #     self.nextbutton.setEnabled(True)

    # def set_passive_tx(self):
    #     self.devicetype = "passive-tx"
    #     print(self.devicetype)
    #     self.backplane_img.clear()
    #     self.backplane_img.setPixmap(QPixmap())
    #     self.backplane_selection.clear()
    #     self.backplane_selection.addItem("Select backplane...")
    #     self.backplane_selection.model().item(0).setFlags(Qt.ItemFlag.ItemIsEnabled)   
    #     self.backplane_selection.addItems(self.passive_tx_backplane_options)
    #     self.nextbutton.setEnabled(True)

    # def set_passive_rx(self):
    #     self.devicetype = "passive-rx"
    #     print(self.devicetype)
    #     self.backplane_img.clear()
    #     self.backplane_img.setPixmap(QPixmap())
    #     self.backplane_selection.clear()
    #     self.nextbutton.setEnabled(True)

    # def set_backplane(self, index):
    #     selected_backplane = self.backplane_selection.itemText(index)
    #     self.backplane = selected_backplane
    #     if selected_backplane == "GSGR1":
    #         pixmap = QPixmap('main/resources/backplanes/GSG30R1.png')
    #     elif selected_backplane == "CF46R0":
    #         pixmap = QPixmap('main/resources/backplanes/CF46R0.png')

    #     self.backplane_img.clear()
    #     self.backplane_img.setFixedSize(350, 350)
    #     self.backplane_img.setPixmap(pixmap)
    #     self.backplane_img.setScaledContents(True)

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