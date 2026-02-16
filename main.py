import os
import sys
import ctypes

# PyQt6 imports
from PyQt6.QtCore import QObject, Qt, QEvent
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox, QPushButton, QComboBox, QGridLayout, QMainWindow, QTabWidget, QFrame, QLabel, QGroupBox, QScrollArea, QMenu, QRadioButton, QFileDialog
from PyQt6.QtGui import QIcon, QScreen, QAction, QColor, QPalette, QFont

from data.appdata import AppData
from modules.terminal import Terminal
from modules.base.customwidgets import TitleBar
from modules.base.iconbutton import IconButton
from modules.console import Console
from modules.plot_window import PlotWindow
from modules.surface_table import SurfaceTable
from modules.add_element_wizzard import AddElementDialog
from modules.base.customwidgets import PlaceHolderFrame


######################################################################################################################################################################################
# AUTHORSHIP METADATA   ##############################################################################################################################################################
######################################################################################################################################################################################
__author__ = "Alex Ackerman"
__company__ = "Avicena Tech"
__copyright__ = "Copyright 2024, Avicena Tech"
__credits__ = ["Alex Ackerman"]
__license__ = "GPL"
__version__ = "0.0.0"
__date__ = "September 16, 2024"
__maintainer__ = "Alex Ackerman"
__email__ = "alex.a@avicena.tech"
__status__ = "Development"

######################################################################################################################################################################################
#   RESOURCES   ######################################################################################################################################################################
######################################################################################################################################################################################
# Get the root directory
root_dir = os.path.dirname(os.path.abspath(__file__))

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

LOGO_ICON_PATH = os.path.join(resources_dir, "avicena_bordered.ico")

######################################################################################################################################################################################
#   Application   ####################################################################################################################################################################
######################################################################################################################################################################################

class App(QMainWindow):
    def __init__(self):
        """
        Initialize the main application window
        """
        super().__init__()
        self.company = AppData.company
        self.appname = AppData.appname                                                                                  # Application name
        self.version = AppData.version                                                                                  # Application version
        self.appid = self.company.lower() + "." + self.appname.replace(" ", "_").lower() + "." + self.version           # Company, product, version
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.appid)                                       # App icon in system tray
        
        # Get dimensions of primary screen
        primary_screen = QApplication.primaryScreen()
        screen_width = primary_screen.size().width()
        screen_height = primary_screen.size().height()
        # Set default screen dimensions based on primary screen resolution
        default_window_width = int(screen_width * 0.7)
        default_window_height = int(screen_height * 0.7)
        self.resize(default_window_width, default_window_height)
        # Set window title
        self.setWindowTitle(self.appname + " " + self.version)
        self.setWindowIcon(QIcon(LOGO_ICON_PATH))
        self.setStyleSheet(theme)
        
        # self.master_logger = Logger()                                                                                   # Master logging object
        # self.master_logger.set_level(self.master_logger.INFO)                                                           # Set default level to INFO - can be changed from gui tools > event log message level

        # Menu bar
        self.menu = self.menuBar()
        self.menu.setStyleSheet(theme)

        self.popup = None

        # Menu bar > file menu
        self.file_menu = self.menu.addMenu("&File")

        # new_icon = QIcon("code/resources/icons/new_icon.png")
        # self.new_action = QAction(new_icon, "&New DUT...", self)
        # self.new_action.setShortcut("Ctrl+N")
        # self.new_action.triggered.connect(self.new_dut)
        # self.file_menu.addAction(self.new_action)

        new_workspace_icon = QIcon("code/resources/icons/new_folder_icon.png")
        self.new_workspace_action = QAction(new_workspace_icon, "&New Workspace...", self)
        self.new_workspace_action.setShortcut("Ctrl+Alt+N")
        # self.new_workspace_action.triggered.connect(self.new_workspace)
        self.file_menu.addAction(self.new_workspace_action)

        self.file_menu.addSeparator()

        open_icon = QIcon("code/resources/icons/open_icon.png")
        self.open_action = QAction(open_icon, "&Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        # self.open_action.triggered.connect(self.open_file)
        self.file_menu.addAction(self.open_action)

        workspace_icon = QIcon("code/resources/icons/folder_icon.png")
        self.open_workspace_action = QAction(workspace_icon, "&Open Workspace...", self)
        self.open_workspace_action.setShortcut("Ctrl+Alt+O")
        # self.open_workspace_action.triggered.connect(self.open_workspace)
        self.file_menu.addAction(self.open_workspace_action)

        self.file_menu.addSeparator()

        save_icon = QIcon("code/resources/icons/save_icon.png")
        self.save_action = QAction(save_icon, "&Save...", self)
        self.save_action.setShortcut("Ctrl+S")
        # self.save_action.triggered.connect(self.save_file)
        self.file_menu.addAction(self.save_action)

        saveas_icon = QIcon("code/resources/icons/saveas_icon.png")
        self.save_as_action = QAction(saveas_icon, "&Save As...", self)
        self.save_as_action.setShortcut("Ctrl+Alt+S")
        # self.save_as_action.triggered.connect(self.save_file_as)
        self.file_menu.addAction(self.save_as_action)

        self.file_menu.addSeparator()

        self.add_element_action = QAction("Add Element...", self)
        self.add_element_action.triggered.connect(self.add_element)
        self.file_menu.addAction(self.add_element_action)

        self.add_element_from_file_action = QAction("Add Element from File...", self)
        self.add_element_from_file_action.triggered.connect(self.add_element_from_file)
        self.file_menu.addAction(self.add_element_from_file_action)

        self.file_menu.addSeparator()

        gear_icon = QIcon("code/resources/icons/gear_icon.png")
        self.preferences_action = QAction(gear_icon, "&Preferences...")
        # self.preferences_action.triggered.connect(self.preferences)
        self.file_menu.addAction(self.preferences_action)

        self.file_menu.addSeparator()

        exit_icon = QIcon("code/resources/icons/power_icon.png")
        self.exit_action = QAction(exit_icon, "&Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(QApplication.instance().quit)
        self.file_menu.addAction(self.exit_action)


# Menu bar > terminal menu
        self.terminal_menu = self.menu.addMenu("&Terminal")
        
        run_icon = QIcon("code/resources/icons/run_icon.png")
        self.run_current_action = QAction(run_icon, "&Run Active Script")
        # self.run_current_action.triggered.connect(self.run_current_script)
        self.terminal_menu.addAction(self.run_current_action)
        
        iterminal_icon = QIcon("code/resources/icons/run_icon.png")
        self.iterminal_action = QAction(run_icon, "&Launch Interactive Scripting Terminal")
        # self.iterminal_action.triggered.connect(self.launch_iterminal)
        self.terminal_menu.addAction(self.iterminal_action)
        
        self.terminal_menu.addSeparator()
        
        python_icon = QIcon("code/resources/icons/python_icon.png")
        self.python_terminal_action = QAction(python_icon, "&Launch iPython Terminal")
        # self.python_terminal_action.triggered.connect(self.launch_ipython)
        self.terminal_menu.addAction(self.python_terminal_action)
        
        cmd_icon = QIcon("code/resources/icons/cmd_icon.png")
        self.cmd_terminal_action = QAction(cmd_icon, "&Launch Command Prompt")
        # self.cmd_terminal_action.triggered.connect(self.launch_cmd)
        self.terminal_menu.addAction(self.cmd_terminal_action)
        
        self.terminal_menu.addSeparator()
        
        msg_level_icon = QIcon("code/resources/icons/message_icon.png")
        self.msg_level_menu = QMenu("Event Log message level", self)
        self.msg_level_menu.setIcon(msg_level_icon) 
        self.terminal_menu.addMenu(self.msg_level_menu)
        
        self.msg_debug_action = QAction("Debug")
        self.msg_debug_action.triggered.connect(self.set_logger_debug)
        self.msg_level_menu.addAction(self.msg_debug_action)
        
        self.msg_info_action = QAction("Info")
        self.msg_info_action.triggered.connect(self.set_logger_info)
        self.msg_level_menu.addAction(self.msg_info_action)
        
        self.msg_attention_action = QAction("Attention")
        self.msg_attention_action.triggered.connect(self.set_logger_attention)
        self.msg_level_menu.addAction(self.msg_attention_action)
        
        self.msg_warning_action = QAction("Warning")
        self.msg_warning_action.triggered.connect(self.set_logger_warning)
        self.msg_level_menu.addAction(self.msg_warning_action)

        self.main_widget = MainWidget(self) 
        self.setCentralWidget(self.main_widget)    

    def add_element(self):
        if self.popup is None or not self.popup.isVisible():
            # parent=None → top-level window
            self.popup = AddElementDialog(parent=None)
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    def add_element_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a file",
            "",
            "All Files (*);;Text Files (*.txt);;Python Files (*.py)",
        )
        if file_path:
            print("Selected:", file_path)
        

    def set_logger_debug(self):
        pass
        # self.master_logger.set_level(self.master_logger.DEBUG)
        # self.master_logger.debug("Event log set to level DEBUG")
        
    def set_logger_info(self):
        pass
        # self.master_logger.set_level(self.master_logger.INFO)
        # self.master_logger.info("Event log set to level INFO")
        
    def set_logger_attention(self):
        pass
        # self.master_logger.set_level(self.master_logger.ATTENTION)
        # self.master_logger.attention("Event log set to level ATTENTION")
        
    def set_logger_warning(self):
        pass
        # self.master_logger.set_level(self.master_logger.WARNING)
        # self.master_logger.warning("Event log set to level WARNING")

class MainWidget(QWidget):

    def __init__(self, parent, logger = None):

        super(MainWidget, self).__init__(parent)        

        # Configure logger to use parent logger if present or create new instance of a logger if not present
        if logger != None:
            self.logger = logger
        else:
            pass
            # self.logger = Logger()
        
        self.main_layout = QGridLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)                                                                             # left, top, right, bottom
        self.setLayout(self.main_layout)
    
        # Control Pane
        self.control_pane = self.ControlPane(self)
        self.main_layout.addWidget(self.control_pane, 0, 0, 2, 1)

        # Surface Table
        self.surface_table = SurfaceTable(self)
        self.main_layout.addWidget(self.surface_table, 0, 1, 1, 1)

        # Plot Window
        self.plot_window = PlotWindow(self)
        self.main_layout.addWidget(self.plot_window, 0, 2, 1, 2)

        # Terminal / Event Log
        self.terminal = self.TerminalPanel(self)                               
        self.main_layout.addWidget(self.terminal, 1, 1, 1, 3)

    
    class ControlPane(QFrame):
        
        def __init__(self, parent):

            super(MainWidget.ControlPane, self).__init__(parent)
            self.parent = parent
            # Configure logger to use parent logger if present or create new instance of a logger if not present

            self.setFixedWidth(400)
            self.setStyleSheet(theme)
            self.frame_layout = QGridLayout()
            self.frame_layout.setSpacing(0)
            self.frame_layout.setContentsMargins(0, 0, 0, 0)                                                                        # left, top, right, bottom
            self.setLayout(self.frame_layout)
            
            self.label = TitleBar("Master Controls")
            self.label.setMaximumHeight(20)
            self.frame_layout.addWidget(self.label, 0, 0)
            
            self.subframe = PlaceHolderFrame(self)
            self.subframe_layout = QGridLayout()
            self.subframe.setLayout(self.subframe_layout)
            self.frame_layout.addWidget(self.subframe, 1, 0)
            self.subframe_layout.setContentsMargins(0, 0, 0, 0)                                                                    # left, top, right, bottom

            self.camera_group = QGroupBox("Camera Connection")
            self.subframe_layout.addWidget(self.camera_group, 1, 0)
            self.camera_group_layout = QGridLayout()
            self.camera_group.setLayout(self.camera_group_layout)
            self.scan_cameras_button = QPushButton("Scan")
            self.camera_group_layout.addWidget(self.scan_cameras_button, 0, 0)
            
            self.connectiongroup = QGroupBox("Instrument Connections")
            self.connectiongroup.setFixedHeight(300)
            self.connectiongroup_layout = QGridLayout()
            self.connectiongroup.setLayout(self.connectiongroup_layout)
            self.subframe_layout.addWidget(self.connectiongroup, 2, 0)
            
            scan_icon = QIcon("code/resources/icons/search_icon.png")
            self.scan_button = QPushButton(" scan instruments")
            self.scan_button.setToolTip("Scan for usb-connected instruments")
            self.scan_button.setIcon(scan_icon)
            self.scan_button.setFixedHeight(25)
            self.scan_button.setFixedWidth(120)
            self.connectiongroup_layout.addWidget(self.scan_button, 0, 0, 1, 3, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            link_icon = QIcon("code/resources/icons/link_icon.png")
            self.bind_button = QPushButton(" bind")
            self.bind_button.setToolTip("Bind selected instruments to virtual instrument")
            self.bind_button.setIcon(link_icon)
            self.bind_button.setFixedWidth(80)
            self.bind_button.setFixedHeight(25)
            self.bind_button.setEnabled(False)
            self.connectiongroup_layout.addWidget(self.bind_button, 0, 3, 1, 1, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            
            connect_icon = QIcon("code/resources/icons/trident_icon.png")
            self.connect_button = QPushButton(" connect")
            self.connect_button.setToolTip("Connect to selected instruments and create virtual instrument instance")
            self.connect_button.setIcon(connect_icon)
            self.connect_button.setFixedHeight(25)
            self.connect_button.setFixedWidth(80)
            self.connect_button.setEnabled(False)
            self.connectiongroup_layout.addWidget(self.connect_button, 0, 4, 1, 1, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            

        class ControlTabHolder(QTabWidget):  
            def __init__(self, parent):
                """
                Initialize the tab holder
                Args:
                    parent (QWidget): The parent widget
                    logger (Logger, optional): The logger object. Defaults to None.
                """
                super(MainWidget.ControlPane.ControlTabHolder, self).__init__(parent)
                self.setStyleSheet(theme)
                self.frame_layout = QGridLayout()
                self.frame_layout.setContentsMargins(0, 0, 0, 0)                                                                # left, top, right, bottom
                self.setLayout(self.frame_layout)
 
    class TerminalPanel(QFrame):
        def __init__(self, parent):
            """
            Initialize the terminal panel
            Args:
                parent (QWidget): The parent widget
            """
            super(MainWidget.TerminalPanel, self).__init__(parent)
            self.setStyleSheet(theme)
            self.frame_layout = QGridLayout()
            self.frame_layout.setContentsMargins(0, 0, 0, 0)                                                                # left, top, right, bottom
            self.setLayout(self.frame_layout)
            self.setMaximumHeight(280)
            
            self.label = TitleBar("Terminal")
            self.label.setMaximumHeight(20)
            self.frame_layout.addWidget(self.label, 0, 0)
            
            self.export_button = IconButton("code/resources/icons/export_icon.png", self)
            self.export_button.clicked.connect(self.export_log)
            self.frame_layout.addWidget(self.export_button, 0, 0, Qt.AlignmentFlag.AlignRight)
            
            self.subframe = PlaceHolderFrame(self)
            self.subframe_layout = QGridLayout()
            self.subframe_layout.setContentsMargins(0, 0, 0, 0)                                                                # left, top, right, bottom
            self.subframe.setLayout(self.subframe_layout)
            self.frame_layout.addWidget(self.subframe, 1, 0)
            
            self.terminaltab = TabHolder(self)
            self.subframe_layout.addWidget(self.terminaltab, 0, 0)
            
            self.eventlog = Terminal(titlebar=False)
            self.terminaltab.addTab(self.eventlog, "Event Log")
            
            self.console = Console(self)
            self.terminaltab.addTab(self.console, "Console")
            
        def export_log(self):
            print("Exporting log...")
                
class TabHolder(QTabWidget):  
    def __init__(self, parent):
        """
        Initialize the tab holder
        Args:
            parent (QWidget): The parent widget
            logger (Logger, optional): The logger object. Defaults to None.
        """
        super(TabHolder, self).__init__(parent)
        self.setStyleSheet(theme)
        self.frame_layout = QGridLayout()
        self.frame_layout.setContentsMargins(0, 0, 0, 0)                                                                # left, top, right, bottom
        self.setLayout(self.frame_layout)

def main():
    app = QApplication(sys.argv)
    # Check the system's color scheme using QStyleHints
    if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
        # Dark mode is enabled, use the system's dark mode colors
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        # Set other palette colors as needed
        app.setPalette(palette)
    else:
        # Dark mode is disabled, use the default light mode colors
        app.setPalette(QPalette())
    window = App()
    window.show()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()