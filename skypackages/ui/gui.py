from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication
from pathlib import Path

from skypackages.manager import SkybuildPackageManager
from skypackages.nexus import NexusMod

from pynxm import Nexus

UI_FILE = Path(__file__).parent / 'skypackages.ui'


class SkyPackagesGui(QtWidgets.QMainWindow):
    def __init__(self, project_folder, nexus_api_key):
        self.project_folder = Path(project_folder)
        self.nexus_api_key = nexus_api_key

        self.nexus_api = None
        self.refresh_nexus_api()

        self.manager = None
        self.refresh_manager()

        self.current_nexus_mod = None

        self.app = QApplication([])
        self.app.setStyle('Fusion')
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.app.setPalette(dark_palette)
        self.app.setStyleSheet('''
            QToolTip {
                color: #ffffff;
                background-color: #2a82da;
                border: 1px solid white;
            }
        ''')
        super().__init__()
        uic.loadUi(UI_FILE, self)

        # load the gui
        self.show()
        self.ensure_gui_elements()
        self.setup_signal_handlers()

    @property
    def current_nexus_url(self):
        return self.NexusUrl.text()

    def ensure_gui_elements(self):
        expected = [
            'PackagesList',
            'TarballsList',
            'SourcesList',
            'NexusUrl',
            'NexusDescription',
            'NexusAvailableFiles'
        ]
        for element in expected:
            assert hasattr(self, element), f'cannot access element {element}'

    def setup_signal_handlers(self):
        self.NexusUrl.returnPressed.connect(self.load_nexus_mod_from_url)

    def render_nexus_mod(self):
        self.NexusUrl.setText(self.current_nexus_mod.url)
        self.NexusTitle.setText(self.current_nexus_mod.name)
        self.NexusSummary.setText(self.current_nexus_mod.summary)
        self.NexusDescription.setText(self.current_nexus_mod.description_html)

    def load_nexus_mod_from_url(self):
        self.current_nexus_mod = NexusMod.from_url(
            self.nexus_api, self.current_nexus_url)
        self.render_nexus_mod()

    def refresh_nexus_api(self):
        self.nexus_api = Nexus(self.nexus_api_key)

    def refresh_manager(self):
        self.manager = SkybuildPackageManager(self.project_folder)

    def run(self):
        print('Running App')
        self.app.exec_()
