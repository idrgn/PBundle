import shutil
import sys
import tempfile

from PyQt5 import QtGui, QtWidgets

from bnd.bnd import BND
from data import *
from interface import main_window
from interface.tree_bundle_item import QTreeWidgetBundleItem


class Application(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        QtGui.QFontDatabase.addApplicationFont(
            resource_path("res" + os.sep + "font.ttc"))
        super().__init__()
        
        # Init
        self.path = None
        self.setupUi(self)
        self.set_connections()

        # Delete temp
        shutil.rmtree(tempfile.gettempdir() + os.sep +"bnd_editor" + os.sep, ignore_errors=True)
        self.setWindowIcon(QtGui.QIcon(resource_path("res" + os.sep + "icon.png")))

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
        self.treeWidget.itemSelectionChanged.connect(self.selection_changed)

    def open_local_bnd(self):
        """
        Open BND inside the current BND
        """
        selected_item = self.get_selected_item()
        if selected_item:
            if not selected_item.bundleItem.is_raw and not selected_item.bundleItem.is_folder:
                self.bnd = selected_item.bundleItem
                self.reload_entries()

    def back_local_bnd(self):
        """
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
            if not selected_item.bundleItem.is_raw and not selected_item.bundleItem.is_folder:
                self.pb_open.setEnabled(True)
            else:
                self.pb_open.setEnabled(False)
        else:
            self.pb_open.setEnabled(False)

    def get_selected_item(self):
        """
        Gets first selected item
        """
        selection = self.treeWidget.selectedItems()
        if selection:
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
        self.pb_add_file.setEnabled(True)
        self.pb_add_folder.setEnabled(True)
        self.pb_delete_file.setEnabled(True)
        self.pb_extract_file.setEnabled(True)
        self.pb_replace_file.setEnabled(True)
        self.pb_movedown.setEnabled(True)
        self.pb_moveup.setEnabled(True)
