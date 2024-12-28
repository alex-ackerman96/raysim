import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

class SpreadsheetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Spreadsheet")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_table()

    def create_table(self):
        self.table = QTableWidget()
        self.table.setRowCount(10)
        self.table.setColumnCount(5)
        
        # Set headers
        headers = ["A", "B", "C", "D", "E"]
        self.table.setHorizontalHeaderLabels(headers)

        # Populate the table with empty items
        for row in range(10):
            for col in range(5):
                item = QTableWidgetItem("")
                self.table.setItem(row, col, item)

        self.layout.addWidget(self.table)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpreadsheetApp()
    window.show()
    sys.exit(app.exec())
