#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from os.path import join as j

from export import FileExport

# from utils import time_to_int


def is_non_zero_file(fpath):
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0


def write_updated_json(infile, outfile, source_path):
    """Write new Bulk Reviewer JSON file with updated source_path.
    """
    with open(infile, "r", encoding="utf-8") as i:
        session_dict = json.load(i)
        session_dict["source_path"] = source_path
        with open(outfile, "w") as o:
            json.dump(session_dict, o)


# class UtilsTest(unittest.TestCase):
#     """Unit tests for utils.
#     """

#     def test_time_to_int_valid_date(self):
#         """Test time_to_int with valid post-1970 date..
#         """
#         time_str = '2019-12-05T12:01:01'
#         self.assertEqual(time_to_int(time_str), 1575547261)

#     def test_time_to_int_pre_1970(self):
#         """Test time_to_int with pre-1970 date.
#         """
#         time_str = '1965-01-01T12:01:01'
#         self.assertEqual(time_to_int(time_str), -157723139)


class SelfCleaningTestCase(unittest.TestCase):
    """TestCase subclass which cleans up self.tmpdir after each test.
    """

    def setUp(self):
        super(SelfCleaningTestCase, self).setUp()

        # tempdir for brunnhilde outputs
        self.tmpdir = tempfile.mkdtemp()
        if not os.path.isdir(self.tmpdir):
            os.mkdirs(self.tmpdir)

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            shutil.rmtree(self.tmpdir)

        super(SelfCleaningTestCase, self).tearDown()


class TestIntegrationProcessor(SelfCleaningTestCase):
    """Main Bulk Reviewer backend integration tests.
    """

    test_data_dir = os.path.abspath(j(os.path.dirname(__file__), "..", "test_data"))

    def test_directory_default(self):
        """Test default settings for directory.
        """
        br_processor_path = os.path.abspath(
            j(os.path.dirname(__file__), "br_processor.py")
        )
        source_dir = j(self.test_data_dir, "source_directory")
        out_dir = j(self.tmpdir, "out")
        cmd = ["python", br_processor_path, source_dir, out_dir, "test"]
        result = subprocess.check_output(cmd)
        # Verify stdout
        json_path = j(out_dir, "test.json")
        self.assertEqual(result.decode("utf-8"), json_path)
        # Verify output dirs and files
        output_dirs = [
            j(out_dir, "test_reports"),
            j(out_dir, "test_reports", "bulk_extractor"),
        ]
        for d in output_dirs:
            self.assertTrue(os.path.isdir(d))
        output_files = [
            json_path,
            j(out_dir, "test_reports", "bulk_extractor", "report.xml"),
            j(out_dir, "test_reports", "bulk_extractor", "pii.txt"),
            j(out_dir, "test_reports", "bulk_extractor", "email.txt"),
        ]
        for f in output_files:
            self.assertTrue(is_non_zero_file(f))
        # Verify contents of JSON match sample
        with open(json_path, "r", encoding="utf-8") as test:
            sample_path = j(self.test_data_dir, "directory.json")
            with open(sample_path, "r", encoding="utf-8") as sample:
                test_dict = json.load(test)
                sample_dict = json.load(sample)
            # Compare file and feature counts against sample
            self.assertEqual(len(test_dict["files"]), len(sample_dict["files"]))
            self.assertEqual(len(test_dict["features"]), len(sample_dict["features"]))

    def test_diskimage_default(self):
        """Test default settings for directory.
        """
        br_processor_path = os.path.abspath(
            j(os.path.dirname(__file__), "br_processor.py")
        )
        source_disk = j(self.test_data_dir, "source_diskimage", "practical.floppy.dd")
        out_dir = j(self.tmpdir, "out")
        cmd = ["python", br_processor_path, "-d", source_disk, out_dir, "test"]
        result = subprocess.check_output(cmd)
        # Verify stdout
        json_path = j(out_dir, "test.json")
        self.assertEqual(result.decode("utf-8"), json_path)
        # Verify output dirs and files
        output_dirs = [
            j(out_dir, "test_reports"),
            j(out_dir, "test_reports", "bulk_extractor"),
            j(out_dir, "test_reports", "bulk_extractor_annotated"),
        ]
        for d in output_dirs:
            self.assertTrue(os.path.isdir(d))
        output_files = [
            json_path,
            j(out_dir, "test_reports", "dfxml.xml"),
            j(out_dir, "test_reports", "bulk_extractor", "report.xml"),
            j(out_dir, "test_reports", "bulk_extractor", "email.txt"),
            j(
                out_dir,
                "test_reports",
                "bulk_extractor_annotated",
                "annotated_domain.txt",
            ),
            j(
                out_dir,
                "test_reports",
                "bulk_extractor_annotated",
                "annotated_email.txt",
            ),
            j(out_dir, "test_reports", "bulk_extractor_annotated", "annotated_url.txt"),
        ]
        for f in output_files:
            self.assertTrue(is_non_zero_file(f))
        # Verify contents of JSON match sample
        with open(json_path, "r", encoding="utf-8") as test:
            sample_path = j(self.test_data_dir, "diskimage.json")
            with open(sample_path, "r", encoding="utf-8") as sample:
                test_dict = json.load(test)
                sample_dict = json.load(sample)
            # Compare file and feature counts against sample
            self.assertEqual(len(test_dict["files"]), len(sample_dict["files"]))
            self.assertEqual(len(test_dict["features"]), len(sample_dict["features"]))


class TestIntegrationExportDirectory(SelfCleaningTestCase):
    """Directory export integration tests.
    """

    test_data_dir = os.path.abspath(j(os.path.dirname(__file__), "..", "test_data"))

    def _setup_directory_test(self):
        """Set up directory integration test and return path to updated JSON.
        """
        source_dir = j(self.test_data_dir, "source_directory")
        json_path = j(self.test_data_dir, "directory.json")
        new_json = j(self.tmpdir, "directory.json")
        write_updated_json(json_path, new_json, source_dir)
        return new_json

    def test_export_directory_cleared(self):
        """Test export of cleared files from directory.
        """
        new_json = self._setup_directory_test()
        out_dir = j(self.tmpdir, "out")
        file_export = FileExport(new_json, out_dir)
        file_export.export_files()
        # Verify cleared files were copied
        cleared = ["file2_nothing.txt", "subdir/file4_nothing.txt"]
        for f in cleared:
            self.assertTrue(is_non_zero_file(j(out_dir, f)))
        # Verify private files were not copied
        private = ["file1_ssn.txt", "subdir/file3_email.txt"]
        for f in private:
            self.assertFalse(is_non_zero_file(j(out_dir, f)))
        # Verify README file written
        self.assertTrue(is_non_zero_file(j(out_dir, "_BulkReviewer_README.txt")))

    def test_export_directory_private(self):
        """Test export of private files from directory.
        """
        new_json = self._setup_directory_test()
        out_dir = j(self.tmpdir, "out")
        file_export = FileExport(new_json, out_dir, False, True)
        file_export.export_files()
        # Verify private files were copied
        private = ["file1_ssn.txt", "subdir/file3_email.txt"]
        for f in private:
            self.assertTrue(is_non_zero_file(j(out_dir, f)))
        # Verify cleared files were not copied
        cleared = ["file2_nothing.txt", "subdir/file4_nothing.txt"]
        for f in cleared:
            self.assertFalse(is_non_zero_file(j(out_dir, f)))
        # Verify README file written
        self.assertTrue(is_non_zero_file(j(out_dir, "_BulkReviewer_README.txt")))

    def test_export_directory_private_flat(self):
        """Test flat export of private files from directory.
        """
        new_json = self._setup_directory_test()
        out_dir = j(self.tmpdir, "out")
        file_export = FileExport(new_json, out_dir, False, True, True)
        file_export.export_files()
        # Verify private files renamed and written to flat dir
        private_flat = ["1_file1_ssn.txt", "4_file3_email.txt"]
        for f in private_flat:
            self.assertTrue(is_non_zero_file(j(out_dir, f)))
        # Verify private files were not copied to original path
        private = ["file1_ssn.txt", "subdir/file3_email.txt"]
        for f in private:
            self.assertFalse(is_non_zero_file(j(out_dir, f)))
        # Verify cleared files were not copied
        cleared = ["file2_nothing.txt", "subdir/file4_nothing.txt"]
        for f in cleared:
            self.assertFalse(is_non_zero_file(j(out_dir, f)))
        # Verify README file written
        self.assertTrue(is_non_zero_file(j(out_dir, "_BulkReviewer_README.txt")))

    def test_directory_tar_exclude(self):
        """Test creation of tar exclude file.
        """
        new_json = self._setup_directory_test()
        exclude_file = j(self.tmpdir, "directory_tar_exclude.txt")
        file_export = FileExport(
            new_json, exclude_file, False, False, False, False, False, True
        )
        file_export.export_files()
        # Verify tar exclude list created
        self.assertTrue(is_non_zero_file(exclude_file))
        # Verify private abspaths and no cleared paths were written to file
        source_dir = j(self.test_data_dir, "source_directory")
        private = [
            j(source_dir, "file1_ssn.txt"),
            j(source_dir, "subdir/file3_email.txt"),
        ]
        cleared = [
            j(source_dir, "file2_nothing.txt"),
            j(source_dir, "subdir/file4_nothing.txt"),
        ]
        with open(exclude_file, "r") as f:
            for line in f:
                self.assertTrue(line.strip() in private)
                self.assertFalse(line.strip() in cleared)


class TestIntegrationExportDiskImage(SelfCleaningTestCase):
    """Disk image export integration tests.
    """

    test_data_dir = os.path.abspath(j(os.path.dirname(__file__), "..", "test_data"))

    def _setup_diskimage_test(self):
        """Set up disk image integration test and return path to updated JSON.
        """
        # Copy source files to tempdir
        source_disk = j(self.test_data_dir, "source_diskimage", "practical.floppy.dd")
        json_path = j(self.test_data_dir, "diskimage.json")
        new_json = j(self.tmpdir, "diskimage.json")
        write_updated_json(json_path, new_json, source_disk)
        return new_json

    def test_export_diskimage_cleared(self):
        """Test export of cleared files from disk image.
        """
        new_json = self._setup_diskimage_test()
        out_dir = j(self.tmpdir, "out")
        file_export = FileExport(new_json, out_dir, True)
        file_export.export_files()
        # Verify cleared files were carved
        cleared = ["Docs/Benchmarks.xls", "FTP.EXE"]
        for f in cleared:
            self.assertTrue(is_non_zero_file(j(out_dir, f)))
        # Verify unallocated file was not carved
        self.assertFalse(is_non_zero_file(j(out_dir, "Docs/Private/ReyHalif.doc")))
        # Verify private file was not carved
        self.assertFalse(is_non_zero_file(j(out_dir, "Docs/Law.doc")))
        # Verify README file written
        self.assertTrue(is_non_zero_file(j(out_dir, "_BulkReviewer_README.txt")))

    def test_export_diskimage_cleared_unallocated(self):
        """Test export of cleared files from disk image with unallocated files.
        """
        new_json = self._setup_diskimage_test()
        out_dir = j(self.tmpdir, "out")
        file_export = FileExport(new_json, out_dir, True, False, False, False, True)
        file_export.export_files()
        # Verify cleared unallocated file was carved
        self.assertTrue(is_non_zero_file(j(out_dir, "Docs/Private/ReyHalif.doc")))
        # Verify private file was not carved
        self.assertFalse(is_non_zero_file(j(out_dir, "Docs/Law.doc")))
        # Verify README file written
        self.assertTrue(is_non_zero_file(j(out_dir, "_BulkReviewer_README.txt")))

    def test_export_diskimage_private(self):
        """Test export of private files from disk image.
        """
        new_json = self._setup_diskimage_test()
        out_dir = j(self.tmpdir, "out")
        file_export = FileExport(new_json, out_dir, True, True)
        file_export.export_files()
        # Verify private file was carved
        self.assertTrue(is_non_zero_file(j(out_dir, "Docs/Law.doc")))
        # Verify cleared files were not carved
        cleared = ["Docs/Benchmarks.xls", "FTP.EXE"]
        for f in cleared:
            self.assertFalse(is_non_zero_file(j(out_dir, f)))
        # Verify README file written
        self.assertTrue(is_non_zero_file(j(out_dir, "_BulkReviewer_README.txt")))

    def test_export_diskimage_private_flat(self):
        """Test flat export of private files from disk image.
        """
        new_json = self._setup_diskimage_test()
        out_dir = j(self.tmpdir, "out")
        file_export = FileExport(new_json, out_dir, True, True, True)
        file_export.export_files()
        # Verify private file was carved with new name to flat dir
        self.assertTrue(is_non_zero_file(j(out_dir, "3_Law.doc")))


if __name__ == "__main__":
    unittest.main()
