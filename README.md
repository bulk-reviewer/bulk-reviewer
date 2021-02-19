![Bulk Reviewer logo](https://github.com/bulk-reviewer/bulk-reviewer/blob/main/full-logo.png)

## Identify, review, and remove sensitive files

For detailed installation and use instructions, see the [documentation](https://bulk-reviewer.readthedocs.io/en/latest/index.html).

Bulk Reviewer is an Electron desktop application that aids in identification, review, and removal of sensitive files in directories and disk images. Bulk Reviewer scans directories and disk images for personally identifiable information (PII) and other sensitive information using [bulk_extractor](https://github.com/simsong/bulk_extractor), a best-in-class digital forensics tool. The desktop application enables users to:

* Scan disk images and directories for private information with bulk_extractor (configurable with user-supplied regular expressions and stoplist files)
* Review features found by type and by file in a user-friendly dashboard that supports annotation and dismissing features as false positives
* Generate CSV reports of features found
* Export sets of files
	* Cleared: Files free of PII
	* Private: Files with PII that should be restricted or run through redaction software

Currently, Bulk Reviewer can scan directories and disk images for:

* Social Security Numbers (SSNs)
* Canadian Social Insurance Number (SINs)
* Credit card numbers
* Email addresses
* Phone numbers
* vCards (Virtual Contact Files)
* URLs, web domains, RFC822 headers, and HTTP logs
* GPS data
* EXIF metadata
* User-supplied regular expressions (uploaded as a txt file with each regexp on a new line)

Scanners planned but not yet implemented include:

* Personal names
* Other national identifiers
* Banking information (e.g. IBAN and SWIFT account numbers, ABA numbers)
* Personal health information
* Facebook and Outlook data
* Additional lexicons (like [those developed by the ePADD project team](https://library.stanford.edu/projects/epadd/community/lexicon-working-group))

The application is designed to aid archivists and librarians in processing and providing access to digital collections but may be useful in other domains as well. Bulk Reviewer has been made possible in part by the generous support of a [Harvard Library Innovation Lab](https://lil.law.harvard.edu) summer fellowship and a [Concordia University Library](https://library.concordia.ca) Research Grant.

An earlier server-based prototype of Bulk Reviewer developed using Django, Django REST Framework, and Vue.js can be found [here](https://github.com/tw4l/bulk-reviewer).

Contributions are welcome! Interested in getting involved? [Get in touch](mailto:tessa@bitarchivist.net)!

## Dependencies

Bulk Reviewer requires that the following programs are installed on the same computer and that their command line interfaces are available on the system path:

* [bulk_extractor](https://github.com/simsong/bulk_extractor): Bulk Reviewer is compatible with bulk_extractor 1.5.5+. Scanning for Canadian Social Insurance Numbers (SINs) requires bulk_extractor version 1.6.0-dev, built from commit [f4ac85d](https://github.com/simsong/bulk_extractor/commit/f4ac85d84c5d5d5aee868234acee527695727344) or later.
* [The Sleuth Kit (TSK)](https://github.com/sleuthkit/sleuthkit)

For Bulk Reviewer to be able to handle Encase/E01 disk images, bulk_extractor and The Sleuth Kit must be built with [libewf](https://github.com/libyal/libewf/).

These dependencies should already be installed in the [BitCurator Environment](https://confluence.educopia.org/display/BC/BitCurator+Environment) (unless you need to scan for Canadian SINs, in which case bulk_extractor will need to be rebuilt from source).

Scripts for installing system dependencies for macOS and Ubuntu 18.04 are included in this repository. See Installation below.

## Installation

### BitCurator

1. Download the `BulkReviewer-x.x.x-x86_64.AppImage` [AppImage](https://appimage.org/) from the [latest Bulk Reviewer release](https://github.com/bulk-reviewer/bulk-reviewer/releases).

2. Save the AppImage file to location of your choice (e.g. the "Forensics and Reporting" folder on the BitCurator desktop).

3. Make the Bulk Reviewer AppImage executable (with `chmod +x FILE` in terminal or by right-clicking the AppImage, selecting Properties, and then selecting "Allow executing file as program" under the Permissions tab).

4. Double-click the AppImage. A prompt will ask if you want to integrate Bulk Reviewer with your system. Choose "Yes" to install Bulk Reviewer.

From this point forward, Bulk Reviewer can be launched by selecting it from the Applications menu or double-clicking on the AppImage file.

### Ubuntu 18.04

1. Install dependencies in a terminal (you can skip this step if bulk_extractor and Sleuth Kit are already installed):

``` bash
wget "https://raw.githubusercontent.com/bulk-reviewer/bulk-reviewer/main/install_ubuntu18.sh"
chmod +x install_ubuntu18.sh
sudo ./install_ubuntu18.sh
```

2. Download the Bulk Reviewer [AppImage](https://appimage.org/) `BulkReviewer-x.x.x.AppImage` from the [latest Bulk Reviewer release](https://github.com/bulk-reviewer/bulk-reviewer/releases).

3. Save the AppImage to location of your choice (e.g. your home folder or desktop).

4. Make the Bulk Reviewer AppImage executable (with `chmod +x FILE` in terminal or by right-clicking the AppImage, selecting Properties, and then selecting "Allow executing file as program" under the Permissions tab).

5. Double-click the AppImage. A prompt will ask if you want to integrate Bulk Reviewer with your system. Choose "Yes" to install Bulk Reviewer.

From this point forward, Bulk Reviewer can be launched by selecting it from the Applications menu or double-clicking on the AppImage file.

### macOS

1. Make sure you have [Homebrew](https://brew.sh/) and [XCode](https://developer.apple.com/xcode/) installed.

2. Install dependencies in a terminal (you can skip this step if bulk_extractor and Sleuth Kit are already installed):

``` bash
wget "https://raw.githubusercontent.com/bulk-reviewer/bulk-reviewer/main/install_mac.sh"
chmod +x install_mac.sh
./install_mac.sh
```

3. Download the `BulkReviewer-x.x.x.dmg` from the [latest Bulk Reviewer release](https://github.com/bulk-reviewer/bulk-reviewer/releases).

4. Double-click the dmg to open the Bulk Reviewer installer. Drag the Bulk Reviewer icon to the Applications folder to install.

## Development

Bulk Reviewer is an Electron desktop application with a Python backend. Local development requires Python 3, Node 10, and npm or yarn (instructions here use yarn).

1. Clone this repository

``` bash
git clone https://github.com/bulk-reviewer/bulk-reviewer
```

2. Prepare Python virtual environment

``` bash
cd bulk-reviewer/

# First time
virtualenv -p python3 env
source env/bin/activate
pip install -r src/main/backend/requirements.txt

# Subsequent times
source env/bin/activate
```

3. Install npm modules (first time only)

``` bash
yarn install
```

4. Start webpack development server

``` bash
yarn run dev
```

## Build locally

1. Follow Development steps 1-3 above

2. Package Python script as executable

``` bash
./build-backend.sh
```

(If build-backend script is not executable, make it executable with `chmod +x build-backend.sh`)

3. Build Electron application for production

``` bash
yarn run build
```

The resulting built application can be found in the `build` directory.

## Test

1. Follow Development steps 1-2 above

2. Run backend tests

``` bash
python src/main/backend/test.py
```

## Logo design
[Bailey McGinn](https://baileymcginn.com/)

---

This project was generated with [electron-vue](https://github.com/SimulatedGREG/electron-vue)@[8fae476](https://github.com/SimulatedGREG/electron-vue/tree/8fae4763e9d225d3691b627e83b9e09b56f6c935) using [vue-cli](https://github.com/vuejs/vue-cli). Documentation about the original structure can be found [here](https://simulatedgreg.gitbooks.io/electron-vue/content/index.html).
