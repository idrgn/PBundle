import binascii
import os
import shutil
import sys
import tempfile
import threading
import time

import sip
from PyQt5 import QtCore, QtGui, QtWidgets

from bnd.bnd import BND
from const import EMPTY_BND_FILE, GZIPPED_FILE_NAME
from data import *
from interface import main_window
from interface.tree_widget_item_bundle import QTreeWidgetItemBundle


class Application(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        QtGui.QFontDatabase.addApplicationFont(resource_path("res/font.ttf").as_posix())
        super().__init__()

        # Init
        self.bnd = None
        self.path = None
        self.setupUi(self)
        self.set_connections()
        self.current_copied_items = []
        self.current_extracted_items = []
        self.treeWidget.setStyle(self.style())

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
        self.action_load_datams.triggered.connect(self.select_bnd_datams)
        self.action_save.triggered.connect(self.save_bnd_file)
        self.pb_open.clicked.connect(self.open_local_bnd)
        self.pb_back.clicked.connect(self.back_local_bnd)
        self.pb_extract_file.clicked.connect(self.extract_files)
        self.pb_replace_file.clicked.connect(self.replace_files)
        self.pb_delete_file.clicked.connect(self.delete_files)
        self.pb_add_folder.clicked.connect(self.add_folder)
        self.pb_add_file.clicked.connect(self.add_file)
        self.pb_add_bnd.clicked.connect(self.add_bnd)
        self.pb_copy.clicked.connect(self.copy_selection)
        self.pb_paste.clicked.connect(self.paste_selection)
        self.treeWidget.itemSelectionChanged.connect(self.selection_changed)
        self.treeWidget.itemChanged.connect(self.item_changed)

    def copy_selection(self):
        """
        Copies current selection
        """
        selection = self.treeWidget.selectedItems()

        if (
            selection
            and len(selection) > 0
            and isinstance(selection[0], QTreeWidgetItemBundle)
        ):
            self.current_copied_items.clear()
            for item in selection:
                self.current_copied_items.append(item.bundle)
            self.pb_paste.setEnabled(True)

    def move_item(self, displacement):
        """
        Moves selected item up or down based on displacement value
        TODO: Finish
        """
        selected = self.get_selected_item()
        if selected.bundle and selected.parent and selected.bundle.parent:
            interface_item_index = self.treeWidget.currentIndex().row()

            bundle_item_parent = selected.bundle.parent
            bundle_item_index = bundle_item_parent.file_list.index(selected.bundle)
            bundle_item_parent.file_list.pop(bundle_item_index)

            new_index = bundle_item_index + displacement

            # Index limits
            if new_index > len(bundle_item_parent.file_list):
                new_index = len(bundle_item_parent.file_list) + 1
            elif new_index < 0:
                new_index = 0

            bundle_item_parent.add_to_file_list(
                selected.bundle, True, False, False, new_index
            )

            # selected.getParent().removeChild(selected)
            # selected.getParent().insertTopLevelItem(bundle_item_index - 1, selected)

    def paste_selection(self):
        """
        Pastes current copied items to the current selected file
        """
        if self.current_copied_items and len(self.current_copied_items) > 0:
            for item in self.current_copied_items:
                new_file = item.copy()
                new_file.parent = None
                self.add_to_selected_item(new_file)

    def add_folder(self):
        """
        Adds a new folder to the current selected file
        """
        self.add_to_selected_item(BND(name="new folder/", is_folder=True))

    def add_file(self):
        """
        Adds one or multiple files to the current selected file
        """
        input_files = QtWidgets.QFileDialog.getOpenFileNames(self, "Open")
        if input_files and input_files[0] and input_files[0][0] != "":
            for path in input_files[0]:
                with open(path, "r+b") as f:
                    self.add_to_selected_item(BND(f.read(), os.path.basename(path)))

    def add_bnd(self):
        """
        Adds a new empty BND file to the current selected file
        """
        new_bnd = BND(EMPTY_BND_FILE, "empty_bundle.bnd")
        self.add_to_selected_item(new_bnd)

    def add_to_selected_item(self, bnd):
        """
        Adds a BND file to the current selected item
        """
        selected = self.get_selected_item()
        new_widget = QTreeWidgetItemBundle(bnd, self.style())

        # If a file is not selected, add to root
        if not selected:
            self.bnd.add_to_file_list(bnd, True, True)
            self.treeWidget.addChildBundle(new_widget)
        else:
            # If a file is selected and it's a folder, add to it
            # If it is a file, get the parent folder and add to it
            if selected.bundle.is_folder:
                selected.bundle.add_to_file_list(bnd, True, True)
                selected.addChildBundle(bnd)
            else:
                # If the file has a parent object with a bundle, add to it
                # If not, add to root
                if selected.getParent() and selected.getParent().bundle:
                    selected.getParent().bundle.add_to_file_list(bnd, True, True)
                    selected.getParent().addChildBundle(bnd)
                else:
                    self.bnd.add_to_file_list(bnd, True, True)
                    self.treeWidget.addChildBundle(new_widget)

    def delete_files(self):
        """
        Triggered when the Delete Files button is pressed
        Deletes one or multiple files or folders
        """
        for entry in self.get_selected_items():
            if entry:
                self.delete_single_item(entry)
        self.update_current_entry_data()

    def delete_single_item(self, item):
        """
        Deletes single item
        """
        item.bundle.delete()
        item.bundle = None
        entry_parent = item.getParent()
        if entry_parent:
            try:
                entry_parent.removeChild(item)
            except Exception:
                sip.delete(item)
        else:
            sip.delete(item)

    def replace_files(self):
        """
        Triggered when the Replace Files button is pressed
        Opens a window to replace one or mutiple files
        """
        counter = 0
        for entry in self.get_selected_items():
            item = entry.bundle
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

    def extract_files(self):
        """
        Triggered when the Extract Files button is pressed
        Extracts one or multiple selected files in the file's folder
        """
        for item in self.get_selected_items():
            self.extract_single_item(item.bundle)
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
            if not selected_item.bundle.is_raw and not selected_item.bundle.is_folder:
                self.update_current_bnd(selected_item.bundle)

    def back_local_bnd(self):
        """
        Triggered when the Back to previous file button is pressed
        Returns to parent BND
        """
        new_bnd = self.bnd.get_parent()
        while new_bnd.is_folder:
            new_bnd = new_bnd.get_parent()
        self.update_current_bnd(new_bnd)

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

        if not selected_item:
            self.set_default_file_data_values()
            self.pb_copy.setEnabled(False)
            return

        bundle = selected_item.bundle

        self.pb_copy.setEnabled(True)

        # Set default values if there is no bundle
        if not bundle:
            self.set_default_file_data_values()
            return

        # Enable the internal open button
        if not bundle.is_raw and not bundle.is_folder:
            self.pb_open.setEnabled(True)
        else:
            self.pb_open.setEnabled(False)

        # Show encrypted / decrypted
        self.cb_encrypted.setChecked(bundle.encrypted)
        self.cb_gzipped.setChecked(bundle.is_gzipped)
        self.cb_raw.setChecked(bundle.is_raw)
        self.cb_modified.setChecked(bundle.is_modified)

        # CRC text
        self.le_crc.setText((str(hex(bundle.get_crc()))).upper()[2:] + " ")
        self.le_crc.setToolTip(f"File: {bundle.get_local_path()}")

        # CRC tooltip
        to_bytes = bundle.to_bytes(ignore_gzip=True)
        self.le_size.setText(sizeof_fmt(len(to_bytes)) + " ")
        self.le_size.setToolTip(f"Size (ungzipped): {len(to_bytes)} bytes")

        # Set empty preview text
        self.te_preview.setText("")

        # Hex view
        # TODO: Update on thread
        # TODO: Adjust to resize (constraints)
        if len(to_bytes) > 0:
            string = str(binascii.hexlify(to_bytes[0:0x70]))[2:-1]
            string = " ".join(string[i : i + 2] for i in range(0, len(string), 2))
            string = "\n".join(string[i : i + 24] for i in range(0, len(string), 24))
            lines = string.splitlines()
            counter = 0
            for line in lines:
                line = " {0:#0{1}x}".format(counter * 8, 4) + " " + line
                self.te_preview.append(line)
                self.te_preview.setAlignment(QtCore.Qt.AlignLeft)
                counter += 1

    def set_default_file_data_values(self):
        """
        Sets default file data values
        """
        self.te_preview.setText("")
        self.le_crc.setText("CRC")
        self.le_crc.setToolTip("None")
        self.le_size.setText("Size")
        self.le_size.setToolTip(f"None")

    def get_selected_item(self):
        """
        Gets first selected item
        """
        selection = self.treeWidget.selectedItems()
        if (
            selection
            and len(selection) > 0
            and isinstance(selection[0], QTreeWidgetItemBundle)
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

    def select_bnd_datams(self):
        """
        Opens select bnd for DATAMS
        """
        # Ask for Datams file
        datams_data = None
        header_data = None

        input_file = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open DATA_MS.BND file"
        )
        if input_file:
            if input_file[0] != "":
                datams_path = input_file[0]

                # Read DATAMS
                with open(datams_path, "r+b") as f:
                    datams_data = f.read()

        # Ask for Header
        input_file = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open DATA_MS.HED file"
        )
        if input_file:
            if input_file[0] != "":
                header_path = input_file[0]

                # Read header
                with open(header_path, "r+b") as f:
                    header_data = f.read()

        if datams_data and header_data:
            concat_data = header_data + datams_data
            self.update_current_bnd(BND(concat_data))
            self.output_path = os.path.dirname(os.path.abspath(self.path))
            self.file_name = os.path.basename(os.path.abspath(self.path))

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
            self.update_current_bnd(BND(data))
            self.output_path = os.path.dirname(os.path.abspath(self.path))
            self.file_name = os.path.basename(os.path.abspath(self.path))

    def save_bnd_file(self):
        """
        Saves BND file
        """
        if self.path and self.bnd:
            with open(self.path + ".out", "wb") as f:
                f.write(self.bnd.get_root_parent().to_bytes())

    def save_expanded_state(self):
        """
        Saves state of all the BND files
        """
        scroll_bar = self.treeWidget.verticalScrollBar()
        scroll_position = scroll_bar.value()

        if self.bnd:
            self.bnd.scroll_position = scroll_position
            selection = self.get_selected_item()
            if selection:
                self.bnd.last_sub_item = selection.bundle

        root = self.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            root_widget = root.child(i)
            if root_widget.bundle.is_folder:
                root_widget.bundle.is_expanded = root_widget.isExpanded()
                self.save_expanded_state_child(root_widget)

    def save_expanded_state_child(self, item):
        """
        Save state of itself and childs
        """
        for x in range(item.childCount()):
            current_widget = item.child(x)
            if current_widget.bundle and current_widget.bundle.is_folder:
                current_widget.bundle.is_expanded = current_widget.isExpanded()
                self.save_expanded_state_child(current_widget)

    def load_expanded_state(self):
        """
        Sets expanded state of all items
        """
        root = self.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            root_widget = root.child(i)
            if root_widget.bundle.is_folder:
                root_widget.setExpanded(root_widget.bundle.is_expanded)
                self.load_expanded_state_child(root_widget)

        if self.bnd:
            if self.bnd.last_sub_item:
                self.treeWidget.setCurrentItem(self.bnd.last_sub_item.ui)
                self.bnd.last_sub_item.ui.setSelected(True)
            threading.Thread(
                target=self.scroll_to_position,
                daemon=True,
                args=(
                    self.treeWidget.verticalScrollBar(),
                    self.bnd.scroll_position,
                ),
            ).start()

    def load_expanded_state_child(self, item):
        """
        Sets expanded state of all items and childs
        """
        for x in range(item.childCount()):
            current_widget = item.child(x)
            if current_widget.bundle and current_widget.bundle.is_folder:
                current_widget.setExpanded(current_widget.bundle.is_expanded)
                self.load_expanded_state_child(current_widget)

    def scroll_to_position(self, widget, position):
        """
        Scrolls to position
        """
        while widget.value() != position:
            widget.setValue(position)
            time.sleep(0.001)

    def update_current_bnd(self, new_bnd):
        """
        Sets current BND file
        """
        # Save expanded state
        self.save_expanded_state()

        # Assign properties if they're not initialized yet
        if not hasattr(new_bnd, "last_sub_item"):
            new_bnd.last_sub_item = None
        if not hasattr(new_bnd, "scroll_position"):
            new_bnd.scroll_position = 0

        # Get new BND
        self.bnd = new_bnd

        # Reload entries and expanded state
        self.reload_entries()
        self.load_expanded_state()

    def reload_entries(self):
        """
        Reload all entries from BND
        Enables all the buttons
        """
        # Clean tree widget
        self.treeWidget.clear()

        # Add entries to tree widget
        for entry in self.bnd.file_list:
            widget = QTreeWidgetItemBundle(entry, self.style())
            self.treeWidget.addChildBundle(widget)

        # Enable buttons
        self.pb_back.setEnabled(self.bnd.has_parent())
        self.pb_add_file.setEnabled(True)
        self.pb_add_folder.setEnabled(True)
        self.pb_add_bnd.setEnabled(True)
        self.pb_delete_file.setEnabled(True)
        self.pb_extract_file.setEnabled(True)
        self.pb_replace_file.setEnabled(True)

        # Change title
        self.treeWidget.setHeaderLabel(self.bnd.get_full_path())

    def item_changed(self, item):
        """
        Triggered when an item is modified
        """
        if isinstance(item, QTreeWidgetItemBundle):
            self.check_item_filename(item)

    def check_item_filename(self, item: QTreeWidgetItemBundle):
        """
        Check if the item filename is correct according to the file type
        """
        name = item.text(0)

        # Check that folders end with /
        # Check that single files are named [[ GZIPPED FILE ]]
        if item.bundle.is_folder:
            if not name.endswith("/"):
                name += "/"

        self.set_item_name(item, name)

    def set_item_name(self, item: QTreeWidgetItemBundle, text: str):
        """
        Updates item name, reloads entry data if the
        item is currently being selected
        """
        if item.bundle.name != text:
            item.setText(0, text)
            item.bundle.set_name(text)
            if item == self.get_selected_item():
                self.update_current_entry_data()
