import shutil
import sys
import tempfile

from PyQt5 import QtGui, QtWidgets

from bnd.bnd import BND
from data import *
from interface import main_window
from interface.tree_bundle_item import QTreeWidgetBundleItem


def display_error(text):
    msg = QtWidgets.QMessageBox()
    msg.setWindowIcon(msg.style().standardIcon(
        QtWidgets.QStyle.SP_MessageBoxCritical))
    msg.setWindowTitle("Error")
    msg.setText(text)
    msg.exec_()


class Application(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        QtGui.QFontDatabase.addApplicationFont(
            resource_path("res" + os.sep + "font.ttc"))
        super().__init__()
        
        self.setupUi(self)

        # Delete temp
        shutil.rmtree(tempfile.gettempdir() + os.sep +"bnd_editor" + os.sep, ignore_errors=True)
        self.setWindowIcon(QtGui.QIcon(resource_path("res" + os.sep + "icon.png")))
        self.action_load.triggered.connect(self.select_bnd)

        # If opened via cmd with parameters
        if len(sys.argv) > 1:
            if sys.argv[1]:
                file = sys.argv[1]
                file = file.replace("\\", "/")
                self.load_bnd_file(file)

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
            self.bnd = BND(data)
            self.reload_entries()

    def reload_entries(self):
        """
        Reload all entries from BND
        """
        self.treeWidget.clear()
        for entry in self.bnd.file_list:
            widget = QTreeWidgetBundleItem(entry, self.style())
            self.treeWidget.addTopLevelItem(widget)
