import sys

from PyQt5 import QtWidgets

from window import Application
from quickreplace import quick_replace

print("BND Editor. Created by Maikel.")

if __name__ == "__main__":
    do_quick_replace = False

    # Quick replace mode check
    if len(sys.argv) > 1:
        if sys.argv[1] == "-qr":
            do_quick_replace = True

    # Quick replace mode, useful for automating file packing
    if do_quick_replace:
        if len(sys.argv) < 5:
            print("Usage: -qr file source destination")
        else:
            qr_file = sys.argv[2]
            qr_source = sys.argv[3]
            qr_destination = sys.argv[4]
            quick_replace(qr_file, qr_source, qr_destination)

    # Normal mode, with UI
    else:
        app = QtWidgets.QApplication(sys.argv)
        main_window = Application()
        main_window.show()
        app.exec_()
