# PBundle

PBundle is a .BND file editor, a format commonly used in the Patapon series

## Features

- Single/batch file and folder addition, renaming, replacing and extracting
- Copy/pasting single or multiple files and folders
- Empty bundle addition
- Folder addition/renaming
- Nested/gzipped bundle support
- File data preview (first 0x70 bytes, size, crc, etc.)
- Command line file replacement

## Usage

### Installing requirements

[**Python**](https://www.python.org/downloads/) is required (tested on Python 3.11.0).

Install the requirements by running the `pip install -r requirements.txt` command or by executing the `requirements.bat` file.

### Running PBundle

You can run PBundle executing the following command:

```
Python P3-Bundle/src/main.py
```

### Command line mode

Quickreplace allows command line file replacement. Currently it only supports DATA_CMN.

Usage:

```
PBundle/src/main.py -qr -s "replacement_file" -p "replacement_file_path" -d "bundle_file"
```

Example:

```
PBundle/src/main.py -qr -s "azito.pac" -p "loadinggroupscript/basesscriptdata.bnd/loadinggroupcmn.bndz/scriptlist.bnd/azito.pac" -d "DATA_CMN.BND"
```

## To-do

- Implement DATAMS file support (currently in progress)
- Implement more command line features (extract all files, add folders, etc.)
