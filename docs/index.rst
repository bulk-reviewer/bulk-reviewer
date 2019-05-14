.. Bulk Reviewer documentation master file, created by
   sphinx-quickstart on Tue Jan  8 13:46:10 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bulk Reviewer's documentation!
=========================================

.. toctree::
    :caption: Table of Contents
    :maxdepth: 2

    installation

Bulk Reviewer is an Electron desktop application that aids in identification, review, and removal of sensitive files in directories and disk images. Bulk Reviewer scans directories and disk images for personally identifiable information (PII) and other sensitive information using `bulk_extractor <https://github.com/simsong/bulk_extractor>`_, a best-in-class digital forensics tool. The desktop application enables users to configure, start, and review scans; generate CSV reports of features found; and export sets of files (either those free of sensitive information, or those with PII that should be restricted or run though redaction software).

Currently, Bulk Reviewer can scan directories and disk images for:

* Social Security Numbers (SSNs)
* Canadian Social Insurance Number (SINs)
* Credit card numbers
* Email addresses
* Phone numbers
* URLs, web domains, RFC822 headers, and HTTP logs
* GPS data
* EXIF metadata
* User-supplied regular expressions (uploaded as a txt file with each regexp on a new line)

Scanners planned but not yet implemented include:

* Personal names
* Names of nationalities, religions, and political affiliations
* National identifiers (besides USA and Canada)
* Banking information (e.g. IBAN and SWIFT account numbers, ABA numbers)
* Personal health information
* Facebook and Outlook data
* Additional lexicons (like those developed by the ePADD project team)

The application is designed to aid archivists and librarians in processing and providing access to digital collections but may be useful in other domains as well. Bulk Reviewer has been made possible in part by the generous support of a `Harvard Library Innovation Lab <https://lil.law.harvard.edu/>`_ summer fellowship and a `Concordia University Library <https://library.concordia.ca>`_ Research Grant.

------------------
Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`
