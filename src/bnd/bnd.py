import gzip
import zlib
from struct import pack

from const import BND_FILE_HEADER, BND_HEADER, EMPTY_BLOCK, EMPTY_WORD, GZIP_HEADER
from data import (
    p3hash,
    read_byte_array,
    read_char,
    read_str,
    read_uint,
    replace_byte_array,
)


class BND:
    """
    BND Object
    """

    def __init__(
        self,
        data: bytes = b"",
        name: str = "",
        depth: int = 0,
        encrypted: bool = False,
        is_folder: bool = False,
        level: int = None,
    ):
        self.file_list = []

        # So only opened items
        # will be processed
        self.scroll_position = 0
        self.is_expanded = False
        self.is_modified = False
        self.raw_data = data

        # Needed stuff for packing
        self.name = name
        self.depth = depth
        self.encrypted = encrypted
        self.parent = None
        self.level = level

        # Gzipped or single BND
        self.is_gzipped = False
        self.is_single_file = False

        # Is folder
        self.is_folder = is_folder
        self.is_raw = False
        if self.is_folder:
            return

        # Default values
        self.version = None
        self.value1 = None
        self.value2 = None
        self.empty_blocks = None
        self.data = None

        # Read data
        self.read_from_file(data)

    def update_data(self, data: bytes = [], encrypted: bool = False):
        """
        Updates data
        """
        self.file_list = []
        self.raw_data = data
        self.encrypted = encrypted

        # Is raw
        self.is_raw = False

        # Gzipped or single BND
        self.is_gzipped = False
        self.is_single_file = False

        # Default values
        self.version = None
        self.value1 = None
        self.value2 = None
        self.empty_blocks = None
        self.data = None

        # Read
        self.read_from_file(data)
        self.set_modified()

    def copy(self):
        """
        Generates a copy of itself
        """
        copy = BND(
            self.raw_data,
            self.name,
            self.depth,
            self.encrypted,
            self.is_folder,
            self.level,
        )

        if self.is_folder:
            for item in self.file_list:
                copy.add_to_file_list(item.copy())

        return copy

    def delete(self):
        """
        Deletes itself
        """
        if self.parent:
            self.parent.set_modified()
            self.parent.file_list.remove(self)
            del self

    def set_modified(self):
        """
        Sets as modified
        """
        self.is_modified = True
        if self.parent:
            self.parent.set_modified()

    def set_name(self, name: str):
        """
        Updates name
        """
        self.name = name
        if self.parent:
            self.parent.set_modified()

    def get_root_parent(self):
        """
        Gets root parent
        """
        if self.parent is None:
            return self
        else:
            return self.parent.get_root_parent()

    def get_depth_file_list(self):
        """
        Gets file list with folders in same directory, in order
        """
        new_list = []
        for file in self.file_list:
            new_list.append(file)
            if file.is_folder:
                new_list.extend(file.get_depth_file_list())
        return new_list

    def get_all_children_bytes(self):
        """
        Returns all files as a list of byte arrays
        """
        list = []
        for item in self.file_list:
            if not item.is_folder:
                list.append(item.to_bytes())
        return list

    def print_data(self):
        """
        Shows all the files inside the BND
        """
        print(f"File: {self.name}")
        for item in self.file_list:
            print(
                f" - Files in folder {item.get_full_path()} : {item.get_file_count()}"
            )

    def get_file_count(self):
        """
        Gets the file count, including folders
        """
        count = 0
        for item in self.file_list:
            count += 1
            if item.is_folder:
                count += item.get_file_count()
        return count

    def get_total_file_count(self):
        """
        Gets the file count, including folders and sub items
        """
        count = 0
        for item in self.file_list:
            count += 1
            if not item.is_raw:
                count += item.get_total_file_count()
        return count

    def get_bnd_count(self):
        """
        Counts amount of BND files
        """
        count = 0
        for item in self.file_list:
            if item.is_folder:
                count += item.get_bnd_count()
            else:
                count += 1
        return count

    def get_bundle_from_filename_array(self, filename_array):
        """
        Tries to get bundle from a filename array
        """
        # Return None if array is empty
        if len(filename_array) == 0:
            return None
        else:
            # Get first item of the array
            current_filename = filename_array[0]

            # Check all bundles
            for bundle in self.file_list:
                print(" -", bundle.name)
                if bundle.name.strip("/") == current_filename:
                    if len(filename_array) == 1:
                        return bundle
                    else:
                        filename_array.pop(0)
                        return bundle.get_bundle_from_filename_array(filename_array)

            # Return none if bundle not found
            return None

    def get_last_folder(self):
        """
        Obtains the last folder inside the BND
        """
        for item in reversed(self.file_list):
            if item.is_folder:
                return item
        return None

    def get_parent(self):
        """
        Add item to file list
        """
        return self.parent

    def get_full_path(self):
        """
        Return full path
        """
        name = self.name

        # If no name, add root
        if name == "":
            name = "root"

        # If has parent, add parent name
        if self.parent:
            name = self.parent.get_full_path() + name

        # If noit folder, add slash
        if not self.is_folder:
            name = name + "/"

        return name

    def get_export_path(self, base: bool = False):
        """
        Generates path for file exporting
        """
        name = self.name

        # If noit folder, add slash
        if not self.is_folder:
            if not base:
                name = "@" + name + "/"

        # If has parent, add parent name
        if self.parent:
            name = self.parent.get_export_path() + name
        else:
            return ""

        return name

    def get_local_path(self):
        """
        Return local path
        """
        if self.parent is None:
            return self.name
        else:
            if not self.parent.is_folder:
                return self.name
            else:
                return self.parent.get_local_path() + self.name

    def add_to_file_list(
        self,
        item: object,
        set_modified: bool = False,
        overwrite_level: bool = False,
        index: int = None,
    ):
        """
        Add item to file list
        """

        item.set_parent(self)

        if overwrite_level:
            if self.is_folder:
                if item.is_folder:
                    item.level = self.level + 1
                    item.depth = self.depth + 1
                else:
                    item.level = (self.level + 1) * -1
                    item.depth = (self.depth + 1) * -1
            else:
                if item.is_folder:
                    item.level = 1
                    item.depth = 1
                else:
                    item.level = -1
                    item.depth = -1

        if item not in self.file_list:
            if index == None:
                self.file_list.append(item)
            else:
                self.file_list.insert(index, item)
            if set_modified:
                self.set_modified()

    def get_crc(self):
        """
        Converts full path to CRC
        """
        return zlib.crc32(str.encode(self.get_local_path()))

    def set_parent(self, parent: object):
        """
        Sets parent object
        """
        self.parent = parent

    def has_parent(self):
        """
        Returns true if object has parent
        """
        return self.parent != None

    def read_from_file(self, data):
        """
        Reads data from a .BND file
        """
        # Decrypt if needed
        if self.encrypted:
            data = p3hash(data, "d")

        # Checks if the header is a gzip header
        if read_byte_array(data, 0x0, 0x3) == GZIP_HEADER:

            # Reassign data with the decrompressed file
            data = zlib.decompress(data, 15 + 32)
            self.is_gzipped = True

            # Check if the resulting file is a BND
            if read_byte_array(data, 0x0, 0x4) != BND_HEADER:

                # Add the simple BND header to the file
                self.data = data
                data = BND_FILE_HEADER + data
                self.is_single_file = True

        # If header is BND
        if not read_byte_array(data, 0x0, 0x4) == BND_HEADER:
            self.is_raw = True
        else:
            # Check if it's a header file
            # Checks if file data exists
            if read_uint(data, 0x14) >= len(data):
                self.is_raw = True
                return

            # Read all the header values
            self.version = read_uint(data, 0x04)
            self.value1 = read_uint(data, 0x08)
            self.value2 = read_uint(data, 0x0C)
            info = read_uint(data, 0x10)

            # Checks all the empty blocks
            empty_blocks = 0

            check = EMPTY_BLOCK

            while check == EMPTY_BLOCK:
                check = read_byte_array(data, 0x28 + empty_blocks * 0x10, 0x10)
                if check == EMPTY_BLOCK:
                    empty_blocks += 1

            entries = read_uint(data, 0x24) - empty_blocks

            self.empty_blocks = empty_blocks

            # Start reading the data
            offset = 0x0

            # Files
            current_level = 0
            current_object = self

            for _ in range(entries):

                crc_pointer = read_uint(data, info + offset + 0x3)

                if crc_pointer != 0:
                    # Reads CRC block containing data
                    crc_block = read_byte_array(data, crc_pointer, 0x10)

                    # Reading data from the CRC block
                    pointer_attributes = read_uint(
                        crc_block, 0x4
                    )  # Address to extra attributes
                    pointer_data = read_uint(
                        crc_block, 0x8
                    )  # Address to the start of the data
                    file_size = read_uint(crc_block, 0xC)  # Size of the data

                    # For DATAMS: File sizes are +0x20000000
                    if file_size >= 0x20000000:
                        file_size -= 0x20000000

                    # Level of the current file (inside folders)
                    file_level = read_char(data, pointer_attributes)

                    # Filename
                    file_name = read_str(data, pointer_attributes + 0x7)

                    # Read file data
                    file_data = read_byte_array(
                        data, pointer_data, file_size
                    )  # File data

                    # FILE LEVEL IS ALWAYS FOLDER LEVEL IN NEGATIVE MINUS ONE
                    # EXAMPLE:
                    # - A file in the root directory will be level -1
                    # - A file in 2 folders will be -3

                    is_change_a_folder = False
                    processed_level = current_level

                    if file_level < 0:
                        processed_level = abs(file_level) - 1
                    else:
                        processed_level = file_level
                        is_change_a_folder = True

                    # If unequal or new folder, do action
                    if processed_level != current_level or is_change_a_folder:

                        # If level is higher than current one, subfolder must be created
                        if processed_level > current_level:
                            # If level is root, add to root
                            new_folder = BND(
                                None,
                                file_name,
                                processed_level,
                                self.encrypted,
                                True,
                                level=file_level,
                            )
                            current_object.add_to_file_list(new_folder)
                            current_object = new_folder

                        # If level is lower than current one, subfolder must be exited
                        elif processed_level < current_level:
                            # Execute difference amount of times in case there is a jump
                            difference = current_level - processed_level
                            for _ in range(difference):
                                # Get parent
                                current_object = current_object.get_parent()

                        # If change is a folder, and it is in the same level as the old one
                        if is_change_a_folder and processed_level <= current_level:
                            # Back to parent
                            current_object = current_object.get_parent()
                            # Create new folder
                            new_folder = BND(
                                None,
                                file_name,
                                processed_level,
                                self.encrypted,
                                True,
                                level=file_level,
                            )
                            # Set to current object
                            current_object.add_to_file_list(new_folder)
                            current_object = new_folder

                        # Set current level
                        current_level = processed_level

                    # Add file
                    if file_level < 0:
                        current_object.add_to_file_list(
                            BND(
                                file_data,
                                file_name,
                                current_object.depth,
                                self.encrypted,
                                level=file_level,
                            )
                        )

                    # Add offset
                    offset += 7 + len(file_name) + 1

    def to_bytes(self, ignore_gzip: bool = False):
        """
        Generates bytes from file data
        """
        # If folder return empty
        if self.is_folder:
            return b""

        # If not modified or raw
        if not self.is_modified or self.is_raw:
            return self.raw_data

        # If single file
        if self.is_single_file:
            if self.is_gzipped and not ignore_gzip:
                return gzip.compress(self.data)
            else:
                return self.data

        #  === SECTION: HEADER
        file_count = self.get_file_count()
        file = BND_HEADER  # 0x0

        # Header values
        file += pack(
            "IIII",
            self.version,
            self.value1,
            self.value2,
            0x28 + self.empty_blocks * 0x10 + file_count * 0x10,
        )  # 0x4 - 0x10

        # Pointers:
        # - Address where file info starts
        # - Address where files start
        # - 0x00000000
        # - 0x00000000
        # This should actually be *4 but for some reason it adds one extra?
        file += EMPTY_WORD * 3

        # Files:
        # - Amount of files with value less than zero
        # - Amount of files + empty blocks
        # - 0x00000000 * 0x4 * amount of empty blocks (might not be needed)
        file += pack("II", self.get_bnd_count(), file_count + self.empty_blocks)
        file += b"\x00" * 0x10 * self.empty_blocks

        # === SECTION: CRC BLOCK
        # == Generate a list with all the items inside the BND and their bytes
        formatted_list = []

        # get data of all the contained items
        file_list = self.get_depth_file_list()
        for item in file_list:
            file_bytes = item.to_bytes()

            formatted_list.append(
                {
                    "crc": item.get_crc(),
                    "name": item.name,
                    "size": len(file_bytes),
                    "bytes": file_bytes,
                }
            )

        # Reorder by crc
        formatted_list = sorted(formatted_list, key=lambda d: d["crc"])

        # Write data: crc - empty (aaddr) - empty (daddr) - size
        for item in formatted_list:
            file += pack("I", item["crc"])
            file += EMPTY_WORD  # info address
            file += EMPTY_WORD  # file data address
            file += pack("I", item["size"])

        # === SECTION: FILE INFO
        previous_entry_length = -1
        current_data_address = 0
        data_address_list = []

        # Address where the file data starts
        file = replace_byte_array(file, 0x10, pack("I", len(file)))

        for entry in file_list:
            # Current file CRC
            crc = entry.get_crc()

            # Get formatted entry
            formatted_entry = next(
                item for item in formatted_list if item["crc"] == crc
            )

            # Index of item inside the list
            index = formatted_list.index(formatted_entry)

            # Calculates address of extra_data
            address = index * 0x10 + 0x28 + 0x10 * self.empty_blocks

            # Appends the data address to the list
            data_address_list.append(
                {
                    "data_address": current_data_address,
                    "crc_block_address": address,
                    "bytes": formatted_entry["bytes"],
                }
            )

            # Is this even used?
            current_data_address += formatted_entry["size"]

            # Add base 4 to length
            if formatted_entry["size"] % 4 != 0:
                current_data_address += 4 - (formatted_entry["size"] % 4)

            # Get length of current entry
            current_entry_length = 7 + len(entry.name) + 1

            # Write address to this file data block to the CRC block
            file = replace_byte_array(file, address + 0x4, pack("I", len(file)))

            # Entry depth level + previous entry data length (0xFF if first one)
            file += pack("bb", entry.level, previous_entry_length)

            # Current entry data length
            file += pack("B", current_entry_length)

            # Address of the corresponding CRC block
            file += pack("<I", address)

            # Filename (should it be full name? w folder)
            file += str.encode(entry.name) + b"\x00"

            # Update
            previous_entry_length = current_entry_length

        # File must end in 512
        while len(file) % 512 != 0:
            file += b"\x00"

        # === SECTION: FILE DATA

        # Address where the file data starts
        # Not sure if this spacing is needed (present in DATACMN)
        # file + b"\x00" + 0x600
        base = len(file)
        file = replace_byte_array(file, 0x14, pack("I", len(file)))

        # Add addresses to CRC block
        for i in range(len(data_address_list)):
            file = replace_byte_array(
                file,
                data_address_list[i]["crc_block_address"] + 0x8,
                pack("I", base + data_address_list[i]["data_address"]),
            )

        # Write the file data
        file = bytearray(file)

        # Iterate over all addresses
        for i in range(len(data_address_list)):
            # Also grabbing files from data by index
            file += data_address_list[i]["bytes"]
            # Make it so next file always start on 0x4 multiple
            while len(file) % 4 != 0:
                file += b"\x00"

        # Convert back to bytes
        file = bytes(file)

        # Gzip
        if self.is_gzipped and not ignore_gzip:
            file = gzip.compress(file)

        # Encrypt
        if self.encrypted:
            file = p3hash(file, "e")

        # Return
        return file
