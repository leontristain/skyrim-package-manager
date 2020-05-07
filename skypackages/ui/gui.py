from enum import Enum
import fnmatch
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
from skypackages.sources import NexusPackageSource

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
        self.current_selected_alias = None
        self.current_selected_blob = None
        self.current_selected_source = None

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

    @property
    def current_nexus_url(self):
        return self.NexusUrl.text()

    def ensure_gui_elements(self):
        expected = [
            'AliasesFilter',
            'AliasesList',
            'BlobsList',
            'SourcesList',
            'NexusUrl',
            'NexusDescription',
            'NexusAvailableFiles',
            'PackagesAndSourcesHSplitter',
            'LeftPaneVSplitter'
        ]
        for element in expected:
            assert hasattr(self, element), f'cannot access element {element}'

    def apply_initial_sizes(self):
        width = QtWidgets.qApp.desktop().availableGeometry(self).width()
        height = QtWidgets.qApp.desktop().availableGeometry(self).height()

        self.PackagesAndSourcesHSplitter.setSizes(
            [width * 1 / 4, width * 3 / 4])

        self.LeftPaneVSplitter.setSizes(
            [height * 2 / 3, height * 1 / 6, height * 1 / 6])

    def setup_signal_handlers(self):
        self.NexusUrl.returnPressed.connect(self.load_nexus_mod_from_url)
        self.NexusAvailableFiles.setContextMenuPolicy(Qt.CustomContextMenu)
        self.NexusAvailableFiles.customContextMenuRequested.connect(
            self.nexus_file_context_menu)

        self.AliasesFilter.textEdited.connect(
            self.aliases_filter_changed)

        self.AliasesList.itemSelectionChanged.connect(
            self.alias_selection_changed)

        self.AliasesList.itemChanged.connect(
            self.alias_content_changed)

        self.BlobsList.itemSelectionChanged.connect(
            self.blob_selection_changed)

        self.SourcesList.itemSelectionChanged.connect(
            self.source_selection_changed)

        self.SourcesList.itemDoubleClicked.connect(
            self.source_activated)

    def aliases_filter_changed(self, text):
        self.render_aliases()

    def source_activated(self, item):
        source = item.data(Qt.UserRole)
        if isinstance(source, NexusPackageSource):
            self.NexusUrl.setText(source.url)
            self.load_nexus_mod_from_url()

    def alias_selection_changed(self):
        self.current_selected_alias = self.AliasesList.currentItem().text()
        self.render_blobs()

    def alias_content_changed(self, alias_item):
        new_alias = alias_item.text()
        old_alias = alias_item.data(Qt.UserRole)['alias']
        if old_alias == new_alias:
            return
        try:
            self.manager.aliases.rename(old_alias, new_alias)
        except Exception as e:
            alias_item.setText(old_alias)
            print(f'Cannot rename alias: got exception with message: {e}')
        else:
            self.current_selected_alias = new_alias
            self.render_aliases()

    def blob_selection_changed(self):
        self.current_selected_blob = self.BlobsList.currentItem().text()
        self.render_sources()

    def source_selection_changed(self):
        self.current_selected_source = self.SourcesList.currentItem().text()

    def initial_render(self):
        self.render_aliases()

    def render_aliases(self):
        self.AliasesList.clear()
        aliases = self.manager.aliases.data
        pattern = self.AliasesFilter.text() + '*'
        for alias, blob_ids in sorted(aliases.items()):
            if pattern and not fnmatch.fnmatch(alias, pattern):
                continue
            list_item = QListWidgetItem()
            list_item.setText(alias)
            list_item.setData(
                Qt.UserRole, {'alias': alias, 'blob_ids': blob_ids})
            list_item.setFlags(list_item.flags() | Qt.ItemIsEditable)
            self.AliasesList.addItem(list_item)
            if self.current_selected_alias == alias:
                self.AliasesList.setCurrentItem(list_item)
        if aliases and not self.AliasesList.currentItem():
            self.AliasesList.setCurrentRow(0)
        if not self.AliasesList.currentItem():
            self.current_selected_alias = None

    def render_blobs(self):
        self.BlobsList.clear()
        alias_item = self.AliasesList.currentItem()
        if alias_item:
            blob_ids = alias_item.data(Qt.UserRole)['blob_ids']
            for blob_id in blob_ids:
                list_item = QListWidgetItem()
                list_item.setText(blob_id)
                self.BlobsList.addItem(list_item)
                if self.current_selected_blob == blob_id:
                    self.BlobsList.setCurrentItem(list_item)
            if blob_ids and not self.BlobsList.currentItem():
                self.BlobsList.setCurrentRow(0)
            if not self.BlobsList.currentItem():
                self.current_selected_blob = None

    def render_sources(self):
        self.SourcesList.clear()
        blob_item = self.BlobsList.currentItem()
        if blob_item:
            blob_id = blob_item.text()
            sources = self.manager.sources.fetch(blob_id)
            for source in sources:
                list_item = QListWidgetItem()
                list_item.setText(f'{source}')
                list_item.setData(Qt.UserRole, source)
                self.SourcesList.addItem(list_item)
                if self.current_selected_source == source:
                    self.SourcesList.setCurrentItem(list_item)
            if sources and not self.SourcesList.currentItem():
                self.SourcesList.setCurrentRow(0)
            if not self.SourcesList.currentItem():
                self.current_selected_source = None

    def render_nexus_mod(self):
        self.NexusUrl.setText(self.current_nexus_mod.url)
        self.NexusTitle.setText(
            f'<a href="{self.current_nexus_mod.url}">'
            f'{self.current_nexus_mod.name}'
            f'</a>')
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

        selected_source = None
        selected_source_item = self.SourcesList.currentItem()
        if selected_source_item:
            selected_source = selected_source_item.data(Qt.UserRole)

        for i, file_ in enumerate(file_list):
            for j, header in enumerate(headers):
                item = QTableWidgetItem()
                item.setText(f'{getattr(file_, header)}')
                item.setData(Qt.UserRole, file_)
                self.NexusAvailableFiles.setItem(i, j, item)
            if file_.file_id == selected_source.file_id:
                self.NexusAvailableFiles.setCurrentCell(i, 0)

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
