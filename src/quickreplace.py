from genericpath import exists

from bnd.bnd import BND


def quick_replace(bnd_file_path, source_file_path, destination):
    """
    Quick BND replacement
    """
    print(
        "Replacing file", destination, "inside", bnd_file_path, "with", source_file_path
    )

    # Check if replacement file exists
    if not exists(source_file_path):
        print("Source file", source_file_path, "doesn't exist")
        return

    # Check if BND file exists
    if not exists(bnd_file_path):
        print("BND file", bnd_file_path, "doesn't exist")
        return

    # Check if destination file is valid
    if destination.endswith("/"):
        print("Destination cannot be a folder")
        return

    # Do stuff
    with open(bnd_file_path, "r+b") as f:
        data = f.read()
        bnd_file = BND(data)
        destination_array = destination.split("/")
        destination_file = bnd_file.get_bundle_from_filename_array(destination_array)

        # Return if destination file not found
        if destination_file == None:
            print("Couldn't find destination file")
            return

        # Replace
        with open(source_file_path, "r+b") as s:
            source_data = s.read()
            destination_file.update_data(source_data)

        # Return to bytes
        data = bnd_file.to_bytes()

    # Write bytes
    with open(bnd_file_path, "wb") as f:
        f.write(data)
