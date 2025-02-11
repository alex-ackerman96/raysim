######################################################################################################################################################################################
#   IMPORTS (built-in, third-party, custom)   ########################################################################################################################################
######################################################################################################################################################################################

# built-in imports
import os
import re
import sys
import json

# PyQt6 imports
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QTextEdit, QGridLayout, QSlider, QFrame, QLabel, QGroupBox, QScrollArea, QVBoxLayout, QSizePolicy, QSpacerItem
from PyQt6.QtGui import QIcon, QScreen, QAction, QColor, QPalette, QTextBlockFormat, QTextCursor, QFontMetrics

# Matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# Basic widget imports
from modules.base.customwidgets import PlaceHolderFrame, TitleBar

######################################################################################################################################################################################
# AUTHORSHIP METADATA   ##############################################################################################################################################################
######################################################################################################################################################################################
__author__ = "Alex Ackerman"
__company__ = "Avicena Tech"
__copyright__ = "Copyright 2024, Avicena Tech"
__credits__ = ["Alex Ackerman"]
__license__ = "GPL"
__version__ = "0.0.0"
__date__ = "April 8, 2024"
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

# # Import theme
# with open('resources/dark.qss', 'r') as f:
#     darktheme = f.read()
    
# with open('resources/light.qss', 'r') as f:
#     lighttheme = f.read()

theme = darktheme

colors_json_path = os.path.join(resources_dir, 'colors.json')

# Import colors
with open(colors_json_path, 'r') as f:
    colors = json.load(f)

BLUE0 = colors["blues"]["darkblue"]
BLUE1 = colors["blues"]["medblue"]
BLUE2 = colors["blues"]["lightblue"]
BLUE3 = colors["blues"]["skyblue"]

GRAY3 = colors["grays"]["neutral"]

class Terminal(QFrame):
    
    def __init__(self, titlebar : bool = True, title : str = "Terminal"):
        """
        Initialize the terminal widget.
        """
        super().__init__()
        # self.setMaximumHeight(250)
        self.setMinimumWidth(600)
        self.setStyleSheet(theme)
        self.frame_layout = QGridLayout()
        self.frame_layout.setSpacing(0)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)                                                                # left, top, right, bottom
        self.setLayout(self.frame_layout)
        if titlebar == True:
            self.label = TitleBar(title)
            self.label.setMaximumHeight(20)
            self.frame_layout.addWidget(self.label, 0, 0)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)                                                                                # Make the text edit read-only
        
        # Redirect stdout to the QTextEdit
        sys.stdout = OutLog(self.text_edit, sys.stdout)
        self.frame_layout.addWidget(self.text_edit, 1, 0)
        

class OutLog:
    def __init__(self, edit, out=None, color=None):
        """
        (edit, out=None, color=None) -> can write stdout, stderr to a QTextEdit.
        edit = QTextEdit
        out = alternate stream (can be the original sys.stdout)
        color = alternate color (i.e. color stderr a different color)
        """
        self.linecount = 0
        self.edit = edit
        self.out = out
        self.color = color
        self.cursor = self.edit.textCursor()

    def write(self, m):
        """
        write(m) -> write the text to the QTextEdit.
        Args:
            m (str): text to write
        """
        # Convert ANSI escape codes to HTML tags
        m = m.replace(" ", "&nbsp;")
        m = m.replace("\n", "<br>")
        html_text = self.convert_ansi_to_html(m)
        self.edit.setTextCursor(self.cursor)
        self.cursor.insertHtml(html_text + "\r")
        # if self.out:
        #     self.out.write(m)

    def flush(self):
        """
        Flush the QTextEdit.
        """
        if self.out:
            self.out.flush()

    def convert_ansi_to_html(self, text):
        """
        Convert ANSI escape codes to HTML tags.
        """
        # Define a dictionary to map ANSI codes to HTML tags
        ansi_to_html = {
            "0;30": "<span style='color:#000000'>",  # Black
            "0;31": "<span style='color:#F00000'>",  # Red
            "0;32": "<span style='color:#00F000'>",  # Green
            "0;33": "<span style='color:#F0F000'>",  # Yellow
            "0;34": "<span style='color:#072EDB'>",  # Blue
            "0;35": "<span style='color:#F000F0'>",  # Magenta
            "0;36": "<span style='color:#00F0F0'>",  # Cyan
            "0;37": "<span style='color:#FFFFFF'>",  # White
            "1;30": "<span style='color:#000000;font-weight:bold'>",  # Bold Black
            "1;31": "<span style='color:#FF0000;font-weight:bold'>",  # Bold Red
            "1;32": "<span style='color:#00FF00;font-weight:bold'>",  # Bold Green
            "1;33": "<span style='color:#FFFF00;font-weight:bold'>",  # Bold Yellow
            "1;34": "<span style='color:#0000FF;font-weight:bold'>",  # Bold Blue
            "1;35": "<span style='color:#FF00FF;font-weight:bold'>",  # Bold Magenta
            "1;36": "<span style='color:#00FFFF;font-weight:bold'>",  # Bold Cyan
            "1;37": "<span style='color:#FFFFFF;font-weight:bold'>",  # Bold White
            "0": "</span>",  # Reset
        }
        # Use a regular expression to replace ANSI codes with HTML tags
        html_text = re.sub(r"\033\[(.*?)m", lambda match: ansi_to_html.get(match.group(1), ""), text)
        return html_text        