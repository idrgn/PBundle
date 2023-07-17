import os
import sys
import tempfile
from pathlib import Path
from struct import unpack
from subprocess import check_output

import camellia
import cffi
import pep272_encryption


def p3hash_camellia(data: bytes, encrypt: bool = False):
    c = camellia.CamelliaCipher(
        key=b"SVsyE56pniSRS9dIPTiE8ApDaUnN0AEa", mode=camellia.MODE_ECB
    )

    if encrypt:
        return c.encrypt(data)
    else:
        return c.decrypt(data)


def p3hash(data: bytes, mode: str):
    """
    mode (str): "d" decrypt / "e" encrypt
    """
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".bin", delete=False) as tf:
        data_length = len(data)

        # Return data if the file is empty
        if data_length == 0:
            return data

        # Add padding if the file is small
        if mode == "d":
            if data_length < 10000:
                data += b"\x00" * (10000 - data_length)

        # Get file paths
        initial_file_path = Path(tf.name)
        result_file_path = Path(f"{tf.name}.decrypted")

        # Save file
        tf.write(data)

        # Decrypt
        check_output(
            f"{resource_path('res/ext/p3h.exe').as_posix()} {initial_file_path} {result_file_path} {mode}",
            shell=True,
        )

        # Read decrypted file
        with open(result_file_path, "rb") as tf2:
            print(f" - Old: {data_length}")
            data = tf2.read()
            if mode == "d":
                if data_length < len(data):
                    data = data[0:data_length]
                    print(f" - Size adjusted")

            print(f" - New: {len(data)}")

        # Remove result file
        result_file_path.unlink()

    # Remove original file
    initial_file_path.unlink()
    return data


def resource_path(relative_path: str) -> Path:
    current_path = Path(".")
    if hasattr(sys, "_MEIPASS"):
        current_path = Path(sys._MEIPASS)
    else:
        current_path = Path(os.path.dirname(__file__))
    return current_path.joinpath(relative_path)


def replace_byte_array(fdata: bytes, position: int, value: bytes):
    fdata = bytearray(fdata)
    for i in range(0, len(value)):
        fdata[position + i] = value[i]
    fdata = bytes(fdata)
    return fdata


def read_uint(fdata: bytes, position: int) -> int:
    return unpack("I", read_byte_array(fdata, position, 4))[0]


def read_ushort(fdata: bytes, position: int) -> int:
    return unpack("H", read_byte_array(fdata, position, 2))[0]


def read_uchar(fdata: bytes, position: int) -> int:
    return unpack("B", read_byte_array(fdata, position, 1))[0]


def read_int(fdata: bytes, position: int) -> int:
    return unpack("i", read_byte_array(fdata, position, 4))[0]


def read_short(fdata: bytes, position: int) -> int:
    return unpack("h", read_byte_array(fdata, position, 2))[0]


def read_char(fdata: bytes, position: int) -> int:
    return unpack("b", read_byte_array(fdata, position, 1))[0]


def read_byte_array(fdata: bytes, position: int, size: int) -> bytes:
    if position + size > len(fdata):
        size = len(fdata) - position
    return fdata[position : position + size]


# def read_str(fdata: bytes, position: int) -> str:
#     string = ""
#     offset = 0x0
#     while read_byte_array(fdata, position + offset, 0x1) != b"\x00":
#         string += chr(read_uchar(fdata, position + offset))
#         offset += 1
#     return string


def read_str(fdata: bytes, position: int) -> str:
    string_bytes = bytearray()
    offset = 0x0
    while (last_byte := read_uchar(fdata, position + offset)) != 0x00:
        string_bytes.append(last_byte)
        offset += 1
    string = unpack(f"{len(string_bytes)}s", string_bytes)[0].decode()
    return string


def sizeof_fmt(num, suffix: str = "B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, "Yi", suffix)


def split_datams(data: bytes):
    base = read_uint(data, 0x14)
    return data[:base], data[base:]
