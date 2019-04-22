#!/usr/bin/env python3

"""
Creates Bulk Reviewer JSON file and DFXML
and bulk_extractor output directories for input
directory or disk image.

Tim Walsh, 2019
https://bitarchivist.net
Licensed under GNU General Public License 3
https://www.gnu.org/licenses/gpl-3.0.en.html

"""

from sqlalchemy import create_engine, Column, ForeignKey, \
                       Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound
from pathlib import Path
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import zipfile
import Objects

Base = declarative_base()


class BRSession(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    source_path = Column(String)
    disk_image = Column(Boolean)
    named_entity_extraction = Column(Boolean)
    regex_file = Column(String, nullable=True)
    ssn_mode = Column(Integer)


class File(Base):
    __tablename__ = 'file'
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
    session = Column(Integer, ForeignKey('session.id'))


class Feature(Base):
    __tablename__ = 'feature'
    id = Column(Integer, primary_key=True)
    feature_type = Column(String(50))
    forensic_path = Column(String, nullable=True)
    offset = Column(String, nullable=True)
    feature = Column(String)
    context = Column(String, nullable=True)
    note = Column(String, nullable=True)
    cleared = Column(Boolean)
    file = Column(Integer, ForeignKey('file.id'))


def create_dfxml_diskimage(src, dfxml_path):
    """
    Create DFXML representation of source disk image using fiwalk
    and save to destination directory. Return True is successful,
    False if unsuccessful.
    """
    cmd = ['fiwalk',
           '-X',
           dfxml_path,
           src]
    try:
        subprocess.check_output(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print('Error creating DFXML with fiwalk. Details: {}'.format(e))
        return False


def create_dfxml_directory(src, dfxml_path, scripts_dir):
    """
    Create DFXML representation of source directory using walk_to_dfxml.py
    and save to destination directory. Return True is successful,
    False if unsuccessful.
    """
    walk_to_dfxml = os.path.join(scripts_dir, 'walk_to_dfxml.py')
    cmd = 'cd "{0}" && python3 {1} > "{2}"'.format(src,
                                                   walk_to_dfxml,
                                                   dfxml_path)
    try:
        subprocess.call(cmd, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print('Error creating DFXML with walk_to_dfxml.py. Details: {}'
              .format(e))
        return False


def run_bulk_extractor(src, bulk_extractor_path, stoplist_dir,
                       ssn_mode, args):
    """
    Create and run bulk_extractor subprocess command.
    """
    cmd = ['bulk_extractor',
           '-o',
           bulk_extractor_path,
           # '-w',
           # os.path.join(stoplist_dir, 'combined-url.txt'),
           # '-w',
           # os.path.join(stoplist_dir, 'combined-email.txt'),
           # '-w',
           # os.path.join(stoplist_dir, 'combined-telephone.txt'),
           # '-w',
           # os.path.join(stoplist_dir, 'combined-ccn.txt'),
           # '-w',
           # os.path.join(stoplist_dir, 'domain.txt'),
           '-x',
           'windirs',
           '-x',
           'winpe',
           '-x',
           'winlnk',
           '-x',
           'winprefetch',
           '-S',
           'ssn_mode={}'.format(str(ssn_mode)),
           '-S',
           'jpeg_carve_mode=0',
           src]
    if not args.diskimage:
        cmd.insert(15, '-R')
    if args.regex:
        cmd.insert(1, '-F')
        cmd.insert(2, args.regex)

    try:
        subprocess.check_output(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print('Error running bulk_extractor. Details: {}'.format(e))
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
        date_modified = ''
        if obj.mtime:
            date_modified = str(obj.mtime)
        date_created = ''
        if obj.crtime:
            date_created = str(obj.crtime)
        if obj.ctime:
            date_created = str(obj.ctime)
        allocated = True
        if obj.unalloc:
            if obj.unalloc == 1:
                allocated = False
        inode = ''
        if obj.inode:
            inode = str(obj.inode)
        fs_offset = ''
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
            verified=False
        )
        try:
            session.add(new_file)
            session.commit()
        except Exception:
            print("Error writing file {} to database.".format(filepath))


def user_friendly_feature_type(feature_file):
    """
    Return user-friendly feature type value for
    corresponding feature file. If no such label
    exists, return name of feature file.
    """
    if feature_file == 'pii.txt':
        return 'Social Security Number (USA)'
    elif feature_file == 'sin.txt':
        return 'Social Insurance Number (Canada)'
    elif feature_file == 'ccn.txt':
        return 'Credit card number'
    elif feature_file == 'telephone.txt':
        return 'Phone number'
    elif feature_file == 'email.txt':
        return 'Email address'
    elif feature_file == 'find.txt':
        return 'Regular expression'
    elif feature_file == 'url.txt':
        return 'URL'
    elif feature_file == 'domain.txt':
        return 'Domain'
    elif feature_file == 'rfc822.txt':
        return 'Email/HTTP header (RFC822)'
    elif feature_file == 'httplogs.txt':
        return 'HTTP log'
    elif feature_file == 'gps.txt':
        return 'GPS data'
    elif feature_file == 'exif.txt':
        return 'EXIF metadata'
    else:
        return feature_file


def annotate_feature_files(feature_files_dir,
                           annotated_feature_path,
                           dfxml_path,
                           scripts_dir):
    """
    Annotate bulk_extractor feature files for disk images
    to associate features to files in the image.
    """
    identify_filenames = os.path.join(scripts_dir, 'identify_filenames.py')

    if not os.path.exists(annotated_feature_path):
            os.makedirs(annotated_feature_path)
    cmd = ['python3',
           identify_filenames,
           '--all',
           '--xmlfile',
           dfxml_path,
           feature_files_dir,
           annotated_feature_path]
    try:
        subprocess.check_output(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print('identify_filenames.py unable to annotated feature files. Details: {}'.format(e))
        return False


def read_features_to_db(feature_files_dir, br_session_id, session, args):
    """
    Read information from appropriate feature files
    into database, adding feature type.
    """
    for feature_file in os.listdir(feature_files_dir):
        # Absolute path for file
        ff_abspath = os.path.join(feature_files_dir, feature_file)
        # Skip empty files
        if not os.path.getsize(ff_abspath) > 0:
            continue
        # Skip directories
        if os.path.isdir(feature_file):
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
        # Skip stoplist results
        if "_stopped" in feature_file:
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
    """
    Parse features in bulk_extractor feature file and write
    each feature to database.
    """
    with open(feature_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Ignore commented lines
            if line.startswith(('#')):
                continue
            # Ignore blank lines
            if not line.strip():
                continue

            # Parse and clean up tab-separated lines
            DELIMITER = '\U0010001c'
            forensic_path = ''
            filepath = ''
            feature = ''
            context = ''
            try:
                (forensic_path, feature, context) = line.split('\t')
                filepath = forensic_path
                if DELIMITER in forensic_path:
                    filepath = forensic_path.split(DELIMITER)[0]
                context = context.rstrip()  # strip trailing newline

                # Make filepath relative to match DFXML filename
                source_path = session.query(BRSession).get(br_session_id).\
                    source_path
                substr = source_path + '/'
                filepath = filepath.split(substr)[1]

                # Find matching file
                try:
                    matching_file = session.query(File).filter_by(
                        filepath=filepath,
                        session=br_session_id
                    ).first()
                except NoResultFound:
                    print("Matching file not found for", filepath)
                    continue

                # Set feature type
                ff_basename = os.path.basename(feature_file)
                feature_type = user_friendly_feature_type(ff_basename)

                # Write feature to database
                postprocessed_feature = Feature(
                    feature_type=feature_type,
                    forensic_path=forensic_path,
                    feature=feature,
                    context=context,
                    cleared=False,
                    file=matching_file.id
                )
                try:
                    session.add(postprocessed_feature)
                    session.commit()
                except Exception:
                    print("Error writing to database.")
            except Exception:
                continue  # for debugging
                # print("Error processing line in feature file {0}. Unread line: {1}".format(feature_file, line))


def parse_annotated_feature_file(feature_file, br_session_id, session):
    """
    Parse features in annotated bulk_extractor feature file
    and write each feature to database.
    """
    with open(feature_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Ignore commented lines
            if line.startswith(('#')):
                continue
            # Ignore blank lines
            if not line.strip():
                continue

            # Parse tab-separated lines
            try:
                (offset, feature, context, filepath,
                 blockhash) = line.split('\t')

                # Try to find matching file
                try:
                    matching_file = session.query(File).filter_by(
                        filepath=filepath,
                        session=br_session_id
                    ).first()

                # If matching file doesn't exist, match to placeholder
                except NoResultFound:

                    # Check if placeholder already exists
                    try:
                        matching_file = session.query(File).filter_by(
                            filepath="<unallocated space>",
                            session=br_session_id
                        ).first()

                    # Create placeholder if one doesn't already exist
                    except NoResultFound:
                        unallocated_placeholder = File(
                            filepath="<unallocated space>",
                            filename="<unallocated space>",
                            allocated=False,
                            session=br_session_id
                        )
                        session.add(unallocated_placeholder)
                        session.commit()
                        matching_file = session.query(File).filter_by(
                            filepath="<unallocated space>",
                            session=br_session_id
                        ).first()

                # Set feature type
                ff_basename = os.path.basename(feature_file).\
                    replace('annotated_', '')
                feature_type = user_friendly_feature_type(ff_basename)

                # Write feature to database
                postprocessed_feature = Feature(
                    feature_type=feature_type,
                    offset=offset,
                    feature=feature,
                    context=context,
                    cleared=False,
                    file=matching_file.id
                )
                session.add(postprocessed_feature)
                session.commit()

            except Exception:
                continue  # debugging
                # print("Error reading line to feature file {0}. Unread line: {1}".format(feature_file, line))


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
        """.format(session_info['id'])
    cursor.execute(files_sql_query)
    files = cursor.fetchall()
    session_info['files'] = files

    # Add features to dictionary with filepaths
    features_sql_query = """\
        SELECT f.id, f.feature_type, f.forensic_path, \
            f.offset, f.feature, f.context, f.note, \
            f.cleared, f.file, fl.filepath
        from feature f, file fl
        WHERE f.file = fl.id
        """.format(session_info['id'])
    cursor.execute(features_sql_query)
    features = cursor.fetchall()
    session_info['features'] = features

    # Replace sqlite integer boolean values in dict with Python booleans
    if session_info['disk_image'] == 1:
        session_info['disk_image'] = True
    else:
        session_info['disk_image'] = False

    if session_info['named_entity_extraction'] == 1:
        session_info['named_entity_extraction'] = True
    else:
        session_info['named_entity_extraction'] = False

    for index, file_dict in enumerate(session_info['files']):
        if file_dict['allocated'] == 1:
            session_info['files'][index]['allocated'] = True
        else:
            session_info['files'][index]['allocated'] = False

        if file_dict['verified'] == 1:
            session_info['files'][index]['verified'] = True
        else:
            session_info['files'][index]['verified'] = False

    for index, feature_dict in enumerate(session_info['features']):
        if feature_dict['cleared'] == 1:
            session_info['features'][index]['cleared'] = True
        else:
            session_info['features'][index]['cleared'] = False

    # Write dictionary as JSON to file
    with open(json_path, 'w') as outfile:
        return json.dump(session_info, outfile, ensure_ascii=False, indent=2)

    # Close sqlite connection
    cursor.close()
    conn.close()


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d",
                        "--diskimage",
                        help="Scan disk image",
                        action="store_true")
    parser.add_argument("--ssn",
                        help="Specify Bulk Extractor ssn_mode (0, 1, or 2)",
                        action="store",
                        type=int)
    parser.add_argument("--include_exif",
                        help="Include EXIF metadata in results",
                        action="store_true")
    parser.add_argument("--include_network",
                        help="Include domains/URLs/RFC822/httplogs in results",
                        action="store_true")
    parser.add_argument("--regex",
                        help="Specify path to regex file",
                        action="store")
    parser.add_argument("-n",
                        "--named_entity_extraction",
                        help="Extract named entities with Tika and spaCy",
                        action="store_true")
    parser.add_argument("source",
                        help="Path to source directory or disk image")
    parser.add_argument("destination",
                        help="Path to directory to write output files")
    parser.add_argument("filename",
                        help="Filename for output file (no extension)")

    return parser


def main():
    # Parse arguments
    parser = _make_parser()
    args = parser.parse_args()

    # Save references to filepaths for source and outputs
    src = os.path.abspath(args.source)
    dest = os.path.abspath(args.destination)
    db_path = os.path.join(dest, args.filename + '.brv')
    reports_path = os.path.join(dest, args.filename + '_reports')
    dfxml_path = os.path.join(reports_path, 'dfxml.xml')
    bulk_extractor_path = os.path.join(reports_path, 'bulk_extractor')
    annotated_feature_path = os.path.join(
        reports_path,
        'bulk_extractor_annotated'
    )
    user_home_dir = os.path.abspath(str(Path.home()))
    bulk_reviewer_dir = os.path.join(user_home_dir, 'bulk-reviewer')
    scripts_dir = os.path.join(bulk_reviewer_dir, 'scripts')

    # Create output directories
    for out_dir in dest, reports_path, bulk_extractor_path:
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

    # Create database and session
    engine = create_engine('sqlite:///{}'.format(db_path))
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
        ssn_mode=ssn_mode)
    session.add(br_session)
    session.commit()

    # Store br_session_id
    br_session_find = session.query(BRSession)\
        .filter(BRSession.name == args.filename).one()
    br_session_id = br_session_find.id

    # Make sure stoplists are extracted
    stoplist_zip = os.path.join(bulk_reviewer_dir, 'stoplists.zip')
    stoplist_dir = os.path.join(bulk_reviewer_dir, 'stoplists')
    if not os.path.isdir(stoplist_dir):
        with zipfile.ZipFile(stoplist_zip, 'r') as zip_ref:
            zip_ref.extractall(bulk_reviewer_dir)

    # Create dfxml
    if args.diskimage:
        dfxml_success = create_dfxml_diskimage(src, dfxml_path)
    else:
        dfxml_success = create_dfxml_directory(src, dfxml_path, scripts_dir)
    if dfxml_success is False:
        sys.exit(1)

    # Parse dfxml to db
    parse_dfxml_to_db(session, br_session_id, dfxml_path)

    # Run bulk_extractor
    bulk_extractor_success = run_bulk_extractor(
        src, bulk_extractor_path,
        stoplist_dir,
        ssn_mode,
        args
    )
    if bulk_extractor_success is False:
        sys.exit(1)

    if args.diskimage:
        # Disk image source: Annotate feature files and read into database
        annotate_success = annotate_feature_files(
            bulk_extractor_path,
            annotated_feature_path,
            dfxml_path,
            scripts_dir
        )
        if annotate_success is False:
            sys.exit(1)
        read_features_to_db(
            annotated_feature_path,
            br_session_id,
            session,
            args
        )

    else:
        # Directory source: read feature files into database
        read_features_to_db(
            bulk_extractor_path,
            br_session_id,
            session,
            args
        )

    # TODO : Get named entities (directories only)

    # Create JSON output
    json_path = os.path.join(dest, args.filename + '.json')
    try:
        brv_to_json(db_path, json_path)
        print(json_path)
    except Exception:
        print('Error creating JSON file')
        sys.exit(1)


if __name__ == '__main__':
    main()
