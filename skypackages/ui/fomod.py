from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QGroupBox,
    QCheckBox,
    QRadioButton,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QLabel
)
import os
from pathlib import Path

import pyfomod
from pyfomod import GroupType

from skypackages.utils import yaml_dump

UI_FILE = Path(__file__).parent / 'fomod.ui'


class FomodOptionCheckBox(QCheckBox):
    mouseEntered = pyqtSignal(QCheckBox)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._data = None

    def data(self):
        return self._data

    def setData(self, value):
        self._data = value

    def enterEvent(self, event):
        self.mouseEntered.emit(self)


class FomodOptionRadioButton(QRadioButton):
    mouseEntered = pyqtSignal(QCheckBox)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

    def data(self):
        return self._data

    def setData(self, value):
        self._data = value

    def enterEvent(self, event):
        self.mouseEntered.emit(self)


class FomodOptionPhoto(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._photo = None

    def photo(self):
        return self._photo

    def setPhoto(self, path):
        self._photo = QPixmap(path)
        self.setPixmap(self._photo.scaled(
            self.width(), self.height(), Qt.KeepAspectRatio))

    def resizeEvent(self, event):
        if self.pixmap():
            self.setPixmap(self._photo.scaled(
                self.width(), self.height(), Qt.KeepAspectRatio))


class FomodOptionsPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None

    def data(self):
        return self._data

    def setData(self, data):
        self._data = data


class FomodOptionsGroup(QGroupBox):
    mouseEnteredOption = pyqtSignal(QCheckBox)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._group = None
        self._options = []
        self._option_items = []

    def group(self):
        return self._group

    def setGroup(self, group):
        self._group = group
        self._options = []
        self._option_items = []

        self.setTitle(group.name)
        self.setLayout(QVBoxLayout())
        for option in group:
            if group.type == GroupType.EXACTLYONE:
                option_widget = FomodOptionRadioButton(self)
                option_widget.toggled.connect(self.stateChanged)
            else:
                option_widget = FomodOptionCheckBox(self)
                option_widget.stateChanged.connect(self.stateChanged)

            option_widget.setText(option.name)
            option_widget.setData(option)
            option_widget.mouseEntered.connect(self.optionEntered)

            self.layout().addWidget(option_widget)
            self._options.append(option)
            self._option_items.append(option_widget)

        if group.type == GroupType.EXACTLYONE and self.firstOptionItem():
            self.firstOptionItem().setChecked(True)

        self.stateChanged()

    def selectFrom(self, options):
        for item in self._option_items:
            stored_option = item.data()
            for option in options:
                if option is stored_option._object:
                    item.setChecked(True)
                    break
            else:
                item.setChecked(False)

    def optionItems(self):
        return self._option_items

    def firstOptionItem(self):
        if self._option_items:
            return self._option_items[0]

    def optionEntered(self, option):
        self.mouseEnteredOption.emit(option)

    def stateChanged(self):
        self.setStyleSheet(
            '' if self.validate() else 'background-color: red; ')

    def validate(self):
        if self._group.type == GroupType.ALL and not all(
                item.isChecked() for item in self._option_items):
            print('not all are checked')
            return False
        elif self._group.type == GroupType.ATLEASTONE and not any(
                item.isChecked() for item in self._option_items):
            print('not at least one are checked')
            return False
        elif self._group.type == GroupType.ATMOSTONE and len([
                item for item in self._option_items if item.isChecked()]) > 1:
            print('not at most one are checked')
            return False
        elif self._group.type == GroupType.EXACTLYONE and len([
                item for item in self._option_items if item.isChecked()]) != 1:
            print('not exactly one are checked')
            return False
        else:
            return True


class FomodInstallerGui(QtWidgets.QMainWindow):
    def __init__(self, fomod_root):
        self.root = Path(fomod_root)
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
            'FomodPhotoVSplitter',
            'FomodInstructions',
            'FomodOptionsGroup',
            'FomodBackButton',
            'FomodNextButton'
        ]
        for element in expected:
            assert hasattr(self, element), f'cannot access element {element}'

    def apply_initial_sizes(self):
        # width = QtWidgets.qApp.desktop().availableGeometry(self).width()
        height = QtWidgets.qApp.desktop().availableGeometry(self).height()
        self.FomodPhotoVSplitter.setSizes([height / 2, height / 2])

    def setup_signal_handlers(self):
        self.FomodNextButton.clicked.connect(self.next_page)
        self.FomodBackButton.clicked.connect(self.previous_page)

    def initial_render(self):
        self.FomodNameLabel.setText(self.installer.root.name)
        self.FomodMetaLabel.setText(
            f'Author: {self.installer.root.author}\n'
            f'Version: {self.installer.root.version}\n'
            f'Website: {self.installer.root.website}'
        )
        self.next_page()

    def previous_page(self):
        previous_data = self.installer.previous()
        if previous_data:
            page, selected = previous_data
            self.render_page(page, selected=selected)

        self.render_files()
        self.render_choices()

    def next_page(self):
        selected = []
        if self.FomodOptionsGroup.data():
            selected = [
                option_item.data()
                for option_item in self.FomodOptionsGroup.data()
                if option_item.isChecked()]

        page = self.installer.next(selected)
        if page:
            self.render_page(page)
        else:
            print('done!')

        self.render_files()
        self.render_choices()

    def render_page(self, page, selected=None):
        selected = selected or []

        old_layout = self.FomodOptionsGroup.layout()
        if old_layout:
            QWidget().setLayout(old_layout)

        self.FomodOptionsGroup.setTitle(page.name)
        self.FomodOptionsGroup.setData([])
        groups_layout = QVBoxLayout()
        for i, group in enumerate(page):
            groupbox = FomodOptionsGroup(self.FomodOptionsGroup)
            groupbox.setGroup(group)
            if i == 0 and groupbox.firstOptionItem():
                self.render_option_hover(groupbox.firstOptionItem())
            groupbox.selectFrom(selected)
            groupbox.mouseEnteredOption.connect(self.render_option_hover)

            groups_layout.addWidget(groupbox)
            self.FomodOptionsGroup.data().extend(groupbox.optionItems())

        v_spacer = QSpacerItem(
            10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        groups_layout.addItem(v_spacer)
        self.FomodOptionsGroup.setLayout(groups_layout)

    def render_files(self):
        lines = []
        for src, dest in self.installer.files().items():
            lines.append(f'{src}')
            lines.append(f'    -> {dest}')

        self.SelectedFilesText.setText(os.linesep.join(lines))
        scroll_bar = self.SelectedFilesText.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def render_choices(self):
        choices = {}
        for page, selected_options in self.installer._previous_pages.items():
            for group in page:
                for option in group:
                    for selected in selected_options:
                        if option is selected:
                            (choices
                                .setdefault('fomod', {})
                                .setdefault('inputs', {})
                                .setdefault(page.name, {})
                                .setdefault(group.name, [])
                                .append(option.name))
                            break
        self.ChoicesText.setText(yaml_dump(choices))

    def render_option_hover(self, option_item):
        option = option_item.data()

        pixmap = QPixmap(str(self.root / option.image))
        self.FomodPhotoLabel.setPhoto(pixmap)
        self.FomodPhotoLabel.setText('')

        self.FomodInstructions.setText(option.description)

    def run(self):
        print('Running App')
        self.app.exec_()
