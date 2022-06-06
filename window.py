import binascii
import os
import shutil
import sys
import tempfile

from PyQt5 import QtCore, QtGui, QtWidgets

from bnd.bnd import BND
from data import *
from interface import main_window
from interface.tree_bundle_item import QTreeWidgetBundleItem


class Application(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        QtGui.QFontDatabase.addApplicationFont(resource_path("res/font.ttc").as_posix())
        super().__init__()

        # Init
        self.path = None
        self.setupUi(self)
        self.set_connections()
        self.current_extracted_items = []

        # Delete temp
        shutil.rmtree(
            Path(tempfile.gettempdir()).joinpath("bnd_editor/"), ignore_errors=True
        )
        self.setWindowIcon(QtGui.QIcon(resource_path("res/icon.png").as_posix()))

        # If opened via cmd with parameters
        if len(sys.argv) > 1:
            if sys.argv[1]:
                file = sys.argv[1]
                file = file.replace("\\", "/")
                self.load_bnd_file(file)

    def set_connections(self):
        """
        Set UI element connections
        """
        self.action_load.triggered.connect(self.select_bnd)
        self.action_save.triggered.connect(self.save_bnd_file)
        self.pb_open.clicked.connect(self.open_local_bnd)
        self.pb_back.clicked.connect(self.back_local_bnd)
        self.pb_extract_file.clicked.connect(self.extract_file)
        self.pb_replace_file.clicked.connect(self.replace_files)
        self.treeWidget.itemSelectionChanged.connect(self.selection_changed)
        self.treeWidget.itemChanged.connect(self.item_changed)

    def replace_files(self):
        """
        Triggered when the Replace Files button is pressed
        Opens a window to replace one or mutiple files
        """
        counter = 0
        for entry in self.get_selected_items():
            item = entry.bundleItem
            if not item.is_folder:
                parent = item.parent
                if parent:
                    input_file = QtWidgets.QFileDialog.getOpenFileName(
                        self,
                        f"Select file to replace file {counter + 1}: {item.get_local_path()}",
                    )
                    if input_file and len(input_file) > 0 and input_file[0]:
                        with open(input_file[0], "r+b") as f:
                            data = f.read()
                            item.update_data(data)
                    counter += 1
        if counter > 0:
            self.update_current_entry_data()

    def extract_file(self):
        """
        Triggered when the Extract Files button is pressed
        Extracts one or multiple selected files in the file's folder
        """
        for item in self.get_selected_items():
            self.extract_single_item(item.bundleItem)
        self.current_extracted_items.clear()

    def extract_single_item(self, bundle):
        """
        Extracts single bundle item, for folders
        it also extracts all its children items
        """
        if bundle.is_folder:
            for child_bundle in bundle.file_list:
                self.extract_single_item(child_bundle)
        else:
            internal_file_path = bundle.get_export_path(True)
            if internal_file_path not in self.current_extracted_items:
                complete_file_path = (
                    f"{self.output_path}/@{self.file_name}/{internal_file_path}"
                )
                os.makedirs(os.path.dirname(complete_file_path), exist_ok=True)
                file_data = bundle.to_bytes()
                with open(complete_file_path, "wb") as f:
                    f.write(file_data)
                self.current_extracted_items.append(complete_file_path)

    def open_local_bnd(self):
        """
        Triggered when the Open local BND file button is pressed
        Opens a BND inside the current BND
        """
        selected_item = self.get_selected_item()
        if selected_item:
            if (
                not selected_item.bundleItem.is_raw
                and not selected_item.bundleItem.is_folder
            ):
                self.bnd = selected_item.bundleItem
                self.reload_entries()

    def back_local_bnd(self):
        """
        Triggered when the Back to previous file button is pressed
        Returns to parent BND
        """
        self.bnd = self.bnd.get_parent()
        while self.bnd.is_folder:
            self.bnd = self.bnd.get_parent()
        self.reload_entries()

    def selection_changed(self):
        """
        Executed when the table selection is changed
        Sets the button states based on current item
        """
        selected_item = self.get_selected_item()
        if selected_item:
            self.update_current_entry_data()
        else:
            self.pb_open.setEnabled(False)

    def update_current_entry_data(self):
        """
        Updates current data
        """
        selected_item = self.get_selected_item()
        bundle = selected_item.bundleItem
        if not bundle.is_raw and not bundle.is_folder:
            self.pb_open.setEnabled(True)
        else:
            self.pb_open.setEnabled(False)

        # CRC text
        self.le_crc.setText((str(hex(bundle.get_crc()))).upper()[2:] + " ")
        self.le_crc.setToolTip(f"File: {bundle.get_local_path()}")

        # CRC tooltip
        to_bytes = bundle.to_bytes(ignore_gzip=True)
        self.le_size.setText(sizeof_fmt(len(to_bytes)) + " ")
        self.le_size.setToolTip(f"Size (ungzipped): {len(to_bytes)} bytes")

        # Unknown
        self.te_preview.setText("")

        # Hex view
        # TODO: Update on thread
        if len(to_bytes) > 0:
            string = str(binascii.hexlify(to_bytes[0:0x70]))[2:-1]

            string = " ".join(string[i : i + 2] for i in range(0, len(string), 2))
            string = "\n".join(string[i : i + 24] for i in range(0, len(string), 24))
            lines = string.splitlines()
            self.te_preview.append("\n")
            counter = 0
            for line in lines:
                line = "{0:#0{1}x}".format(counter * 8, 4) + " " + line
                self.te_preview.append(line)
                self.te_preview.setAlignment(QtCore.Qt.AlignLeft)
                counter += 1

    def get_selected_item(self):
        """
        Gets first selected item
        """
        selection = self.treeWidget.selectedItems()
        if (
            selection
            and len(selection) > 0
            and isinstance(selection[0], QTreeWidgetBundleItem)
        ):
            return selection[0]
        else:
            return None

    def get_selected_items(self):
        """
        Gets multiple selected items
        """
        return self.treeWidget.selectedItems()

    def select_bnd(self):
        """
        Opens select bnd
        """
        input_file = QtWidgets.QFileDialog.getOpenFileName(self, "Open")
        if input_file:
            if input_file[0] != "":
                self.load_bnd_file(input_file[0])

    def dragEnterEvent(self, event):
        """
        Drag enter event
        """
        event.accept()

    def dragMoveEvent(self, event):
        """
        Drag move event
        """
        event.accept()

    def dropEvent(self, event):
        """
        Load file from drag and drop event
        """
        file = event.mimeData()
        file = file.urls()
        file = file[0]
        file = str(file)
        file = file.replace(file[:27], "")
        file = file[:-2]
        self.load_bnd_file(file)

    def load_bnd_file(self, file):
        """
        Read BND file
        """
        with open(file, "r+b") as f:
            data = f.read()
            self.path = file
            self.bnd = BND(data)
            self.reload_entries()
            self.output_path = os.path.dirname(os.path.abspath(self.path))
            self.file_name = os.path.basename(os.path.abspath(self.path))

    def save_bnd_file(self):
        """
        Saves BND file
        """
        if self.path and self.bnd:
            with open(self.path + ".out", "wb") as f:
                f.write(self.bnd.get_root_parent().to_bytes())

    def reload_entries(self):
        """
        Reload all entries from BND
        Enables all the buttons
        """
        # Clean tree widget
        self.treeWidget.clear()

        # Add entries to tree widget
        for entry in self.bnd.file_list:
            widget = QTreeWidgetBundleItem(entry, self.style())
            self.treeWidget.addTopLevelItem(widget)

        # Enable buttons
        self.pb_back.setEnabled(self.bnd.has_parent())
        # self.pb_add_file.setEnabled(True)
        # self.pb_add_folder.setEnabled(True)
        # self.pb_delete_file.setEnabled(True)
        self.pb_extract_file.setEnabled(True)
        self.pb_replace_file.setEnabled(True)
        # self.pb_movedown.setEnabled(True)
        # self.pb_moveup.setEnabled(True)

        # Change title
        self.treeWidget.setHeaderLabel(self.bnd.get_full_path())

    def item_changed(self, item):
        """
        Triggered when an item is modified
        """
        if isinstance(item, QTreeWidgetBundleItem):
            self.check_item_filename(item)

    def check_item_filename(self, item: QTreeWidgetBundleItem):
        """
        Check if the item filename is correct according to the file type
        """
        name = item.text(0)
        if item.get_is_folder():
            if not name.endswith("/"):
                name += "/"
        elif item.get_is_single_file():
            if name != "[[ GZIPPED FILE ]]":
                name = "[[ GZIPPED FILE ]]"
        else:
            self.set_item_name(item, name)

    def set_item_name(self, item: QTreeWidgetBundleItem, text: str):
        """
        Updates item name, reloads entry data if the
        item is currently being selected
        """
        item.setText(0, text)
        item.bundleItem.set_name(text)
        if item == self.get_selected_item():
            self.update_current_entry_data()
