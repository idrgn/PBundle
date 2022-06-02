from data import *
from classes import *
from PyQt5 import QtCore, QtGui, QtWidgets
import window
import tempfile
import zlib
import gzip
import shutil
import binascii
import sys
import sip

c = cc(BND())
file_list = []
current_properties = [0, ""]  # depth, filename


class About(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_MessageBoxQuestion))
        self.setWindowTitle("About")
        self.setMinimumSize(QtCore.QSize(300, 300))
        self.setMaximumSize(QtCore.QSize(300, 300))
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 0, 281, 51))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(30, 53, 121, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 239, 149))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(30, 82, 91, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.label_3.setObjectName("label_3")
        self.textEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.textEdit.setGeometry(QtCore.QRect(30, 110, 241, 151))
        self.textEdit.setObjectName("textEdit")
        self.label.setText("Patapon BND Editor")
        self.label_2.setText("Created by Madwig")
        self.label_3.setText("Changelog:")
        self.textEdit.setPlainText(
            "This is just a test release.\nNothing to see here yet...")
        self.textEdit.setReadOnly(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.textEdit.setFont(font)


def display_error(text):
    msg = QtWidgets.QMessageBox()
    msg.setWindowIcon(msg.style().standardIcon(
        QtWidgets.QStyle.SP_MessageBoxCritical))
    msg.setWindowTitle("Error")
    msg.setText(text)
    msg.exec_()


class Application(QtWidgets.QMainWindow, window.Ui_MainWindow):
    def __init__(self):
        QtGui.QFontDatabase.addApplicationFont(
            resource_path("res" + os.sep + "font.ttc"))
        super().__init__()
        self.setupUi(self)

        shutil.rmtree(tempfile.gettempdir() + os.sep +
                      "bnd_editor" + os.sep, ignore_errors=True)

        self.setWindowIcon(QtGui.QIcon(
            resource_path("res" + os.sep + "icon.png")))

        self.treeWidget.selectionModel().selectionChanged.connect(self.get_selected_entry)
        self.treeWidget.itemChanged.connect(self.item_changed)
        self.treeWidget.itemSelectionChanged.connect(self.get_data)
        self.treeWidget.expanded.connect(self.updateExpanded)
        self.treeWidget.collapsed.connect(self.updateCollapsed)

        self.action_load.triggered.connect(self.select_bnd)
        self.action_load.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_DialogOpenButton))
        self.action_refresh.triggered.connect(self.reload_bnd)
        self.action_refresh.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_BrowserReload))
        self.action_save.triggered.connect(self.save_file)
        self.action_save.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_DialogSaveButton))
        self.action_save_as.triggered.connect(self.save_file)
        self.action_save_as.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_DriveFDIcon))
        self.action_exit.triggered.connect(sys.exit)
        self.action_exit.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_BrowserStop))

        self.action_about.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_MessageBoxInformation))
        self.action_about.triggered.connect(self.loadInfo)
        self.action_disable_filesystem_and_save.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning))
        self.action_overwrite_all_filenames.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))

        self.pb_delete_file.clicked.connect(self.delete_file)
        self.pb_add_file.clicked.connect(self.add_files)
        self.pb_add_folder.clicked.connect(self.add_folder)
        self.pb_replace_file.clicked.connect(self.replace_file)
        self.pb_moveup.clicked.connect(lambda: self.move_file(-1))
        self.pb_movedown.clicked.connect(lambda: self.move_file(1))
        self.pb_extract_file.clicked.connect(self.extract_file)
        self.pb_open.clicked.connect(self.open_local_bnd)
        self.pb_back.clicked.connect(self.back_local_bnd)

        self.le_crc.selectionChanged.connect(lambda: self.le_crc.deselect())
        self.le_crc.setText("")
        self.le_crc.setToolTip("None")
        self.le_size.selectionChanged.connect(lambda: self.le_size.deselect())
        self.le_size.setText("")
        self.le_size.setToolTip("None")

        if len(sys.argv) > 1:
            if sys.argv[1]:
                file = sys.argv[1]
                file = file.replace("\\", "/")
                self.load_bnd_file(file)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        self.drop_load(event)

    def drop_load(self, event):
        file = event.mimeData()
        file = file.urls()
        file = file[0]
        file = str(file)
        file = file.replace(file[:27], "")
        file = file[:-2]
        self.load_bnd_file(file)

    def load_bnd_file(self, file):
        print(file)
        result, arg1, arg2 = c.bnd_file.read_from_file(
            file, self.check_encryption_decryption.isChecked())
        if result == 0:
            file_list.clear()
            file_list.append([c.bnd_file, -1, c.bnd_file.path,
                             c.bnd_file.path, arg1, arg2])
            current_properties[0] = 0
            # c.bnd_file.print_all_entries()
            self.treeWidget.setHeaderLabel(
                file_list[0][3].split("/")[-1] + "/")
            self.load_entries(c.bnd_file)
        else:
            display_error("Not a valid BND file.")

    def updateCollapsed(self, item):
        self.treeWidget.itemFromIndex(item).setIcon(
            0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))

    def updateExpanded(self, item):
        self.treeWidget.itemFromIndex(item).setIcon(
            0, self.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon))

    def loadInfo(self):
        self.aboutw = About()
        self.aboutw.show()

    def create_entry(self, index):
        entry = QtWidgets.QTreeWidgetItem()
        entry.setText(0, c.bnd_file.data[index].fname)
        if c.bnd_file.data[index].flevel > 0:
            icon = QtWidgets.QStyle.SP_DirIcon
        else:
            icon = QtWidgets.QStyle.SP_FileIcon
        entry.setIcon(0, self.style().standardIcon(icon))
        entry.setData(0, QtCore.Qt.UserRole, index)
        entry.setFlags(entry.flags() | QtCore.Qt.ItemIsEditable)
        return entry

    def move_file(self, displacement):
        index = self.get_selected_entry()
        if index != -1:
            if c.bnd_file.data[index].flevel > 0:
                return
            result = c.bnd_file.move_entry(index, displacement)
            if result != -1:
                if self.check_reload_on_save.isChecked():
                    self.load_entries(c.bnd_file)
                    return
                ilist = self.get_item_list()
                parent = c.bnd_file.get_parent(index)
                pos = self.treeWidget.currentIndex().row()
                newitem = self.create_entry(result)
                sip.delete(ilist[index])
                if c.bnd_file.data[result].flevel == -1:
                    self.treeWidget.insertTopLevelItem(
                        pos + displacement, newitem)
                else:
                    ilist[parent].insertChild(result-parent-1, newitem)
                self.update_entry_ids()
                self.treeWidget.setCurrentItem(newitem)

    def delete_file(self):
        selection = self.treeWidget.selectedItems()
        if selection:
            flist = []
            for file in selection:
                flist.append(file.data(0, QtCore.Qt.UserRole))
            flist.sort(reverse=True)
            for index in flist:
                c.bnd_file.delete_entry(index)
            if self.check_reload_on_save.isChecked():
                self.load_entries(c.bnd_file)
                return
            for file in selection:
                sip.delete(file)
            self.update_entry_ids()
            # self.load_entries(c.bnd_file)

    def add_files(self):
        input_files = QtWidgets.QFileDialog.getOpenFileNames(self, "Open")
        if input_files:
            if input_files[0]:
                if input_files[0][0] != "":
                    for path in input_files[0]:
                        # print(path)
                        insertion = c.bnd_file.add_entry(
                            self.get_selected_entry(), path)
                        if self.check_reload_on_save.isChecked():
                            self.load_entries(c.bnd_file)
                            return
                        # print(insertion)
                        parent = c.bnd_file.get_parent(insertion)
                        items = self.get_item_list()
                        # print(c.bnd_file.data[insertion].flevel)
                        parenti = items[parent]
                        entry = self.create_entry(insertion)
                        if c.bnd_file.data[insertion].flevel == -1:
                            self.treeWidget.insertTopLevelItem(0, entry)
                        else:
                            parenti.insertChild(0, entry)
                        name = c.bnd_file.data[parent].fname
                        self.update_entry_ids()
                        c.bnd_file.data[parent].fname = name
                    # self.load_entries(c.bnd_file)

    def update_buttons(self):
        b = not file_list[-1][5]
        self.pb_add_file.setEnabled(b)
        self.pb_add_folder.setEnabled(b)
        self.pb_delete_file.setEnabled(b)
        self.pb_movedown.setEnabled(b)
        self.pb_moveup.setEnabled(b)

    def save_file(self):
        if len(file_list) <= 1 or current_properties[0] == 0:
            fname = file_list[-1][2]
            gzipd = file_list[-1][4]
            singl = file_list[-1][5]
            c.bnd_file.save_file(self.check_encryption_decryption.isChecked(
            ), self.check_extended_backup_files.isChecked())
            if singl or gzipd:
                f = open(fname, "r+b")
                data = f.read()
                if singl:
                    data = data[512:]
                if gzipd:
                    data = gzip.compress(data)
                with open(c.bnd_file.path, "wb") as r:
                    r.write(data)
        else:
            c.bnd_file.save_file(self.check_encryption_decryption.isChecked(
            ), self.check_extended_backup_files.isChecked())
            file_list[-1][0] = c.bnd_file
            index = file_list[-1][1]
            fname = file_list[-1][2]
            gzipd = file_list[-1][4]
            singl = file_list[-1][5]
            for i in reversed(file_list[:-1]):
                f = open(fname, "r+b")
                data = f.read()
                if singl:
                    data = data[512:]
                if gzipd:
                    data = gzip.compress(data)
                c.bnd_file = i[0]
                c.bnd_file.replace_entry_send_data(index, data)
                c.bnd_file.save_file(self.check_encryption_decryption.isChecked(
                ), self.check_extended_backup_files.isChecked())
                i[0] = c.bnd_file
                index = i[1]
                fname = i[2]
                gzipd = i[4]
                singl = i[5]
            c.bnd_file = file_list[-1][0]

    def open_local_bnd(self):
        index = self.get_selected_entry()
        if index != -1:
            if c.bnd_file.data[index].flevel < 0:
                data = c.bnd_file.data[index].fdata
                name = c.bnd_file.data[index].fname
                fcrc = str(zlib.crc32(str.encode(
                    name + "/" + c.bnd_file.get_path(index))))
                temp = tempfile.gettempdir() + os.sep + "bnd_editor" + os.sep
                path = temp + fcrc + ".BND"
                gzpd = False
                sfil = False
                if len(data) > 0x28:
                    # if gzipped and not bnd, add a basic bnd header and ALSO change another flag
                    if read_byte_array(data, 0x0, 0x3) == b'\x1f\x8b\x08':
                        data = zlib.decompress(data, 15 + 32)
                        gzpd = True
                        if read_byte_array(data, 0x0, 0x4) != b'BND\x00':
                            sfil = True
                            x = open(resource_path(
                                "res" + os.sep + "bnd_header"), "r+b")
                            ndata = x.read()
                            data = ndata + data
                    if read_byte_array(data, 0x0, 0x4) == b'BND\x00':
                        try:
                            os.makedirs(temp)
                        except OSError:
                            pass
                        with open(path, "wb") as r:
                            r.write(data)
                        bndf = BND()
                        bndf.read_from_file(
                            path, self.check_encryption_decryption.isChecked())
                        file_list.append(
                            [bndf, index, bndf.path, c.bnd_file.get_path(index), gzpd, sfil])
                        current_properties[0] += 1
                        c.bnd_file = bndf
                        self.load_entries(c.bnd_file)
                        self.update_filename()
                        self.update_buttons()
            else:
                selection = self.treeWidget.selectedItems()
                if selection:
                    sel = selection[0]
                    sel.setExpanded(True)

    def back_local_bnd(self):
        if len(file_list) <= 1 or current_properties[0] == 0:
            return
        os.remove(file_list[-1][2])
        file_list.pop()
        c.bnd_file = file_list[-1][0]
        current_properties[0] -= 1
        self.load_entries(c.bnd_file)
        self.update_filename()
        if current_properties[0] == 0:
            shutil.rmtree(tempfile.gettempdir() + os.sep +
                          "bnd_editor" + os.sep, ignore_errors=True)
        self.update_buttons()

    def add_folder(self):  # fix
        text, selection = QtWidgets.QInputDialog.getText(
            self, 'New folder', 'Enter folder name:')
        if selection:
            if text != "":
                if not text.endswith("/"):
                    text = text + "/"
                insertion = c.bnd_file.add_folder(
                    self.get_selected_entry(), str(text))
                if self.check_reload_on_save.isChecked():
                    self.load_entries(c.bnd_file)
                    return
                parent = c.bnd_file.get_parent(insertion)
                items = self.get_item_list()
                parenti = items[parent]
                entry = self.create_entry(insertion)
                if c.bnd_file.data[insertion].flevel == 1:
                    self.treeWidget.insertTopLevelItem(0, entry)
                else:
                    parenti.insertChild(0, entry)
                name = c.bnd_file.data[parent].fname
                self.update_entry_ids()
                c.bnd_file.data[parent].fname = name
                # self.load_entries(c.bnd_file)

    def update_entry_ids(self):
        i = 0
        self.treeWidget.blockSignals(True)
        for item in self.treeWidget.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            item.setData(0, QtCore.Qt.UserRole, i)
            i += 1
        self.treeWidget.blockSignals(False)

    def get_item_list(self):
        ilist = []
        for item in self.treeWidget.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            ilist.append(item)
        return ilist

    def delete_all_items(self):
        for item in self.treeWidget.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            sip.delete(item)

    def get_selected_entry(self):
        selection = self.treeWidget.selectedItems()
        if selection:
            sel = selection[0]
            identifier = sel.data(0, QtCore.Qt.UserRole)
            return identifier
        return -1

    def load_entries(self, file):
        # self.delete_all_items()
        self.treeWidget.clear()
        x = 0
        while x < len(c.bnd_file.data):
            if c.bnd_file.data[x].flevel >= 0:
                entry = self.create_entry(x)
                index = self.search_sub(x, c.bnd_file.data[x].flevel, entry)
                x += index
            else:
                entry = self.create_entry(x)
                x += 1
            self.treeWidget.addTopLevelItem(entry)
        self.pb_back.setEnabled(current_properties[0] > 0)
        self.pb_add_file.setEnabled(True)
        self.pb_add_folder.setEnabled(True)
        self.pb_delete_file.setEnabled(True)
        self.pb_extract_file.setEnabled(True)
        self.pb_replace_file.setEnabled(True)
        self.pb_movedown.setEnabled(True)
        self.pb_moveup.setEnabled(True)

    def search_sub(self, position, current_type, entry):
        next_folder_type = current_type + 1  # the id of next folder
        current_file_type = -1 - current_type  # the id of this folder's files
        index = 1
        if index+position > len(c.bnd_file.data)-1:
            return index
        next_entry_type = c.bnd_file.data[position+index].flevel
        while next_entry_type == next_folder_type or next_entry_type == current_file_type and index < len(c.bnd_file.data):
            if next_folder_type == next_entry_type:
                newentry = self.create_entry(position+index)
                index = index + \
                    self.search_sub(
                        position+index, next_entry_type, newentry) - 1
                entry.addChild(newentry)
            if current_file_type == next_entry_type:
                newentry = self.create_entry(position+index)
                entry.addChild(newentry)
            index += 1
            if index+position > len(c.bnd_file.data)-1:
                return index
            next_entry_type = c.bnd_file.data[position+index].flevel
        return index

    def update_filename(self):
        string = file_list[0][3].split("/")[-1] + "/"
        for i in file_list[1:]:
            string += i[3].split("/")[-1] + os.sep
            string = string.replace("/", os.sep)
            string = string.replace("\\", os.sep)
        self.treeWidget.setHeaderLabel(string)

    def reload_bnd(self):  # fix
        if c.bnd_file.path != "":
            c.bnd_file = file_list[0][0]
            result, arg1, arg2 = c.bnd_file.read_from_file(
                c.bnd_file.path, self.check_encryption_decryption.isChecked())
            if result == 0:
                file_list.clear()
                file_list.append(
                    [c.bnd_file, -1, c.bnd_file.path, c.bnd_file.path, arg1, arg2])
                current_properties[0] = 0
                ntitle = file_list[0][3].split("/")[-1] + os.sep
                ntitle = ntitle.replace("/", os.sep)
                ntitle = ntitle.replace("\\", os.sep)
                self.treeWidget.setHeaderLabel(ntitle)
                self.load_entries(c.bnd_file)
            else:
                display_error("Not a valid BND file.")

    def select_bnd(self):
        input_file = QtWidgets.QFileDialog.getOpenFileName(self, "Open")
        if input_file:
            if input_file[0] != "":
                self.load_bnd_file(input_file[0])

    def extract_file(self):
        selection = self.treeWidget.selectedItems()
        if selection:
            for item in selection:
                path = ""
                index = item.data(0, QtCore.Qt.UserRole)
                if current_properties[0] > 0:
                    path = file_list[0][3].split("/")[-1] + "/"
                    for i in range(len(file_list[:1])):
                        path += file_list[i][0].get_path(file_list[i+1][1])
                    path = os.path.dirname((os.path.abspath(
                        file_list[0][0].path))) + os.sep + "extracted" + os.sep + path + os.sep
                c.bnd_file.extract_handler(index, path)

    def replace_file(self):
        selection = self.treeWidget.selectedItems()
        if selection:
            for i in range(len(selection)):
                if c.bnd_file.data[selection[i].data(0, QtCore.Qt.UserRole)].flevel < 0:
                    input_file = QtWidgets.QFileDialog.getOpenFileName(self, "Open file to replace file " + str(
                        i) + ": " + c.bnd_file.data[selection[i].data(0, QtCore.Qt.UserRole)].fname)
                    if input_file:
                        if input_file[0] != "":
                            c.bnd_file.replace_entry_data(selection[i].data(
                                0, QtCore.Qt.UserRole), input_file[0])
                            self.get_data()

    def get_data(self):
        index = self.get_selected_entry()
        if index != -1 and index < len(c.bnd_file.data):
            # print(c.bnd_file.get_path(index))
            self.le_crc.setText(
                (str(hex(c.bnd_file.data[index].crc))).upper()[2:] + " ")
            self.le_crc.setToolTip("File: " + c.bnd_file.get_path(index))
            self.le_size.setText(sizeof_fmt(c.bnd_file.data[index].size) + " ")
            self.le_size.setToolTip(
                "Size: " + str(c.bnd_file.data[index].size) + " bytes")
            self.te_preview.setText("")
            if len(c.bnd_file.data[index].fdata) > 0:
                string = str(binascii.hexlify(
                    c.bnd_file.data[index].fdata[0:0x70]))[2:-1]
                string = ' '.join(string[i:i+2]
                                  for i in range(0, len(string), 2))
                string = '\n'.join(string[i:i+24]
                                   for i in range(0, len(string), 24))
                lines = string.splitlines()
                self.te_preview.append("\n")
                counter = 0
                for line in lines:
                    line = "{0:#0{1}x}".format(counter * 8, 4) + " " + line
                    self.te_preview.append(line)
                    self.te_preview.setAlignment(QtCore.Qt.AlignLeft)
                    counter += 1
            data = c.bnd_file.data[index].fdata
            if read_byte_array(data, 0x0, 0x3) == b'\x1f\x8b\x08' or read_byte_array(data, 0x0, 0x4) == b'BND\x00':
                self.pb_open.setEnabled(True)
            else:
                self.pb_open.setEnabled(False)
        else:
            self.le_crc.setText("")
            self.le_crc.setToolTip("None")
            self.le_size.setText("")
            self.le_size.setToolTip("None")
            self.te_preview.setText("")
            self.pb_open.setEnabled(False)

    def item_changed(self, item):
        new_name = item.text(0)
        if file_list[-1][5]:
            if new_name != "[[ GZIPPED FILE ]]":
                item.setText(0, "[[ GZIPPED FILE ]]")
            return
        edited_item = self.get_selected_entry()
        if edited_item != -1 or edited_item < len(c.bnd_file.data):
            if c.bnd_file.data[edited_item].flevel > 0:
                if not new_name.endswith("/"):
                    new_name += "/"
                    item.setText(0, new_name)
                    return
            # print("Renamed item: ", c.bnd_file.data[edited_item].fname, "to", new_name)
            c.bnd_file.data[edited_item].fname = new_name
            # old_crc = c.bnd_file.data[edited_item].crc
            c.bnd_file.update_crc()
            # print("Old CRC: ", old_crc, " and new: ", c.bnd_file.data[edited_item].crc)
            self.get_data()

    def get_selected_item(self):
        selection = self.treeWidget.selectedItems()
        if selection:
            sel = selection[0]
        return sel
