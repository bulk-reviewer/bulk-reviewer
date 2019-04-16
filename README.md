# Bulk Reviewer

> Identify, review, and remove private information in directories and disk images

Bulk Reviewer is a software program that aids in identification, review, and removal of sensitive files in directories and disk images. Bulk Reviewer scans directories and disk images for personally identifiable information (PII) and other sensitive information using [bulk_extractor](https://github.com/simsong/bulk_extractor), a best-in-class digital forensics tool, and can optionally extract named entities (personal names as well as nationalities, religions, and political affiliations) using [spaCy](https://spacy.io/) and [Apache Tika](https://tika.apache.org/). A browser application enables users to configure, start, and review scans, generate reports, and export files, separating problematic files (e.g., those requiring redaction or further review) from those that are free of sensitive information.

Currently, Bulk Reviewer can scan directories and disk images for:

* Social Security Numbers (SSNs)
* Credit card numbers
* Email addresses
* Phone numbers
* URLs, web domains, RFC822 headers, and HTTP logs
* GPS data
* EXIF metadata

Scanners planned but not yet implemented include:

* Personal names
* Names of nationalities, religions, and political affiliations
* User-supplied regular expressions
* Canadian Social Insurance Number (SIN) and other national identifiers
* Banking information
* Personal health information
* Facebook and Outlook data
* Additional lexicons (like [those developed by the ePADD project team](https://library.stanford.edu/projects/epadd/community/lexicon-working-group))

Contributions are welcome!

The application is designed to aid archivists and librarians in processing and providing access to digital collections but may be useful in other domains as well. The application is currently under active development, and is still in the exploratory/prototype phase. This project has been made possible in part by the generous support of the [Library Innovation Lab](https://lil.law.harvard.edu) at Harvard University, where Tim Walsh was a 2018 Summer Fellow, and a Concordia University Library Research Grant.

An earlier Django-based server application version of Bulk Reviewer can be found [here](https://github.com/timothyryanwalsh/bulk-reviewer).

Interested in getting involved? [Get in touch](mailto:tim.walsh@concordia.ca)!

## Development

Bulk Reviewer is an Electron desktop application with a Python backend. Local development requires Python 3, Node, and npm/yarn (instructions here use yarn).

1. Clone this repository

`git clone https://github.com/bulk-reviewer/bulk-reviewer`

2. Prepare Python virtual environment

``` bash
# First time

virtualenv -p python3 env
source env/bin/activate
pip install -r src/main/backend/requirements.txt

# Subsequent times

source env/bin/activate
```

3. Install npm modules (first time only)

`yarn install`

4. Start webpack development server

`yarn run dev`

## Build locally

Instructions forthcoming. Basic steps:

1. Package Python scripts

2. Build Electron application for production

`yarn run build`

## Logo design
[Bailey McGinn](https://baileymcginn.com/)

---

This project was generated with [electron-vue](https://github.com/SimulatedGREG/electron-vue)@[8fae476](https://github.com/SimulatedGREG/electron-vue/tree/8fae4763e9d225d3691b627e83b9e09b56f6c935) using [vue-cli](https://github.com/vuejs/vue-cli). Documentation about the original structure can be found [here](https://simulatedgreg.gitbooks.io/electron-vue/content/index.html).
