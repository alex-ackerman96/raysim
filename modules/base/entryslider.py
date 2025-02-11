from typing import Union
from PyQt6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QGridLayout, QGroupBox, QSlider, QLineEdit
from PyQt6.QtGui import QImage, QPixmap, QPalette, QColor, QFont
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, Qt

from modules.base.customwidgets import NumValidator, PlaceHolderFrame

class EntrySlider(PlaceHolderFrame):
    def __init__(self, method, valuelabel : str = "Slider", leftlabel : str = "Left", rightlabel : str = "Right", range : tuple = (0, 100), default : int = 50, tickinterval : int = 1, trough : tuple = ("#333333", "#c2c2c2"), entrylength : int = 5):
        super().__init__()

        self.setFixedHeight(80)
        self.setFixedWidth(320)
        self.frame_layout = QGridLayout()
        self.setLayout(self.frame_layout)

        self.method = method
        self.range = range

        # main label
        self.mainlbl = QLabel(valuelabel)
        self.mainlbl.setFont(QFont("Arial", 11))
        self.frame_layout.addWidget(self.mainlbl, 0, 0, 1, 3, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # text entry / current value
        self.entry = QLineEdit()
        self.num = NumValidator()
        self.entry.setValidator(self.num)
        self.entry.setMaxLength(entrylength)
        self.entry.setFixedHeight(20)
        self.entry.setFixedWidth(entrylength * 8)
        self.entry.setFont(QFont("Consolas", 10))
        self.entry.setText(str(default))

        self.entry.returnPressed.connect(self._set_slider_value)

        self.frame_layout.addWidget(self.entry, 0, 3, 1, 1, )

        #left label
        self.leftlbl = QLabel(leftlabel)
        self.leftlbl.setFont(QFont("Consolas", 10))
        self.frame_layout.addWidget(self.leftlbl, 1, 0, 1, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # slider
        self.slider = self.Slider(trough)
        self.slider.setMinimum(range[0])
        self.slider.setMaximum(range[1])
        self.slider.setTickInterval(tickinterval)
        self.slider.setSingleStep(tickinterval)
        self.slider.setValue(default)
        self.slider.valueChanged.connect(self._set_value)
        self.frame_layout.addWidget(self.slider, 1, 1, 1, 4, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        #right label
        self.rightlbl = QLabel(rightlabel)
        self.rightlbl.setFont(QFont("Consolas", 10))
        self.frame_layout.addWidget(self.rightlbl, 1, 5, 1, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _set_value(self, value):
         self.method(value)
         self.entry.setText(str(value))

    def _set_slider_value(self):
        value = self.entry.text()
        if value == '':
                value = self.range[0]
        value = float(value)
        if value < self.range[0]:
             value = self.range[0]
             self.entry.setText(str(value))
        elif value > self.range[1]:
             value = self.range[1]
             self.entry.setText(str(value))
        self.slider.setValue(value)
 
    def set_slider_trough_gradient(self, left : str = None, right : str = None):
        pass


    class Slider(QSlider):
        def __init__(self, trough):
            super().__init__(Qt.Orientation.Horizontal)
            self.setFixedWidth(200)

            self.leftcolor = trough[0]
            self.rightcolor = trough[1]
            self.stylesheet = """
                            Slider::groove:horizontal 
                                                            {{
                                                                border: 1px solid transparent;
                                                                background: qlineargradient(x1:0, y1:1, x2:1, y2:1, stop:0 {leftcolor}, stop:1 {rightcolor});
                                                                height: 4px;
                                                                border-radius: 3px;
                                                            }}
                                Slider::handle:horizontal 
                                                            {{
                                                                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2d3f52, stop:1 #57718c);
                                                                border: 1px solid transparent;
                                                                width: 6px;
                                                                height:20px;
                                                                margin-top: -4px;
                                                                margin-bottom: -4px;
                                                                border-radius: 2px;
                                                            }}
                                Slider::add-page:horizontal
                                                            {{
                                                                background: transparent;
                                                                border-radius: 3px;
                                                            }}
                                Slider::sub-page:horizontal
                                                            {{
                                                                background: transparent;
                                                                border-radius: 3px;
                                                            }}
                            """
            
            formatted_stylesheet = self.stylesheet.format(leftcolor=self.leftcolor, rightcolor=self.rightcolor)
            self.setStyleSheet(formatted_stylesheet)
