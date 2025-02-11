from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize

class IconButton(QPushButton):
    def __init__(self, icon, parent=None):
        super(IconButton, self).__init__(parent)
        self.setIcon(QIcon(icon))
        self.setIconSize(QSize(18, 18))
        self.setFixedSize(24, 18)
        self.setStyleSheet('background-color: transparent; border: none;')