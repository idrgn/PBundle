from PyQt5 import QtWidgets
from bnd import *
import sys

print("BND Editor. Created by Maikel.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Application()
    window.show() 
    app.exec_()