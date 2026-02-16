from PyQt6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QFrame, QGridLayout, QPushButton, QWidget, QApplication
from PyQt6.QtCore import pyqtSignal



class SurfaceTable(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.popup = None

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.addSurfaceButton = QPushButton("Add Surface...")
        self.addSurfaceButton.clicked.connect(self.add_surface)
        self.layout.addWidget(self.addSurfaceButton, 0, 0)

        self.addLensButton = QPushButton("Add Lens...")
        self.addLensButton.clicked.connect(self.add_lens)
        self.layout.addWidget(self.addLensButton, 0, 1)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Type", "Material", "Position", "Properties"])
        self.width = 300
        
        self.layout.addWidget(self.table, 1, 0, 1, 2)

    def add_surface(self):
        # Always create a new dialog OR re-show the existing one
        if self.popup is None or not self.popup.isVisible():
            # parent=None → top-level window
            self.popup = NewSurfaceDialog(parent=None)
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    def add_lens(self):
        pass

class NewSurfaceDialog(QWidget):
    window_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # If you want an independent window, you can force it:
        # self.setWindowFlag(Qt.Window)

        primary_screen = QApplication.primaryScreen()
        screen_width = primary_screen.size().width()
        screen_height = primary_screen.size().height()

        default_window_width = int(screen_width * 0.4)
        default_window_height = int(screen_height * 0.4)
        self.resize(default_window_width, default_window_height)

        self.setWindowTitle("Add New Surface")
        self.window_layout = QGridLayout(self)

        self.frame = QFrame(self)
        self.frame_layout = QGridLayout(self.frame)
        self.frame.setLayout(self.frame_layout)
        self.window_layout.addWidget(self.frame, 0, 0)


    def closeEvent(self, event):
        self.window_closed.emit()
        super().closeEvent(event)