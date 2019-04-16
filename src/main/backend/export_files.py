#!/usr/bin/env python3

"""
Exports files from Bulk Reviewer source directory
or disk image.

Takes Bulk Reviewer JSON as input and based on
user-supplied options exports either only files
with confirmed PII or only files clear of private
or otherwise sensitive information.

Tim Walsh, 2019
https://bitarchivist.net
Licensed under GNU General Public License 3
https://www.gnu.org/licenses/gpl-3.0.en.html
"""

import argparse
import json
import os
import shutil
import subprocess


def carve_file(filepath, fs_offset, disk_image, inode, file_dest):
    """
    Carve file from disk image using The Sleuth Kit's
    icat command line utility.
    """
    icat_cmd = 'icat -o {0} "{1}" {2} > "{3}"'.format(
        fs_offset,
        disk_image,
        inode,
        file_dest
    )
    try:
        subprocess.call(icat_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print('Error exporting file {0}: {1}'.format(filepath, e))


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d",
                        "--diskimage",
                        help="Use if source is disk image",
                        action="store_true")
    parser.add_argument("--pii",
                        help="Use to export files with confirmed PII",
                        action="store_true")
    parser.add_argument("json_input",
                        help="Path to JSON file containing feature data")
    parser.add_argument("destination",
                        help="Path to directory to write output files")

    return parser


def main():
    # Parse arguments
    parser = _make_parser()
    args = parser.parse_args()

    # Set varibles
    json_path = os.path.abspath(args.json_input)
    dest_path = os.path.abspath(args.destination)

    # Convert input json to dict
    with open(json_path, 'r') as f:
        session_dict = json.load(f)

    # Delete temp json file
    try:
        os.remove(json_path)
    except OSError:
        print('Unable to delete JSON file')

    # Create list of files with PII
    features = session_dict['features']
    files_with_pii = []
    for f in features:
        if f['cleared'] is False:
            if f['filepath'] not in files_with_pii:
                files_with_pii.append(f['filepath'])

    # Create list of files without PII
    files = session_dict['files']
    files_without_pii = []
    for f in files:
        if f['filepath'] not in files_with_pii:
            files_without_pii.append(f['filepath'])

    # Export files from directory
    if not args.diskimage:

        # Export files without PII, replicating directory structure
        if not args.pii:
            for f in files_without_pii:
                # Build paths for source and dest file
                file_src = os.path.join(session_dict['source_path'], f)
                file_dest = os.path.join(dest_path, f)
                # Copy file, creating dirs if necessary
                os.makedirs(os.path.dirname(file_dest), exist_ok=True)
                try:
                    shutil.copy2(file_src, file_dest)
                except OSError as e:
                    print('Error copying file {1}: {2}'.format(file_src, e))
            print('Files without PII copied to {}'.format(dest_path))
            return

        # Export files with PII to flat directory
        for f in files_with_pii:
            # Get file information
            filtered_files = [x for x in files if x['filepath'] == f]
            file_info = filtered_files[0]
            # Build path for source file
            file_src = os.path.join(session_dict['source_path'], f)
            # Build path for destination file, appending
            # ID to filename to prevent filepath collisions
            file_basename = str(file_info['id']) + '_' + os.path.basename(f)
            file_dest = os.path.join(dest_path, file_basename)
            # Copy file
            try:
                shutil.copy2(file_src, file_dest)
            except OSError as e:
                print('Error copying file {1}: {2}'.format(file_src, e))

        print('Files with PII copied to {}'.format(dest_path))
        return

    # Export files from disk image

    # Export files without PII, replicating directory structure
    if not args.pii:
        for f in files_without_pii:
            # Build path for destination file
            file_dest = os.path.join(dest_path, f)
            # Create intermediate dirs if necessary
            os.makedirs(os.path.dirname(file_dest), exist_ok=True)
            # Get file information
            filtered_files = [x for x in files if x['filepath'] == f]
            file_info = filtered_files[0]
            # TODO: CHECK IF FILE IS ALLOCATED
            # Carve file from disk image
            carve_file(f,
                       int(file_info['fs_offset']),
                       session_dict['source_path'],
                       int(file_info['inode']),
                       file_dest)
            # TODO: RESTORE FS DATES FROM VALUES RECORDED IN DFXML
        print('Files without PII copied to {}'.format(dest_path))
        return

    # Export files with PII to flat directory
    for f in files_with_pii:
        # Get file information
        filtered_files = [x for x in files if x['filepath'] == f]
        file_info = filtered_files[0]
        # Build path for destination file, appending
        # ID to filename to prevent filepath collisions
        file_basename = str(file_info['id']) + '_' + os.path.basename(f)
        file_dest = os.path.join(dest_path, file_basename)
        # Create intermediate dirs if necessary
        os.makedirs(os.path.dirname(file_dest), exist_ok=True)
        # TODO: CHECK IF FILE IS ALLOCATED
        # Carve file from disk image
        carve_file(f,
                   int(file_info['fs_offset']),
                   session_dict['source_path'],
                   int(file_info['inode']),
                   file_dest)
        # TODO: RESTORE FS DATES FROM VALUES RECORDED IN DFXML
    print('Files with PII copied to {}'.format(dest_path))
    return


if __name__ == '__main__':
    main()
