#!/usr/bin/env python3

"""
Bulk Reviewer
---
Creates Bulk Reviewer JSON file and DFXML
and bulk_extractor output directories for input
directory or disk image.

Tessa Walsh, 2019-2020
https://bitarchivist.net
Licensed under GNU General Public License 3
https://www.gnu.org/licenses/gpl-3.0.en.html
"""

from sqlalchemy import create_engine, func, Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
import argparse
import bisect
import bulk_extractor_reader
import fiwalk
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import Objects

from export import FileExport
from utils import print_to_stderr_and_exit


Base = declarative_base()
xor_re = re.compile(b"^(\\d+)\\-XOR\\-(\\d+)")

FEATURE_LABELS = {
    "pii.txt": "Social Security Number (USA)",
    "sin.txt": "Social Insurance Number (Canada)",
    "ccn.txt": "Credit card number",
    "telephone.txt": "Phone number",
    "email.txt": "Email address",
    "find.txt": "Regular expression",
    "lightgrep.txt": "Regular expression",
    "url.txt": "URL",
    "domain.txt": "Domain",
    "rfc822.txt": "Email/HTTP header (RFC822)",
    "httplogs.txt": "HTTP log",
    "gps.txt": "GPS data",
    "exif.txt": "EXIF metadata",
    "vcard.txt": "vCard (Virtual Contact File)",
}


class BRSession(Base):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    source_path = Column(String)
    disk_image = Column(Boolean)
    named_entity_extraction = Column(Boolean)
    regex_file = Column(String, nullable=True)
    ssn_mode = Column(Integer)


class File(Base):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    filepath = Column(String)
    date_modified = Column(String(50), nullable=True)
    date_created = Column(String(50), nullable=True)
    note = Column(String, nullable=True)
    allocated = Column(Boolean)
    verified = Column(Boolean)
    inode = Column(String, nullable=True)
    fs_offset = Column(String, nullable=True)
    session = Column(Integer, ForeignKey("session.id"))


class Feature(Base):
    __tablename__ = "feature"
    id = Column(Integer, primary_key=True)
    feature_type = Column(String(50))
    forensic_path = Column(String, nullable=True)
    offset = Column(String, nullable=True)
    feature = Column(String)
    context = Column(String, nullable=True)
    note = Column(String, nullable=True)
    dismissed = Column(Boolean)
    file = Column(Integer, ForeignKey("file.id"))


class byterundb:
    """
    The byte run database holds a set of byte runs, sorted by the
    start byte. It can be searched to find the name of a file that
    corresponds to a byte run.

    Class slightly modified from:
    https://github.com/simsong/bulk_extractor/blob/
    master/python/identify_filenames.py
    """

    def __init__(self):
        self.rary = []  # each element is (runstart,runend,(fileinfo))
        self.sorted = True  # whether or not sorted

    def __iter__(self):
        return self.rary.__iter__()

    def __len__(self):
        return len(self.rary)

    def dump(self):
        for e in self.rary:
            print(e)

    def add_extent(self, offset, length, fileinfo):
        """Add the extent the array, but fix any invalid arguments"""
        if type(offset) != int or type(length) != int:
            return
        self.rary.append((offset, offset + length, fileinfo))
        self.sorted = False

    def search_offset(self, pos):
        """Return the touple associated with a offset"""
        if self.sorted is False:
            self.rary.sort()
            self.sorted = True

        p = bisect.bisect_left(self.rary, ((pos, 0, "")))

        # If the offset matches the first byte in the returned byte run,
        # we have found the matching exten
        try:
            if self.rary[p][0] == pos:
                return self.rary[p]
        except IndexError:
            pass

        # If the first element in the array was found, all elements are to the
        # right of the provided offset, so there is no byte extent that maches.

        if p == 0:
            return None

        # Look at the byte extent whose origin is to the left
        # of pos. If the extent includes pos, return it, otherwise
        # return None
        if self.rary[p - 1][0] <= pos < self.rary[p - 1][1]:
            return self.rary[p - 1]

        return None

    def process_fi(self, fi):
        """Read an XML file and add each byte run to this database"""

        def gval(x):
            """Always return X as bytes"""
            if x is None:
                return b""
            if type(x) == bytes:
                return x
            if type(x) != str:
                x = str(x)
            return x.encode("utf-8")

        for run in fi.byte_runs():
            try:
                fname = gval(fi.filename())
                md5val = gval(fi.md5())
                if not fi.allocated():
                    fname = b"*" + fname
                fileinfo = (fname, md5val)
                self.add_extent(run.img_offset, run.len, fileinfo)
            except TypeError as e:
                pass


class byterundb2:
    """
    Maintain two byte run databases, one for allocated files,
    one for unallocated files.

    Class slightly modified from:
    https://github.com/simsong/bulk_extractor/blob/
    master/python/identify_filenames.py
    """

    def __init__(self):
        self.allocated = byterundb()
        self.unallocated = byterundb()
        self.filecount = 0

    def __len__(self):
        return len(self.allocated) + len(self.unallocated)

    def process(self, fi):
        if fi.allocated():
            self.allocated.process_fi(fi)
        else:
            self.unallocated.process_fi(fi)
        self.filecount += 1
        # if self.filecount % 1000 == 0:
        #     print("Processed %d fileobjects in DFXML file" % self.filecount)

    def read_xmlfile(self, fname):
        # print("Reading file map from XML file {}".format(fname))
        fiwalk.fiwalk_using_sax(xmlfile=open(fname, "rb"), callback=self.process)

    def read_imagefile(self, fname):
        fiwalk_args = "-zM"
        # print("Reading file map by running fiwalk on {}".format(fname))
        fiwalk.fiwalk_using_sax(
            imagefile=open(fname, "rb"), callback=self.process, fiwalk_args=fiwalk_args
        )

    def search_offset(self, offset):
        """
        First search the allocated. If there is nothing, search unallocated
        """
        r = self.allocated.search_offset(offset)
        if not r:
            r = self.unallocated.search_offset(offset)
        return r

    def path_to_offset(self, offset):
        """If the path has an XOR transformation, add the offset within
        the XOR to the initial offset. Otherwise don't. Return the integer
        value of the offset."""
        m = xor_re.search(offset)
        if m:
            return int(m.group(1)) + int(m.group(2))
        negloc = offset.find(b"-")
        if negloc == -1:
            return int(offset)
        return int(offset[0:negloc])

    def search_path(self, path):
        return self.search_offset(self.path_to_offset(path))

    def dump(self):
        # print("Allocated:")
        self.allocated.dump()
        # print("Unallocated:")
        self.unallocated.dump()


def create_dfxml(src, dfxml_path):
    """
    Create DFXML representation of source disk image using fiwalk
    and save to destination directory. Return True is successful,
    False if unsuccessful.
    """
    cmd = ["fiwalk", "-X", dfxml_path, src]
    try:
        subprocess.check_output(cmd)
        return True
    except subprocess.CalledProcessError as e:
        logging.error("Error creating DFXML with fiwalk: %s", e)
        return False


def run_bulk_extractor(src, bulk_extractor_path, stoplist_dir, ssn_mode, args):
    """
    Create and run bulk_extractor subprocess command.
    """
    cmd = [
        "bulk_extractor",
        "-o",
        bulk_extractor_path,
        "-x",
        "windirs",
        "-x",
        "winpe",
        "-x",
        "winlnk",
        "-x",
        "winprefetch",
        "-S",
        "ssn_mode={}".format(str(ssn_mode)),
        "-S",
        "jpeg_carve_mode=0",
        src,
    ]
    if not args.diskimage:
        cmd.insert(15, "-R")
    if args.regex:
        cmd.insert(1, "-F")
        cmd.insert(2, args.regex)
    if args.stoplists:
        # Add each .txt file found in stoplist dir to cmd
        stoplist_files = os.listdir(stoplist_dir)
        for f in stoplist_files:
            if f.endswith(".txt"):
                cmd.insert(5, "-w")
                cmd.insert(6, os.path.join(stoplist_dir, f))

    try:
        subprocess.check_output(cmd)
        return True
    except subprocess.CalledProcessError as e:
        logging.error("Error running bulk_extractor: %s", e)
        return False


def parse_dfxml_to_db(session, br_session_id, dfxml_path):
    """
    Write database entry for each regular file
    recorded in DFXML file.
    """

    # Gather info for each FileObject and save to db
    for (event, obj) in Objects.iterparse(dfxml_path):

        # Only work on FileObjects
        if not isinstance(obj, Objects.FileObject):
            continue

        # Skip directories and links
        if obj.name_type:
            if obj.name_type != "r":
                continue

        # Gather file metadata
        date_modified = ""
        if obj.mtime:
            date_modified = str(obj.mtime)
        date_created = ""
        if obj.crtime:
            date_created = str(obj.crtime)
        if obj.ctime:
            date_created = str(obj.ctime)
        allocated = True
        if obj.unalloc:
            if obj.unalloc == 1:
                allocated = False
        inode = ""
        if obj.inode:
            inode = str(obj.inode)
        fs_offset = ""
        if obj.volume_object:
            fs_offset = obj.volume_object.partition_offset

        # Save file metadata to model
        filepath = obj.filename
        filename = os.path.basename(filepath)
        new_file = File(
            filepath=filepath,
            filename=filename,
            session=br_session_id,
            date_modified=date_modified,
            date_created=date_created,
            allocated=allocated,
            inode=inode,
            fs_offset=fs_offset,
            verified=False,
        )
        try:
            session.add(new_file)
            session.commit()
        except Exception as e:
            logging.error("File %s not written to database: %s", filepath, e)


def write_filesystem_metadata_to_db(session, br_session_id, src):
    """
    Recursively walk filesystem of src and write
    metadata for each file to database.
    """
    for root, dirs, files in os.walk(src):
        for f in files:
            # Filepath
            fpath = os.path.join(root, f)
            rel_fpath = os.path.relpath(fpath, start=src)
            abs_fpath = os.path.abspath(fpath)

            # Modified date
            file_info = os.stat(abs_fpath)
            date_modified = ""
            if file_info.st_mtime:
                date_modified = datetime.utcfromtimestamp(
                    file_info.st_mtime
                ).isoformat()

            # Save file metadata to model
            new_file = File(
                filepath=rel_fpath,
                filename=f,
                session=br_session_id,
                date_modified=date_modified,
                date_created="",
                allocated=True,
                inode="",
                fs_offset="",
                verified=False,
            )
            try:
                session.add(new_file)
                session.commit()
            except Exception as e:
                logging.error("File %s not written to database: %s", rel_fpath, e)


def process_featurefile2(rundb, infile, outfile):
    """
    Returns features from infile, determines the file for each,
    writes results to outfile.

    Slightly modified from:
    https://github.com/simsong/bulk_extractor/blob/
    master/python/identify_filenames.py
    """
    # Stats
    unallocated_count = 0
    feature_count = 0
    features_encoded = 0
    located_count = 0

    outfile.write(b"# Position\tFeature")
    outfile.write(b"\tContext")
    outfile.write(b"\tFilename\tMD5")
    outfile.write(b"\n")
    t0 = time.time()
    linenumber = 0
    for line in infile:
        linenumber += 1
        if bulk_extractor_reader.is_comment_line(line):
            outfile.write(line)
            continue
        try:
            (path, feature, context) = line[:-1].split(b"\t")
        except ValueError as e:
            logging.error("Error annotating feature file: %s", e)
            logging.error("Offending line %s: %s", linenumber, line[:-1])
            continue
        feature_count += 1

        # Increment counter if this feature was encoded
        if b"-" in path:
            features_encoded += 1

        # Search for feature in database
        tpl = rundb.search_path(path)

        # Output to annotated feature file
        outfile.write(path)
        outfile.write(b"\t")
        outfile.write(feature)
        outfile.write(b"\t")
        outfile.write(context)

        # If we found the data, output that
        if tpl:
            located_count += 1
            outfile.write(b"\t")
            outfile.write(b"\t".join(tpl[2]))  # just the file info
        else:
            unallocated_count += 1
        outfile.write(b"\n")

    t1 = time.time()
    for (title, value) in [
        ["# Total features input: {}", feature_count],
        ["# Total features located to files: {}", located_count],
        ["# Total features in unallocated space: {}", unallocated_count],
        ["# Total features in encoded regions: {}", features_encoded],
        ["# Total processing time: {:.2} seconds", t1 - t0],
    ]:
        outfile.write((title + "\n").format(value).encode("utf-8"))
    return (feature_count, located_count)


def annotate_feature_files(feature_files_dir, annotated_feature_path, dfxml_path):
    """
    Annotate bulk_extractor feature files for disk images
    to associate features to files in the image.

    Based on:
    https://github.com/simsong/bulk_extractor/blob/
    master/python/identify_filenames.py
    """
    # Make directory for annotated feature files
    if not os.path.exists(annotated_feature_path):
        os.makedirs(annotated_feature_path)

    # Read bulk_extractor report and DFXML file
    rundb = byterundb2()
    report = bulk_extractor_reader.BulkReport(feature_files_dir)
    rundb.read_xmlfile(dfxml_path)
    if len(rundb) == 0:
        raise RuntimeError(
            "\nERROR: No files detected in XML file {}\n".format(dfxml_path)
        )

    # Process each feature file
    feature_file_list = report.feature_files()
    try:
        feature_file_list.remove("tcp.txt")  # not needed
    except ValueError:
        pass
    for feature_file in feature_file_list:
        output_fn = os.path.join(annotated_feature_path, ("annotated_" + feature_file))
        if os.path.exists(output_fn):
            raise RuntimeError(output_fn + " exists")
        # print("feature_file:", feature_file)
        (feature_count, located_count) = process_featurefile2(
            rundb, report.open(feature_file, mode="rb"), open(output_fn, "wb")
        )


def check_for_lightgrep(be_files):
    """Return True if lightgrep file in bulk_extractor outputs.
    """
    filtered_lightgrep = [x for x in be_files if "lightgrep" in x]
    if filtered_lightgrep:
        return True
    return False


def read_features_to_db(feature_files_dir, br_session_id, session, args):
    """
    Read information from appropriate feature files
    into database, adding feature type.
    """
    be_files = os.listdir(feature_files_dir)
    for feature_file in be_files:
        # Absolute path for file
        ff_abspath = os.path.join(feature_files_dir, feature_file)
        # Skip empty files
        if not os.path.getsize(ff_abspath) > 0:
            continue
        # Skip directories
        if os.path.isdir(ff_abspath):
            continue
        # Skip bulk_extractor report
        if "report.xml" in feature_file:
            continue
        # Skip histograms
        if "histogram" in feature_file:
            continue
        if "url_" in feature_file:
            continue
        # Skip zip-related files
        if "zip" in feature_file:
            continue
        # Skip json
        if "json" in feature_file:
            continue
        # Skip hex
        if "hex" in feature_file:
            continue
        # Skip stoplist results
        if "_stopped" in feature_file:
            continue
        # Skip find if lightgrep enabled
        lightgrep = check_for_lightgrep(be_files)
        if lightgrep:
            if "find" in feature_file:
                continue
        # Skip network/web results unless args specify otherwise
        if not args.include_network:
            if "url" in feature_file:
                continue
            if "domain" in feature_file:
                continue
            if "rfc822" in feature_file:
                continue
        # Skip EXIF results unless args specify otherwise
        if not args.include_exif:
            if "exif" in feature_file:
                continue
        # Parse file and write features into db
        if args.diskimage:
            parse_annotated_feature_file(ff_abspath, br_session_id, session)
        else:
            parse_feature_file(ff_abspath, br_session_id, session)


def parse_feature_file(feature_file, br_session_id, session):
    """Write features from bulk_extractor feature file to the database

    Feature files can be encoded in one of several character encodings.
    We read the input file as bytes and get valid Unicode for each line
    wihout UnicodeDecodeErrors with the help bulk_extractor_reader's
    decode_feature helper.
    """
    with open(feature_file, "rb") as f:
        for line in f:
            line = bulk_extractor_reader.decode_feature(line)

            # Ignore commented lines
            if line.startswith("#"):
                continue
            # Ignore blank lines
            if not line.strip():
                continue

            # Parse and clean up tab-separated lines
            DELIMITER = "\U0010001c"
            forensic_path = ""
            filepath = ""
            feature = ""
            context = ""
            try:
                (forensic_path, feature, context) = line.split("\t")
                filepath = forensic_path
                if DELIMITER in forensic_path:
                    filepath = forensic_path.split(DELIMITER)[0]
                context = context.rstrip()  # strip trailing newline

                # Make filepath relative to match DFXML filename
                source_path = session.query(BRSession).get(br_session_id).source_path
                parent_dir = os.path.split(source_path)[1] + "/"
                filepath = filepath.replace("//", "/").split(parent_dir)[1]

                # Find matching file
                try:
                    matching_file = (
                        session.query(File)
                        .filter_by(filepath=filepath, session=br_session_id)
                        .first()
                    )
                except NoResultFound:
                    logging.error(
                        """
                        Matching file not found for file %s.
                        """,
                        filepath,
                    )
                    continue

                # Set feature type
                ff_basename = os.path.basename(feature_file)
                try:
                    feature_type = FEATURE_LABELS[ff_basename]
                except KeyError:
                    feature_type = ff_basename

                # Write feature to database
                postprocessed_feature = Feature(
                    feature_type=feature_type,
                    forensic_path=forensic_path,
                    feature=feature,
                    context=context,
                    dismissed=False,
                    file=matching_file.id,
                )
                session.add(postprocessed_feature)
                session.commit()
            except Exception:
                logging.warning(
                    """Error processing line in feature file %s. Unread line: %s.\
                    """,
                    feature_file,
                    line,
                )


def parse_annotated_feature_file(feature_file, br_session_id, session):
    """Write features from annotated feature file to the database

    Annotated feature files contain information about filepaths that is
    otherwise missing from feature files describing disk images.

    Annotated feature files are written as UTF-8 so we shouldn't get
    UnicodeDecodeErrors, but handle errors with surrogateescape just to
    be safe.
    """
    with open(feature_file, "r", encoding="utf-8", errors="surrogateescape") as f:
        for line in f:
            # Ignore commented lines
            if line.startswith(("#")):
                continue
            # Ignore blank lines
            if not line.strip():
                continue

            # Parse tab-separated lines
            try:

                # Assume 5 values in annotated line
                try:
                    (offset, feature, context, filepath, blockhash) = line.split("\t")

                # Catch ValueError when line only has 3
                except ValueError:
                    (offset, feature, context) = line.split("\t")
                    filepath = "<unallocated space>"

                # Try to find matching file
                try:
                    matching_file = (
                        session.query(File)
                        .filter_by(filepath=filepath, session=br_session_id)
                        .one()
                    )

                # If matching file doesn't exist, match to placeholder
                except NoResultFound:

                    # Use placeholder if it already exists
                    try:
                        matching_file = (
                            session.query(File)
                            .filter_by(
                                filepath="<unallocated space>", session=br_session_id
                            )
                            .one()
                        )

                    # Create and use placeholder if it doesn't already exist
                    except NoResultFound:
                        unallocated_placeholder = File(
                            filepath="<unallocated space>",
                            filename="<unallocated space>",
                            allocated=False,
                            session=br_session_id,
                        )
                        session.add(unallocated_placeholder)
                        session.commit()
                        matching_file = (
                            session.query(File)
                            .filter_by(
                                filepath="<unallocated space>", session=br_session_id
                            )
                            .one()
                        )

                # Set feature type
                ff_basename = os.path.basename(feature_file).replace("annotated_", "")
                try:
                    feature_type = FEATURE_LABELS[ff_basename]
                except KeyError:
                    feature_type = ff_basename

                # Write feature to database
                postprocessed_feature = Feature(
                    feature_type=feature_type,
                    offset=offset,
                    feature=feature,
                    context=context.rstrip(),
                    dismissed=False,
                    file=matching_file.id,
                )
                session.add(postprocessed_feature)
                session.commit()

            except Exception:
                logging.warning(
                    """Error processing line in feature file %s. Unread line: %s.\
                    """,
                    feature_file,
                    line,
                )


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def brv_to_json(brv_path, json_path):
    """
    Write output file containing JSON representation
    of information in input .brv Bulk Reviewer database.
    """

    # Open db connection and get cursor
    conn = sqlite3.connect(brv_path)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    # SessionInfo
    session_info = dict()
    files = []
    features = []

    # Fetch session data from sqlite db and save to dictionary
    cursor.execute("SELECT * from session;")
    session_info = cursor.fetchone()

    # Add files to dictionary
    files_sql_query = """\
        SELECT fl.*, \
        (SELECT COUNT(*) from feature f where f.file = fl.id) \
            as feature_count \
        from file fl
        WHERE session='{}';
        """.format(
        session_info["id"]
    )
    cursor.execute(files_sql_query)
    files = cursor.fetchall()
    session_info["files"] = files

    # Add features to dictionary with filepaths
    features_sql_query = """\
        SELECT f.id, f.feature_type, f.forensic_path, \
            f.offset, f.feature, f.context, f.note, \
            f.dismissed, f.file, fl.filepath
        from feature f, file fl
        WHERE f.file = fl.id
        """.format(
        session_info["id"]
    )
    cursor.execute(features_sql_query)
    features = cursor.fetchall()
    session_info["features"] = features

    # Replace sqlite integer boolean values in dict with Python booleans
    if session_info["disk_image"] == 1:
        session_info["disk_image"] = True
    else:
        session_info["disk_image"] = False

    if session_info["named_entity_extraction"] == 1:
        session_info["named_entity_extraction"] = True
    else:
        session_info["named_entity_extraction"] = False

    for index, file_dict in enumerate(session_info["files"]):
        if file_dict["allocated"] == 1:
            session_info["files"][index]["allocated"] = True
        else:
            session_info["files"][index]["allocated"] = False

        if file_dict["verified"] == 1:
            session_info["files"][index]["verified"] = True
        else:
            session_info["files"][index]["verified"] = False

    for index, feature_dict in enumerate(session_info["features"]):
        if feature_dict["dismissed"] == 1:
            session_info["features"][index]["dismissed"] = True
        else:
            session_info["features"][index]["dismissed"] = False

    # Write dictionary as JSON to file
    with open(json_path, "w", encoding="utf-8", errors="ignore") as outfile:
        return json.dump(session_info, outfile, ensure_ascii=False, indent=2)

    # Close sqlite connection
    cursor.close()
    conn.close()


def _configure_logging(bulk_reviewer_dir):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = logging.FileHandler(
        os.path.join(bulk_reviewer_dir, "bulk-reviewer.log"), "a", "utf-8"
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", help="", action="store_true")
    parser.add_argument(
        "-d", "--diskimage", help="Scan disk image", action="store_true"
    )
    parser.add_argument(
        "--ssn",
        help="Specify Bulk Extractor ssn_mode (0, 1, or 2)",
        action="store",
        type=int,
    )
    parser.add_argument(
        "--include_exif", help="Include EXIF metadata in results", action="store_true"
    )
    parser.add_argument(
        "--include_network",
        help="Include domains/URLs/RFC822/httplogs in results",
        action="store_true",
    )
    parser.add_argument(
        "--be_reports",
        help="Specify path to existing bulk_extractor reports directory",
        action="store",
    )
    parser.add_argument("--regex", help="Specify path to regex file", action="store")
    parser.add_argument(
        "--stoplists",
        help="Specify directory for bulk_extractor stoplists",
        action="store",
    )
    parser.add_argument(
        "-n",
        "--named_entity_extraction",
        help="Extract named entities with Tika and spaCy",
        action="store_true",
    )
    parser.add_argument(
        "--export",
        help="Use script in export mode (export files based on JSON input)",
        action="store_true",
    )
    parser.add_argument(
        "--pii",
        help="Export files with PII. Used in tandem with --export flag",
        action="store_true",
    )
    parser.add_argument(
        "--flat",
        help="Export private files in flat directory. \
              Used in tandem with --export flag",
        action="store_true",
    )
    parser.add_argument(
        "--restore_dates",
        help="Restore modified dates for exported files to values in DFXML. \
              Used in tandem with --export flag",
        action="store_true",
    )
    parser.add_argument(
        "--unallocated",
        help="Export unallocated files. Used in tandem with --export flag",
        action="store_true",
    )
    parser.add_argument(
        "--tar",
        help="Generate tar exclude file. Used in tandem with --export flag",
        action="store_true",
    )
    parser.add_argument("source", help="Path to source directory or disk image")
    parser.add_argument("destination", help="Path to directory to write output files")
    parser.add_argument("filename", help="Filename for output file (no extension)")

    return parser


def main():
    # Parse arguments
    parser = _make_parser()
    args = parser.parse_args()

    # Save references to filepaths for source and outputs
    src = os.path.abspath(args.source)
    dest = os.path.abspath(args.destination)
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, args.filename + ".brv")
    reports_path = os.path.join(dest, args.filename + "_reports")
    dfxml_path = os.path.join(reports_path, "dfxml.xml")
    annotated_feature_path = os.path.join(reports_path, "bulk_extractor_annotated")
    user_home_dir = os.path.abspath(os.path.expanduser("~"))
    bulk_reviewer_dir = os.path.join(user_home_dir, "bulk-reviewer")

    if args.be_reports:
        bulk_extractor_path = os.path.abspath(args.be_reports)
    else:
        bulk_extractor_path = os.path.join(reports_path, "bulk_extractor")

    # Make bulk_reviewer_dir if doesn't already exist
    if not os.path.exists(bulk_reviewer_dir):
        os.makedirs(bulk_reviewer_dir)

    # Configure logging
    _configure_logging(bulk_reviewer_dir)

    # If script run in export mode, run file export and return
    if args.export:
        logging.info(
            "Running script in file export mode. JSON file: %s. Destination: %s.",
            src,
            dest,
        )
        file_export = FileExport(
            src,
            dest,
            args.diskimage,
            args.pii,
            args.flat,
            args.restore_dates,
            args.unallocated,
            args.tar,
        )
        file_export.export_files()
        return

    # Otherwise, log starting message and continue
    logging.info(
        "Running script in processing mode. Name: %s. Source: %s.", args.filename, src
    )

    # Create output directories
    for out_dir in dest, reports_path, bulk_extractor_path:
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

    # Create database and session
    engine = create_engine("sqlite:///{}".format(db_path))
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Set ssn mode - default to 1 if not provided
    if args.ssn in (0, 2):
        ssn_mode = args.ssn
    else:
        ssn_mode = 1

    # Save BR session info to db
    br_session = BRSession(
        name=args.filename,
        source_path=src,
        disk_image=args.diskimage,
        named_entity_extraction=args.named_entity_extraction,
        regex_file=args.regex,
        ssn_mode=ssn_mode,
    )
    session.add(br_session)
    session.commit()

    # Store br_session_id
    try:
        br_session_find = (
            session.query(BRSession).filter(BRSession.name == args.filename).one()
        )
        br_session_id = br_session_find.id
    except Exception:
        logging.error("JSON file with same name already exists. Quitting")
        print_to_stderr_and_exit("JSON file with same name already exists.")

    # Disk image - Write file info to db
    if args.diskimage:

        # Create dfxml
        logging.info("Creating DFXML")
        dfxml_success = create_dfxml(src, dfxml_path)
        if dfxml_success is False:
            print_to_stderr_and_exit("fiwalk unable to create DFXML.")

        # Parse dfxml to db
        logging.info("Parsing DFXML to database")
        try:
            parse_dfxml_to_db(session, br_session_id, dfxml_path)
        except Exception as e:
            logging.error("Error parsing DFXML file %s: %s", dfxml_path, e)
            print_to_stderr_and_exit("Error parsing DFXML file.")

        # Write error message and quit if no files found
        num_files = session.query(func.count(File.id)).scalar()
        if num_files == 0:
            logging.error(
                "No files found. File system may be unsupported by fiwalk. Quitting."
            )
            print_to_stderr_and_exit(
                "No files found. File system may be unsupported by fiwalk."
            )

    # Directory - Write file info to db
    else:
        logging.info("Writing source file metadata to database")
        write_filesystem_metadata_to_db(session, br_session_id, src)

    # Run bulk_extractor if reports aren't already provided
    if not args.be_reports:
        logging.info("Running bulk_extractor")
        stoplist_dir = ""
        if args.stoplists:
            stoplist_dir = os.path.abspath(args.stoplists)
        bulk_extractor_success = run_bulk_extractor(
            src, bulk_extractor_path, stoplist_dir, ssn_mode, args
        )
        if bulk_extractor_success is False:
            print_to_stderr_and_exit("Error running bulk_extractor.")

    if args.diskimage:
        # Disk image source: Annotate feature files and read into database
        logging.info("Annotating feature files")
        annotate_feature_files(bulk_extractor_path, annotated_feature_path, dfxml_path)
        logging.info("Reading feature files to database")
        read_features_to_db(annotated_feature_path, br_session_id, session, args)

    else:
        # Directory source: read feature files into database
        logging.info("Reading feature files to database")
        read_features_to_db(bulk_extractor_path, br_session_id, session, args)

    # TODO : Get named entities (directories only)

    # Create JSON output
    json_path = os.path.join(dest, args.filename + ".json")
    try:
        brv_to_json(db_path, json_path)
        logging.info("Created JSON file %s", json_path)
        # print path to stdout as utf-8 (supports utf-8 chars/emojis)
        sys.stdout.buffer.write(json_path.encode("utf-8"))
    except Exception as e:
        logging.error("Error creating JSON file %s: %s", json_path, e)
        print_to_stderr_and_exit("Error creating JSON file.")

    # Delete temp_dir with .brv file
    try:
        shutil.rmtree(temp_dir)
        logging.info("Deleted tempdir")
    except Exception:
        logging.warning("Unable to delete tempdir %s", temp_dir)

    logging.info("Complete")


if __name__ == "__main__":
    main()
