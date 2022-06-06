import typing
from bnd.bnd import BND
from PyQt5.QtWidgets import QWidget, QTreeWidget

from interface.tree_widget_item_bundle import QTreeWidgetItemBundle


class QTreeWidgetBundle(QTreeWidget):
    def __init__(self, parent: typing.Optional[QWidget] = ...) -> None:
        super().__init__(parent)
        self.bundle = None

    def setBundle(self, bundle: BND):
        """
        Sets bundle
        """
        self.bundle = bundle
        self.bundle.ui = self

    def setStyle(self, style):
        """
        Sets style
        """
        self.style = style

    def addChildBundle(self, item: QTreeWidgetItemBundle):
        """
        Adds child bundle
        """
        if isinstance(item, BND):
            self.addTopLevelItem(QTreeWidgetItemBundle(item, self.style))
        elif isinstance(item, QTreeWidgetItemBundle):
            self.addTopLevelItem(item)

    def addTopLevelItem(self, item: QTreeWidgetItemBundle) -> None:
        """
        Overwrite for addTopLevelItem
        """
        item.setParent(self)
        if self.bundle:
            self.bundle.add_to_file_list(item.bundle)
        return super().addTopLevelItem(item)

    def getParent(self):
        """
        Returns self because it's always root
        """
        return self
