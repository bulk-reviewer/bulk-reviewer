# Bulk Reviewer

> Identify, review, and remove private information in directories and disk images

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


---

This project was generated with [electron-vue](https://github.com/SimulatedGREG/electron-vue)@[8fae476](https://github.com/SimulatedGREG/electron-vue/tree/8fae4763e9d225d3691b627e83b9e09b56f6c935) using [vue-cli](https://github.com/vuejs/vue-cli). Documentation about the original structure can be found [here](https://simulatedgreg.gitbooks.io/electron-vue/content/index.html).
