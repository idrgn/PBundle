from bnd.bnd import BND
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyle, QTreeWidgetItem


class QTreeWidgetItemBundle(QTreeWidgetItem):
    def __init__(self, item: BND, style) -> None:
        super().__init__()

        self.parent = None

        # Name
        self.setText(0, item.name)

        # Vairable icon
        if item.is_folder:
            icon = QStyle.SP_DirIcon
        else:
            icon = QStyle.SP_FileIcon

        # Set icon
        self.setIcon(0, style.standardIcon(icon))
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        # Save variable
        self.bundle = item
        self.bundle.ui = self
        self.style = style

        # Add subfolders
        if self.bundle.is_folder:
            self.addSubItems()

    def addChildBundle(self, bundle: BND):
        widget = QTreeWidgetItemBundle(bundle, self.style)
        widget.setParent(self)
        self.addChild(widget)

    def addSubItems(self):
        """
        Adds items in subfolders
        """
        for item in self.bundle.file_list:
            self.addChildBundle(item)

    def setParent(self, parent):
        """
        Sets parent
        """
        self.parent = parent

    def getParent(self):
        """
        Gets parent
        """
        return self.parent
