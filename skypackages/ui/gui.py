from enum import Enum
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QCursor
from PyQt5.QtWidgets import (
    QApplication,
    QListWidgetItem,
    QTableWidgetItem,
    QMenu,
    QInputDialog,
    QLineEdit)
from pathlib import Path

from skypackages.manager import SkybuildPackageManager
from skypackages.nexus import NexusMod

from pynxm import Nexus

UI_FILE = Path(__file__).parent / 'skypackages.ui'


class NexusDownloadPostActions(Enum):
    add_as_new = 0
    add_into_selected = 1
    diff_with_selected = 2


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
            'AliasesList',
            'BlobsList',
            'SourcesList',
            'NexusUrl',
            'NexusDescription',
            'NexusAvailableFiles'
        ]
        for element in expected:
            assert hasattr(self, element), f'cannot access element {element}'

    def setup_signal_handlers(self):
        self.NexusUrl.returnPressed.connect(self.load_nexus_mod_from_url)
        self.NexusAvailableFiles.setContextMenuPolicy(Qt.CustomContextMenu)
        self.NexusAvailableFiles.customContextMenuRequested.connect(
            self.nexus_file_context_menu)

    def render_aliases(self):
        self.AliasesList.clear()
        for alias, blob_ids in sorted(self.manager.aliases.data.items()):
            list_item = QListWidgetItem()
            list_item.setText(alias)
            list_item.setData(Qt.UserRole, blob_ids)
            self.AliasesList.addItem(list_item)

    def render_nexus_mod(self):
        self.NexusUrl.setText(self.current_nexus_mod.url)
        self.NexusTitle.setText(self.current_nexus_mod.name)
        self.NexusSummary.setText(self.current_nexus_mod.summary)
        self.NexusDescription.setText(self.current_nexus_mod.description_html)

    def render_nexus_files(self, file_list):
        # sort the filelist
        file_list = sorted(
            file_list,
            key=lambda item: (
                '' if item.category_name == 'MAIN' else item.category_name,
                0 if item.is_primary else 1,
                item.name
            ))

        # clear the table
        self.NexusAvailableFiles.clear()

        # render the table
        headers = [
            'category_name',
            'file_id',
            'name',
            'version',
            'is_primary',
            'size',
            'description',
            'file_name',
        ]

        self.NexusAvailableFiles.setColumnCount(len(headers))
        self.NexusAvailableFiles.setRowCount(len(file_list))
        self.NexusAvailableFiles.setHorizontalHeaderLabels(headers)

        for i, file_ in enumerate(file_list):
            for j, header in enumerate(headers):
                item = QTableWidgetItem()
                item.setText(f'{getattr(file_, header)}')
                item.setData(Qt.UserRole, file_)
                self.NexusAvailableFiles.setItem(i, j, item)

        self.NexusAvailableFiles.resizeColumnsToContents()

    def nexus_file_context_menu(self, event):
        clicked_item = self.NexusAvailableFiles.itemAt(event)
        if clicked_item:
            nexus_file = clicked_item.data(Qt.UserRole)
            menu = QMenu(self.NexusAvailableFiles)

            action_add_as_new = menu.addAction(
                'Download and Add as New Package')
            action_add_as_new.triggered.connect(
                lambda: self.nexus_download(
                    nexus_file,
                    post_action=NexusDownloadPostActions.add_as_new))

            action_add_into_selected = menu.addAction(
                'Download and Add into Selected Package')
            action_add_into_selected.triggered.connect(
                lambda: self.nexus_download(
                    nexus_file,
                    post_action=NexusDownloadPostActions.add_into_selected))

            action_diff_with_selected = menu.addAction(
                'Download and Diff with Selected Package')
            action_diff_with_selected.triggered.connect(
                lambda: self.nexus_download(
                    nexus_file,
                    post_action=NexusDownloadPostActions.diff_with_selected))

            menu.popup(QCursor.pos())

    def nexus_download(self, nexus_file, post_action=None):
        downloaded = nexus_file.download_into(self.manager.paths.download_cache)
        print(f'downloaded: {downloaded}')

        if post_action is NexusDownloadPostActions.add_as_new:
            alias = ''
            while not self.validate_alias(alias):
                alias, ok_pressed = QInputDialog.getText(
                    None,
                    'New Package Name',
                    'New Package Name',
                    QLineEdit.Normal,
                    '')
            self.manager.add_source(
                alias, nexus_file.package_source, downloaded)
            self.render_aliases()

    def validate_alias(self, alias):
        if not alias:
            print('alias must not be empty')
            return False
        if ' ' in alias:
            print('no spaces allowed in an alias name')
            return False
        return True

    def load_nexus_mod_from_url(self):
        self.current_nexus_mod = NexusMod.from_url(
            self.nexus_api, self.current_nexus_url)
        self.render_nexus_mod()
        self.render_nexus_files(self.current_nexus_mod.file_list)

    def refresh_nexus_api(self):
        self.nexus_api = Nexus(self.nexus_api_key)

    def refresh_manager(self):
        self.manager = SkybuildPackageManager(self.project_folder)

    def run(self):
        print('Running App')
        self.app.exec_()
