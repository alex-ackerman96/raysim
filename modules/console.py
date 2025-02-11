import sys
from PyQt6.QtGui import QColor, QPainter, QTextFormat,QTextCharFormat, QSyntaxHighlighter, QTextCursor, QFontMetrics
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget, QFrame, QGridLayout
from PyQt6.QtCore import QRegularExpression, Qt, QRect

# with open('main//resources//dark.qss', 'r') as f:
#     darktheme = f.read()

# theme = darktheme

def hex_to_qcolor(hex_string):
    # Remove '#' if present
    hex_string = hex_string.lstrip('#')
    return QColor('#' + hex_string)

class KeywordHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Keywords with hexadecimal colors
        keyword_colors = {
            "device":"#6CC8B0",
            "instrument":"#6CC8B0",
            "import":"#B488C0",
            "addr":"#81C449",
            "val":"#81C449",
            "start":"#0032FF",
            "set":"",
            "stop":"",
            "run":"",
            "for":"",
            "while":"",
            "halt":"#6CC8B0",
            "write":"#6CC8B0",
            "read":"#6CC8B0",
        }

        # Add rules for keywords
        for keyword, color in keyword_colors.items():
            keyword_format = QTextCharFormat()
            if color:
                keyword_format.setForeground(QColor(color))
            self.highlighting_rules.append((QRegularExpression(r'\b' + keyword + r'\b'), keyword_format))

        # Rule for text in double quotes
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#48C300"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), quote_format))

        # Rule for hexadecimal numbers
        int_format = QTextCharFormat()
        int_format.setForeground(QColor("#FF0000"))
        self.highlighting_rules.append((QRegularExpression(r'\b0x[0-9A-Fa-f]+'), int_format))

        # Rule for words following specific keywords
        follow_keyword_format = QTextCharFormat()
        follow_keyword_format.setForeground(QColor("#FF8C00"))  # Dark orange color
        follow_keyword_format.setFontItalic(True)

        follow_keywords = ["device", "instrument"]
        for word in follow_keywords:
            pattern = QRegularExpression(r'\b' + word + r'\s+(\w+)')
            self.highlighting_rules.append((pattern, follow_keyword_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            matches = expression.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                if pattern.pattern().endswith(r'\s+(\w+)'):
                    # This is a "follow keyword" rule
                    start = match.capturedStart(1)
                    length = match.capturedLength(1)
                else:
                    start = match.capturedStart()
                    length = match.capturedLength()
                self.setFormat(start, length, format)

class CodeTextEdit(QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)

        self.document().setDocumentMargin(0)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.highlighted_line = 0
        self.highlight_color = QColor("#202d3f52")
        self.cursorPositionChanged.connect(self.update_highlight)

    def update_highlight(self):
        self.highlighted_line = self.textCursor().blockNumber()
        self.viewport().update()

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        
        # Get the cursor for the highlighted line
        cursor = QTextCursor(self.document().findBlockByNumber(self.highlighted_line))
        
        # Get the rectangle for the start of the line
        start_rect = self.cursorRect(cursor)
        
        # Move cursor to end of line and get that rectangle
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        end_rect = self.cursorRect(cursor)
        
        # Create a rectangle that spans the full width
        highlight_rect = QRect(
            0,  # Start from the left edge
            start_rect.top(),
            self.viewport().width(),  # Span the full width
            start_rect.height()
        )
        
        painter.fillRect(highlight_rect, self.highlight_color)
        painter.end()
        
        super().paintEvent(event)

class Console(QFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.frame_layout = QGridLayout()
        self.setLayout(self.frame_layout)

        self.text_edit = CodeTextEdit(self)
        self.highlighter = KeywordHighlighter(self.text_edit.document())
        self.frame_layout.addWidget(self.text_edit, 0, 0)
