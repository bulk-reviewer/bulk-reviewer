Technical information
=====================

Bulk Reviewer is an `Electron <https://electronjs.org/>`_ (Node.js + Chromium) desktop application with a `Vue.js <https://vuejs.org/>`_ frontend built using `Buefy <https://buefy.org/>`_ UI components and the `electron-vue <https://github.com/SimulatedGREG/electron-vue>`_ boilerplate.

Backend functionality is provided by a Python 3 script ``br_processor.py`` which is packaged and included in the built application. This backend script handles calling `bulk_extractor <https://github.com/simsong/bulk_extractor>`_ as a subprocess, post-processing bulk_extractor feature files and associating features with their respective source files, and creating the Bulk Reviewer JSON output file and handing it to the frontend. This same backend script is called with the ``--export`` flag and additional arguments to manage file exports. Bulk Reviewer uses the ``icat`` tool from `Sleuth Kit <https://www.sleuthkit.org/>`_ to carve files from disk images for file exports.

The Bulk Reviewer backend includes some modified code from the public domain `bulk_extractor <https://github.com/simsong/bulk_extractor>`_ and `DFXML <https://github.com/simsong/dfxml>`_ codebases, including code written by Simson Garfinkel and Alex Nelson, to parse DFXML, annotate bulk_extractor feature files, and associate features with their respective source files.