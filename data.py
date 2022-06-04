import os
import sys
import tempfile
from subprocess import check_output


def p3hash(data, mode):
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".bin", delete=False) as tf:
        temp = tf.name
        tf.write(data)
        check_output(
            resource_path("res\ext\p3h.exe")
            + " "
            + tf.name
            + " "
            + tf.name
            + "1 "
            + mode,
            shell=True,
        )
        with open(tf.name + "1", "rb") as tf2:
            data = tf2.read()
        os.remove(tf.name + "1")
    os.remove(temp)
    return data


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def replace_byte_array(fdata, position, value):
    fdata = bytearray(fdata)
    for i in range(0, len(value)):
        fdata[position + i] = value[i]
    fdata = bytes(fdata)
    return fdata


def to_signed(n, byte_count):
    return int.from_bytes(n.to_bytes(byte_count, "little"), "little", signed=True)


def read_integer(fdata, position, size):
    return int.from_bytes(
        read_byte_array(fdata, position, size), byteorder="little", signed=False
    )


def read_byte_array(fdata, position, size):
    if position + size > len(fdata):
        size = len(fdata) - position
    return fdata[position : position + size]


def read_string(fdata, position):
    string = ""
    offset = 0x0
    while read_byte_array(fdata, position + offset, 0x1) != b"\x00":
        string += chr(read_integer(fdata, position + offset, 0x1))
        offset += 1
    return string


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, "Yi", suffix)
