.. Bulk Reviewer documentation master file, created by
   sphinx-quickstart on Tue Jan  8 13:46:10 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bulk Reviewer documentation
===========================

.. toctree::
    :maxdepth: 2

    overview
    technicalinfo
    installation
    newscan
    reviewdashboard


**Current version: Bulk Reviewer 0.1.0**

Bulk Reviewer is an Electron desktop application that aids in identification, review, and removal of sensitive files in directories and disk images. Bulk Reviewer scans directories and disk images for personally identifiable information (PII) and other sensitive information using `bulk_extractor <https://github.com/simsong/bulk_extractor>`_, a best-in-class digital forensics tool. The desktop application enables users to configure, start, and review scans; generate CSV reports of features found; and export sets of files (either those free of sensitive information, or those with PII that should be restricted or run though redaction software).