
from bnd.bnd import BND
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyle, QTreeWidgetItem


class QTreeWidgetBundleItem(QTreeWidgetItem):
    def __init__(self, item: BND, style) -> None:
        super().__init__()

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
        self.bundleItem = item
        self.style = style

        # Add subfolders
        if self.bundleItem.is_folder:
            self.add_sub_items()

    def add_sub_items(self):
        """
        Adds items in subfolders
        """
        for item in self.bundleItem.file_list:
            self.addChild(QTreeWidgetBundleItem(item, self.style))