#!/usr/bin/env python3

"""
Bulk Reviewer
---
File export and disk image carving module

Tim Walsh, 2019
https://bitarchivist.net
Licensed under GNU General Public License 3
https://www.gnu.org/licenses/gpl-3.0.en.html
"""

from datetime import datetime
import json
import logging
import os
import shutil
import subprocess
import sys

from utils import print_to_stderr_and_exit, time_to_int


class FileExport:
    """Class representing Bulk Reviewer export.
    """

    def __init__(
        self,
        json_path,
        destination,
        disk_image=False,
        private=False,
        flat=False,
        restore_dates=False,
        export_unallocated=False,
        tar_list=False,
        session_dict=dict(),
        files_with_pii=list(),
        files_without_pii=list(),
        files_not_copied=list(),
    ):
        self.json_path = json_path
        self.destination = destination
        self.disk_image = disk_image
        self.private = private
        self.flat = flat
        self.restore_dates = restore_dates
        self.export_unallocated = export_unallocated
        self.tar_list = tar_list
        self.session_dict = session_dict
        self.files_with_pii = files_with_pii
        self.files_without_pii = files_without_pii
        self.files_not_copied = files_not_copied

    def export_files(self):
        """Handle file export.
        """
        self._load_from_json()

        features = self.session_dict["features"]
        for f in features:
            if f["dismissed"] is False:
                if f["filepath"] not in self.files_with_pii:
                    self.files_with_pii.append(f["filepath"])

        files = self.session_dict["files"]
        for f in files:
            if f["filepath"] not in self.files_with_pii:
                self.files_without_pii.append(f["filepath"])

        # If tar option selected, create tar exclude file and exit
        if self.tar_list:
            # Skip if disk image
            if not self.disk_image:
                self._create_tar_exclude_file()

        if self.disk_image:
            if self.private:
                self._export_files_private_diskimage()
            else:
                self._export_files_cleared_diskimage()
        else:
            if self.private:
                self._export_files_private_directory()
            else:
                self._export_files_cleared_directory()

        self._write_readme()
        self._report_status()

    def _load_from_json(self):
        """Save Bulk Reviewer JSON data to session_dict.

        Attempt to delete temp JSON file after read.
        """
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.session_dict = json.load(f)
        try:
            os.remove(self.json_path)
        except OSError:
            logging.warning("Unable to delete JSON file %s", self.json_path)

    def _create_tar_exclude_file(self):
        """Create TAR exclude file and exit with code 0.

        File includes absolute path to each file containing PII.
        Each entry is written on its own line.
        """
        try:
            with open(self.destination, "w") as f:
                for private_file in self.files_with_pii:
                    private_filepath = os.path.join(
                        self.session_dict["source_path"], private_file
                    )
                    f.write(private_filepath + "\n")
            logging.info("Created tar exclude file %s", str(self.destination))
            print("Tar exclude file written to {}".format(str(self.destination)))
            sys.exit(0)
        except Exception as e:
            logging.error(
                "Unable to create tar exclude file %s. Details: %s",
                str(self.destination),
                e,
            )
            print_to_stderr_and_exit(
                "Unable to create tar exclude file %s.", str(self.destination)
            )

    def _export_files_private_diskimage(self):
        """Export private files from disk image.
        """
        files = self.session_dict["files"]
        for f in self.files_with_pii:
            # Get file information
            filtered_files = [x for x in files if x["filepath"] == f]
            file_info = filtered_files[0]
            # Build path for destination file
            if self.flat:
                # Append ID to filename to prevent filepath collisions
                file_basename = str(file_info["id"]) + "_" + os.path.basename(f)
                file_dest = os.path.join(self.destination, file_basename)
            else:
                file_dest = os.path.join(self.destination, f)
            # Skip unallocated files unless args.unallocated is True
            if self.export_unallocated is not True:
                if file_info["allocated"] is False:
                    continue
            # Create intermediate dirs if necessary
            os.makedirs(os.path.dirname(file_dest), exist_ok=True)
            # Carve file from disk image
            carve_success = self._carve_file(
                f,
                int(file_info["fs_offset"]),
                self.session_dict["source_path"],
                int(file_info["inode"]),
                file_dest,
            )
            if carve_success is False:
                self.files_not_copied.append(file_dest)
            # Set modified date to modified or created value from DFXML
            if self.restore_dates:
                self._restore_modified_date(
                    file_dest, file_info["date_modified"], file_info["date_created"]
                )
        logging.info("Files with PII copied to %s", self.destination)

    def _export_files_cleared_diskimage(self):
        """Export cleared files from disk image.
        """
        files = self.session_dict["files"]
        for f in self.files_without_pii:
            # Build path for destination file
            file_dest = os.path.join(self.destination, f)
            # Get file information
            filtered_files = [x for x in files if x["filepath"] == f]
            file_info = filtered_files[0]
            # Skip unallocated files unless args.unallocated is True
            if self.export_unallocated is not True:
                if file_info["allocated"] is False:
                    continue
            # Create intermediate dirs if necessary
            os.makedirs(os.path.dirname(file_dest), exist_ok=True)
            # Carve file from disk image
            carve_success = self._carve_file(
                f,
                int(file_info["fs_offset"]),
                self.session_dict["source_path"],
                int(file_info["inode"]),
                file_dest,
            )
            if carve_success is False:
                self.files_not_copied.append(file_dest)
            # Set modified date to modified or created value from DFXML
            if self.restore_dates:
                self._restore_modified_date(
                    file_dest, file_info["date_modified"], file_info["date_created"]
                )
        logging.info("Files without PII copied to %s", self.destination)

    def _export_files_private_directory(self):
        """Export private files from directory.
        """
        files = self.session_dict["files"]
        for f in self.files_with_pii:
            # Get file information
            filtered_files = [x for x in files if x["filepath"] == f]
            file_info = filtered_files[0]
            # Build path for source file
            file_src = os.path.join(self.session_dict["source_path"], f)
            # Build path for destination file
            if self.flat:
                # Append ID to filename to prevent filepath collisions
                file_basename = str(file_info["id"]) + "_" + os.path.basename(f)
                file_dest = os.path.join(self.destination, file_basename)
            else:
                file_dest = os.path.join(self.destination, f)
            os.makedirs(os.path.dirname(file_dest), exist_ok=True)
            # Copy file
            try:
                shutil.copy2(file_src, file_dest)
            except OSError as e:
                logging.error("Error copying file %s: %s", file_src, e)
                self.files_not_copied.append(file_src)
        logging.info("Files with PII copied to %s", self.destination)

    def _export_files_cleared_directory(self):
        """Export cleared files from directory.
        """
        for f in self.files_without_pii:
            # Build paths for source and dest file
            file_src = os.path.join(self.session_dict["source_path"], f)
            file_dest = os.path.join(self.destination, f)
            # Copy file, creating dirs if necessary
            os.makedirs(os.path.dirname(file_dest), exist_ok=True)
            try:
                shutil.copy2(file_src, file_dest)
            except OSError as e:
                logging.error("Error copying file %s: %s", file_src, e)
                self.files_not_copied.append(file_src)
        logging.info("Cleared files copied to %s", self.destination)

    def _write_readme(self):
        """Write README file in output directory for file export.
        Include metadata about the session and export.
        """
        out_file = os.path.join(self.destination, "_BulkReviewer_README.txt")
        time_of_export = str(datetime.now())[:19]
        source_type = "Directory"
        if self.session_dict["disk_image"] is True:
            source_type = "Disk image"
        export_type = "Cleared files"
        if self.private:
            export_type = "Private files"

        flat_faq = """\n\nFiles in this export have been flattened into a \
single directory to support redaction workflows. In order to prevent name \
collisions, each file's unique ID (as assigned by Bulk Reviewer) is added to \
the beginning of the filename on export. These IDs can be matched to original \
filepaths and corresponding features using the Bulk Reviewer CSV export.
        """

        try:
            with open(out_file, "w") as f:
                # Write metadata
                f.write("Files exported from Bulk Reviewer")
                f.write("\n================================")
                f.write("\nType: {}".format(export_type))
                f.write("\nDate: {}".format(time_of_export))
                f.write("\nSource: {}".format(self.session_dict["source_path"]))
                f.write("\nSource type: {}".format(source_type))
                # Include disk image file export options
                if source_type == "Disk image":
                    dates = str(self.restore_dates)
                    unalloc = str(self.export_unallocated)
                    f.write("\nModified dates restored: {}".format(dates))
                    f.write("\nUnallocated files included: {}".format(unalloc))

                # For cleared export, write list of excluded files
                if not self.private:
                    f.write("\n\nFiles excluded from export for containing PII:")
                    for pii_file in self.files_with_pii:
                        f.write("\n{}".format(pii_file))

                # Add section explaining flat outputs
                if self.flat:
                    f.write(flat_faq)

            logging.info("Created export README file %s", out_file)

        except Exception as e:
            logging.warning(
                "Unable to create export README file %s. Details: %s", out_file, e
            )

    def _report_status(self):
        """Report status of export back to user by printing to stdout.

        Include list of files that were unable to be copied or carved
        if applicable.
        """
        #
        logging.info("Export complete")
        if not self.files_not_copied:
            if self.private:
                print(
                    "Private files successfully exported to directory", self.destination
                )
            else:
                print(
                    "Cleared files successfully exported to directory", self.destination
                )
            return

        # If errors with copying/carving files, print list of specific files
        if self.private:
            print(
                """
                Private files exported to directory %s.
                The following files encountered errors: %s.
                See Bulk Reviewer log for details.
                """.strip(),
                self.destination,
                ", ".join(self.files_not_copied),
            )
        else:
            print(
                """
                Cleared files exported to directory %s.
                The following files encountered errors: %s.
                See Bulk Reviewer log for details.
                """.strip(),
                self.destination,
                ", ".join(self.files_not_copied),
            )

    @staticmethod
    def _carve_file(filepath, fs_offset, disk_image, inode, file_dest):
        """Carve file from disk image using icat.

        Return True is successful, False if not.
        """
        icat_cmd = 'icat -o {0} "{1}" {2} > "{3}"'.format(
            fs_offset, disk_image, inode, file_dest
        )
        try:
            subprocess.call(icat_cmd, shell=True)
            logging.debug("File %s exported from disk image", filepath)
            return True
        except subprocess.CalledProcessError as e:
            logging.error("Error exporting file %s: %s", filepath, e)
            return False

    @staticmethod
    def _restore_modified_date(file_dest, date_modified, date_created):
        """Rewrite last modified date of file.

        Use date modified if exists, otherwise use date created.
        """
        if len(date_modified) > 0:
            int_time = time_to_int(date_modified[:19])
        elif len(date_created) > 0:
            int_time = time_to_int(date_created[:19])
        else:
            logging.warning("No date to restore from recorded for file %s", file_dest)
            return

        try:
            os.utime(file_dest, (int_time, int_time))
        except OSError as e:
            logging.warning(
                "Error modifying modified date for %s. Error: %s", file_dest, e
            )
