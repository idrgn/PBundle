import sys
import argparse

from PyQt5 import QtWidgets

from window import Application
from quickreplace import quick_replace

print("BND Editor. Created by Maikel.")


if __name__ == "__main__":

    # Create argument parser
    parser = argparse.ArgumentParser(description="PBundle")

    # Arguments
    parser.add_argument(
        "-quickreplace",
        "-qr",
        action="store_true",
        help="Quick replace mode",
        default=False,
    )

    parser.add_argument("-sourcefile", "-s", type=str, help="Replacement file")
    parser.add_argument("-internalpath", "-p", type=str, help="Internal file path")
    parser.add_argument(
        "-destinationfile", "-d", type=str, help="BND file to be modified"
    )

    # Parse arguments
    args = parser.parse_args()

    # Quick replace mode, useful for automating file packing
    # Or normal mode, with UI
    if args.quickreplace:
        if not args.destinationfile:
            print("Missing destination BND file (-d 'destination')")
        elif not args.sourcefile:
            print("Missing source file (-s 'source')")
        elif not args.internalpath:
            print("Missing internal file path (-p 'path')")
        else:
            quick_replace(args.destinationfile, args.sourcefile, args.internalpath)
    else:
        app = QtWidgets.QApplication(sys.argv)
        main_window = Application()
        main_window.show()
        app.exec_()
