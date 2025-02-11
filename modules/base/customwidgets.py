# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 23:03:25 2023

@author: admin
"""
######################################################################################################################################################################################
#   IMPORTS (built-in, third-party, custom)   ########################################################################################################################################
######################################################################################################################################################################################

# built-in imports
import sys
import os

# PyQt6 imports
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QPoint, QRectF, QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import QFrame, QLabel, QGridLayout, QGroupBox, QPushButton, QScrollArea, QLineEdit, QTabWidget
from PyQt6.QtGui import QKeySequence, QKeyEvent, QValidator, QPainter, QPen, QBrush, QColor


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
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Construct the path to the 'resources' directory
resources_dir = os.path.join(root_dir, 'resources')
# Convert the path to an absolute path
resources_dir = os.path.abspath(resources_dir)

sys.path.append(resources_dir)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append("/resources")

darktheme_path = os.path.join(resources_dir, 'dark.qss')
lighttheme_path = os.path.join(resources_dir, 'light.qss')

with open(darktheme_path, 'r') as f:
    darktheme = f.read()
    
with open(lighttheme_path, 'r') as f:
    lighttheme = f.read()

theme = darktheme

class PlaceHolderFrame(QFrame):    
    
    def __init__(self, parent = None):
        super(PlaceHolderFrame, self).__init__(parent)   

class RaisedFrame(QFrame):    
    
    def __init__(self, parent):
        super(RaisedFrame, self).__init__(parent)   
        
class BorderedFrame(QFrame):    
    
    def __init__(self, parent):
        super(BorderedFrame, self).__init__(parent)   
        
class TitleBar(QLabel):
    
    def __init__(self, parent):
        super(TitleBar, self).__init__(parent)  
        self.setMaximumHeight(20)

class BlankFrame(QFrame):
    
    def __init__(self, parent):
        super(BorderedFrame, self).__init__(parent) 

class GroupPane(QGroupBox):

    def __init__(self, parent):
        super(GroupPane, self).__init__(parent)

        self.layout = QGridLayout()
        self.layout.setContentsMargins(4, 4, 4, 4)                                                                       # left, top, right, bottom
        self.setLayout(self.layout)
        #topspacer = QSpacerItem(0, 20)
        #self.layout.addItem(topspacer, 0, 0)

    def addWidget(self, row, widget):
        self.layout.addWidget(widget, row + 1, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        
class ScrollFrame(PlaceHolderFrame):
    
    def __init__(self, parent):
        super(ScrollFrame, self).__init__(parent)
        
        self.setStyleSheet(theme)
        self.baseframe_layout = QGridLayout()
        self.baseframe_layout.setContentsMargins(0, 0, 0, 0)                                                                                # left, top, right, bottom
        self.setLayout(self.baseframe_layout)
        
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.frame = PlaceHolderFrame(parent=self)
        self.frame_layout = QGridLayout()
        self.frame_layout.setContentsMargins(0, 0, 0, 0)                                                                                 # left, top, right, bottom
        self.frame.setLayout(self.frame_layout)
        self.scrollarea.setWidget(self.frame)
        self.baseframe_layout.addWidget(self.scrollarea, 0, 1)

class HexLineEdit(QLineEdit):
    def keyPressEvent(self, event: QKeyEvent):
        """
        Overrides the keyPressEvent to only allow certain characters.
        """
        # Allow only hexadecimal characters
        allowed_chars = "abcdefABCDEF0123456789"
        # Check if the pressed key is the backspace key
        if event.matches(QKeySequence.StandardKey.Backspace):
            super().keyPressEvent(event)
        elif event.text() in allowed_chars:
            super().keyPressEvent(event)
        else:
            # Ignore the key press if the character is not allowed
            pass

class HexValidator(QValidator):
    def validate(self, input_str, pos):
        valid_chars = set('0123456789abcdefABCDEF')
        if all(char in valid_chars for char in input_str):
            return QValidator.State.Acceptable, input_str, pos
        else:
            return QValidator.State.Invalid, input_str, pos
        
class NumValidator(QValidator):
    def validate(self, input_str, pos):
        valid_chars = set('0123456789.')
        if all(char in valid_chars for char in input_str):
            return QValidator.State.Acceptable, input_str, pos
        else:
            return QValidator.State.Invalid, input_str, pos
    