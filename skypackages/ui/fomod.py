from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication
from pathlib import Path

import pyfomod

UI_FILE = Path(__file__).parent / 'fomod.ui'


class FomodInstallerGui(QtWidgets.QMainWindow):
    def __init__(self, fomod_root):
        self.root = fomod_root
        self.installer = pyfomod.Installer(self.root)

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
        self.apply_initial_sizes()
        self.setup_signal_handlers()
        self.initial_render()

    def ensure_gui_elements(self):
        expected = [
            'DataTabs',
            'SelectedFilesTab',
            'SelectedFilesText',
            'ChoicesTab',
            'ChoicesText',
            'FomodWizardGroup',
            'FomodNameLabel',
            'FomodMetaLabel',
            'FomodPhotoLabel',
            'FomodInstructions',
            'FomodOptionsGroup',
            'FomodBackButton',
            'FomodNextButton'
        ]
        for element in expected:
            assert hasattr(self, element), f'cannot access element {element}'

    def apply_initial_sizes(self):
        pass

    def setup_signal_handlers(self):
        self.FomodNextButton.clicked.connect(self.next_page)

    def initial_render(self):
        self.FomodNameLabel.setText(self.installer.root.name)
        self.FomodMetaLabel.setText(
            f'Author: {self.installer.root.author}\n'
            f'Version: {self.installer.root.version}\n'
            f'Website: {self.installer.root.website}'
        )

    def next_page(self):
        page = self.installer.next()
        print(f'{page}')
        for group in page:
            print(f'  {group}')
            for option in group:
                print(f'    {option}')
        print('next page')
        print(page)
        print(self.installer.root.name)
        print(self.installer.root.author)
        print(self.installer.root.version)
        print(self.installer.root.description)
        print(self.installer.root.website)
        print(page.name)

    def run(self):
        print('Running App')
        self.app.exec_()
