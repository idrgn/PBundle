import zlib

from const import BND_FILE_HEADER, BND_HEADER, EMPTY_BLOCK, GZIP_HEADER
from data import p3hash, read_byte_array, read_integer, read_string, to_signed


class BND:
    """
    BND Object
    """
    def __init__(self, data: bytes = [], name: str = "root/", depth: int = 0, encrypted: bool = False, is_folder = False):
        self.file_list = []
        self.name = name
        self.depth = depth
        self.encrypted = encrypted
        self.parent = None

        # Is folder
        self.is_folder = is_folder
        self.is_raw = False
        if self.is_folder: return

        # Gzipped or single BND
        self.is_gzipped = False
        self.is_single_bnd_file = False

        # Default values
        self.add_default_values()

        # Ignore DATAMS.HED
        if name == "datams.hed":
            self.is_raw = True
            self.data = data
        else:
            self.read_from_file(data)
        
        # Print data
        # self.print_data()

    def add_default_values(self):
        """
        Set default values for a BND file
        """
        self.is_raw = False
        self.raw_data = None
        self.version = None
        self.value1 = None
        self.value2 = None
        self.info = None
        self.file = None
        self.entries = None
        self.empty_blocks = None

    def print_data(self):
        print("File: " + self.name)
        for item in self.file_list:
            print(" - Files in folder " + str(item.get_name()) + " : " + str(item.get_file_count()))

    def get_last_folder(self):
        for item in reversed(self.file_list):
            if item.is_folder:
                return item
        return None

    def get_parent(self):
        """
        Add item to file list
        """
        return self.parent

    def get_name(self):
        """
        Return own name
        """
        if self.parent == None:
            return self.name
        else:
            return self.parent.get_name() + self.name

    def get_file_count(self):
        """
        Return file count
        """
        return len(self.file_list)

    def add_to_file_list(self, item: object):
        """
        Add item to file list
        """
        item.set_parent(self)
        self.file_list.append(item)

    def set_parent(self, parent: object):
        self.parent = parent


    def has_parent(self):
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
            is_gzipped = True

            # Check if the resulting file is a BND
            if read_byte_array(data, 0x0, 0x4) != BND_HEADER:

                # Add the simple BND header to the file
                data = BND_FILE_HEADER + data
                is_single_bnd_file = True

        # If header is BND
        if read_byte_array(data, 0x0, 0x4) == BND_HEADER:

            # Read all the header values
            self.version = read_integer(data, 0x04, 0x1)
            self.value1 = read_integer(data, 0x08, 0x1)
            self.value2 = read_integer(data, 0x0C, 0x1)
            self.info = read_integer(data, 0x10, 0x4)
            self.file = read_integer(data, 0x14, 0x4)

            # Checks all the empty blocks
            empty_blocks = 0

            check = EMPTY_BLOCK

            while check == EMPTY_BLOCK:
                check = read_byte_array(data, 0x28 + empty_blocks * 0x10, 0x10)
                if check == EMPTY_BLOCK:
                    empty_blocks += 1

            entries = read_integer(data, 0x24, 0x4) - empty_blocks

            self.empty_blocks = empty_blocks

            # Start reading the data
            offset = 0x0

            # How the file level structure will work
            # # If it increases, create a new folder and continue the loop in there
            # # If it decreases
            current_level = 0
            current_object = self

            for i in range(entries):

                crc_pointer = read_integer(data, self.info + offset + 0x3, 0x4)

                if crc_pointer != 0:
                    # Reads CRC block containing data
                    crc_block = read_byte_array(data, crc_pointer, 0x10)

                    # Reading data from the CRC block
                    pointer_attributes = read_integer(crc_block, 0x4, 0x4) # Address to extra attributes
                    pointer_data = read_integer(crc_block, 0x8, 0x4) # Address to the start of the data
                    file_size = read_integer(crc_block, 0xC, 0x4)  # Size of the data

                    # For DATAMS: File sizes are +0x20000000
                    if file_size >= 0x20000000:
                        file_size -= 0x20000000

                    # Level of the current file (inside folders)
                    file_level = to_signed(read_integer(data, pointer_attributes, 0x1), 1)
                    # Filename
                    file_name = read_string(data, pointer_attributes + 0x7)

                    # Read file data
                    file_data = read_byte_array(data, pointer_data, file_size)  # File data

                    # FILE LEVEL IS ALWAYS FOLDE RLEVEL IN NEGATIVE MINUS ONE
                    # EXAMPLE:
                    # - A file in the root directory will be level -1
                    # - A file in 2 folders will be -3

                    is_change_a_folder = False
                    processed_level = current_level

                    if (file_level < 0):
                        processed_level = abs(file_level) - 1
                    else:
                        processed_level = file_level
                        is_change_a_folder = True

                    # If unequal or new folder, do action
                    if processed_level != current_level or is_change_a_folder:

                        # If level is higher than current one, subfolder must be created
                        if processed_level > current_level:
                            # If level is root, add to root
                            new_folder = BND(None, file_name, processed_level, self.encrypted, True)
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
                        if (is_change_a_folder and processed_level <= current_level):
                            # Back to parent
                            current_object = current_object.get_parent()
                            # Create new folder
                            new_folder = BND(None, file_name, processed_level, self.encrypted, True)
                            # Set to current object
                            current_object.add_to_file_list(new_folder)
                            current_object = new_folder

                        # Set current level
                        current_level = processed_level

                    # Add file
                    if (file_level < 0):
                        current_object.add_to_file_list(BND(file_data, file_name, current_object.depth, self.encrypted))

                    # Add offset
                    offset += 7 + len(file_name) + 1
        
        # If not BND, raw
        else:
            self.is_raw = True
            self.raw_data = data
