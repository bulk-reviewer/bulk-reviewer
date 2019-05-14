Installation
=============

Dependencies
------------
Bulk Reviewer requires that the following programs are installed on the same computer and that their command line interfaces are available on the system path:

* `bulk_extractor <https://github.com/simsong/bulk_extractor/>`_: Bulk Reviewer is compatible with bulk_extractor 1.5.5+. Scanning for Canadian Social Insurance Numbers (SINs) requires bulk_extractor version 1.6.0-dev, built from commit `f4ac85d <https://github.com/simsong/bulk_extractor/commit/f4ac85d84c5d5d5aee868234acee527695727344/>`_ or later.
* `The Sleuth Kit <https://github.com/sleuthkit/sleuthkit/>`_

For Bulk Reviewer to be able to handle Encase/E01 disk images, bulk_extractor and The Sleuth Kit must be built with `libewf <https://github.com/libyal/libewf/>`_.

These dependencies should already be installed in the `BitCurator Environment <https://confluence.educopia.org/display/BC/BitCurator+Environment/>`_ (unless you need to scan for Canadian SINs, in which case bulk_extractor will need to be rebuilt from source).

Installation in BitCurator
--------------------------

1. Download the ``BulkReviewer-x.x.x-x86_64.AppImage`` `AppImage <https://appimage.org/>`_ from the `latest Bulk Reviewer release <https://github.com/bulk-reviewer/bulk-reviewer/releases/>`_.

2. Move the AppImage to the "Forensics and Reporting" folder on the BitCurator desktop.

3. Make the Bulk Reviewer AppImage executable (right-click on the AppImage file, select Properties, and then select "Allow executing file as program" under the Permissions tab; or change the file permissions with ``chmod u+x`` in a terminal).

4. Double-click the AppImage. A prompt will ask if you want to integrate Bulk Reviewer with your system. Choose "Yes" to install Bulk Reviewer.

From this point forward, Bulk Reviewer can be launched by selecting it from the Applications menu or double-clicking on the AppImage file in the "Forensics and Reporting" folder.

Installation in Ubuntu 18.04
----------------------------

1. Install dependencies in a terminal:

.. code-block:: none

    wget "https://github.com/bulk-reviewer/bulk-reviewer/blob/master/install_ubuntu18.sh"
    chmod a+x install_ubuntu18.sh
    sudo ./install_ubuntu18.sh

2. Download the ``BulkReviewer-x.x.x-x86_64.AppImage`` `AppImage <https://appimage.org/>`_ from the `latest Bulk Reviewer release <https://github.com/bulk-reviewer/bulk-reviewer/releases/>`_.

3. Move the AppImage to your home directory or desktop and make the file executable (right-click on the AppImage file, select Properties, and then select "Allow executing file as program" under the Permissions tab; or change the file permissions with ``chmod u+x`` in a terminal).

4. Double-click the AppImage. A prompt will ask if you want to integrate Bulk Reviewer with your system. Choose "Yes" to install Bulk Reviewer.

From this point forward, Bulk Reviewer can be launched by selecting it from the Applications menu or double-clicking on the AppImage file.

Installation in macOS
---------------------

1. Make sure you have `Homebrew <https://brew.sh/>`_ and `XCode <https://developer.apple.com/xcode/>`_ installed.

2. Download the ``install_mac.sh`` script from the Bulk Reviewer Github repository.

3. In a terminal, change directory to where you saved the `install_mac.sh` script and install dependencies:

.. code-block:: none

    brew install libewf afflib sleuthkit
    chmod a+x install_mac.sh
    ./install_mac.sh

4. Download the `BulkReviewer-x.x.x.dmg` from the `latest Bulk Reviewer release <https://github.com/bulk-reviewer/bulk-reviewer/releases/>`_.

5. Double-click the dmg to open the Bulk Reviewer installer. Drag the Bulk Reviewer icon to the Applications folder to install.