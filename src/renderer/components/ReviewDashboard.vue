<template>
  <section class="padded">
    <!-- Header -->
    <div class="container-fluid" style="margin-bottom: 15px;">
      <h1 class="title is-4">Session: {{ brSession.name }}</h1>
      <h2 class="subtitle is-6">
        Source: {{ brSession.source_path }}
        <span v-if="brSession.disk_image === true">
          <b-tooltip label="Type: Disk image"
            position="is-right"
            type="is-light">
            <b-icon icon="hdd"></b-icon>
          </b-tooltip>
        </span>
        <span v-else>
          <b-tooltip label="Type: Directory"
            position="is-right"
            type="is-light">
            <b-icon icon="folder"></b-icon>
          </b-tooltip>
        </span>
      </h2>
      <button class="button" @click="openSaveFileDialog">
        <b-icon
          icon="save"
          size="is-small">
        </b-icon>
        <span>Save</span>
      </button>
      <button class="button" @click="isExportModalActive = true">
        <b-icon
          icon="file-export"
          size="is-small">
        </b-icon>
        <span>Export files</span>
      </button>
      <button class="button" @click="downloadCSVFeaturesReport">
        <b-icon
          icon="download"
          size="is-small">
        </b-icon>
        <span>Download CSV</span>
      </button>
      <button
        class="button"
        @click="downloadTarExcludeFile"
        v-show="brSession.disk_image === false">
        <b-icon
          icon="download"
          size="is-small">
        </b-icon>
        <span>Download tar exclude file</span>
      </button>
    </div>

    <!-- File export modal -->
    <b-modal :active.sync="isExportModalActive"
      has-modal-card
      trap-focus
      aria-role="dialog"
      aria-modal>
      <div class="modal-card" style="width: auto">
        <header class="modal-card-head">
          <p class="modal-card-title">Export files</p>
        </header>
        <section class="modal-card-body">
          <!-- Export type -->
          <div class="block">
            <h3><strong>Type</strong></h3>
            <b-radio v-model="exportType"
                name="cleared"
                native-value="cleared">
                Cleared
                <b-tooltip label="Files free of undismissed PII"
                  position="is-right"
                  type="is-light">
                  <b-icon
                    icon="question-circle"
                    size="is-small">
                  </b-icon>
                </b-tooltip>
            </b-radio>
            <br>
            <b-radio v-model="exportType"
                name="private"
                native-value="private">
                Private
                <b-tooltip label="Files containing PII"
                  position="is-right"
                  type="is-light">
                  <b-icon
                    icon="question-circle"
                    size="is-small">
                  </b-icon>
                </b-tooltip>
            </b-radio>
          </div>
          <!-- Checkbox options -->
          <div class="block" v-show="atLeastOneExportOption"> 
            <h3><strong>Options</strong></h3>
            <div v-show="exportType === 'private'">
              <b-checkbox
                type="is-info"
                v-model="exportFlat">
                Export files to flat directory
              </b-checkbox>
              <br>
            </div>
            <div v-show="brSession.disk_image === true">
              <b-checkbox
                type="is-info"
                v-model="restoreDates"
                v-show="brSession.disk_image === true">
                Restore modified/created dates
              </b-checkbox>
              <br>
              <b-checkbox
                type="is-info"
                v-model="exportUnallocatedFiles"
                v-show="brSession.disk_image === true">
                Include unallocated files
              </b-checkbox>
            </div>
          </div>
        </section>
        <footer class="modal-card-foot">
          <button class="button" @click="isExportModalActive = false">Cancel</button>
          <button class="button is-primary" @click="exportFiles">Choose destination and export</button>
        </footer>
      </div>
    </b-modal>

    <!-- File selector button -->
    <div>
      <button
        v-if="showFileSelector"
        class="button"
        @click="toggleFileSelector">
        - Hide file selector
      </button>
      <button
        v-else
        class="button is-primary"
        @click="toggleFileSelector">
        + Show file selector
      </button>
    </div>
    
    <!-- File selector -->
    <div 
      class="container-fluid"
      id="fileSelector"
      v-show="showFileSelector">

      <h3 class="title is-6">Files with features: {{ filesWithFeaturesCount }}</h3>
      
      <b-field grouped group-multiline>
        <button
          v-show="selected != null"
          class="control button field is-light"
          @click="selected = null">
          <b-icon icon="times"></b-icon>
            <span>Clear selected</span>
          </button>
      </b-field>

      <b-table
        :data="filesWithFeatures"
        :selected.sync="selected"
        :paginated="true"
        :per-page="perPage"
        :current-page.sync="currentPage"
        :default-sort-direction="defaultSortDirection"
        default-sort="feature_count"
        focusable
        narrowed>

        <template slot-scope="props">

          <!-- Columns -->
          <b-table-column
            field="filepath"
            label="File"
            sortable>
            <span v-show="props.row.verified === true">
              <b-icon
                icon="check"
                class="verified">
              </b-icon>
            </span>
            {{ props.row.filepath }}
            <span 
              v-show="props.row.allocated === false"
              class="tag is-light">
              Unallocated file
            </span>
            <button
              v-if="props.row.verified !== true"
              class="button is-small is-light"
              @click="toggleFileVerifiedStatus(props.row.id)">
              Verify
            </button>
            <button
              v-else
              class="button is-small is-light"
              @click="toggleFileVerifiedStatus(props.row.id)">
              Unverify
            </button>
          </b-table-column>

          <b-table-column field="date_modified" label="Modified" sortable v-if="brSession.disk_image === false">
            {{ props.row.date_modified }}
          </b-table-column>

          <b-table-column field="date_created" label="Created" sortable v-else>
            {{ props.row.date_created }}
          </b-table-column>

          <b-table-column field="feature_count" label="Features" sortable>
            {{ fileFeatureCount(props.row.filepath) }} 
            <span 
              v-show="fileFeatureCount(props.row.filepath) < props.row.feature_count"
              class="dismissed">
              (of {{ props.row.feature_count }})
            </span>
          </b-table-column>
        </template>

      </b-table>
    </div>

    <!-- Features -->
    <feature-table
      :tableData="tableDataComputed"
      :currentFeatureContext="currentFeatureContext"
      :selected="selected"
      v-on:nullify="selected = null">
    </feature-table>

  </section>
</template>

<script>
import FeatureTable from './FeatureTable'

export default {
  name: 'review-dashboard',
  components: { FeatureTable },
  data () {
    return {
      selected: null,
      defaultSortDirection: 'desc',
      isPaginated: true,
      currentPage: 1,
      perPage: 5,
      showFileSelector: false,
      exportUnallocatedFiles: false,
      restoreDates: false,
      exportFlat: false,
      exportType: 'cleared',
      isExportModalActive: false
    }
  },
  methods: {
    toggleFileSelector () {
      this.showFileSelector = !this.showFileSelector
    },
    toggleFeatureDismissedStatus (featureID) {
      this.$store.dispatch('toggleFeatureDismissed', featureID)
    },
    toggleFileVerifiedStatus (fileID) {
      this.$store.dispatch('toggleFileVerified', fileID)
    },
    // attempt to open file with default program for filetype
    // only works for directories, not disk images
    openFileOnDesktop (myFile) {
      const shell = require('electron').shell
      const path = require('path')
      let fileAbspath = path.join(this.$store.state.BRSession.brSession.source_path, myFile)
      shell.openPath(fileAbspath)
    },
    // return count of non-dismissed features associated with file
    fileFeatureCount (filepath) {
      // get features associated with file
      let features = this.$store.state.BRSession.brSession.features
      let fileFeatures = features.filter(f => f.filepath === filepath)
      // filter out dismissed features
      let notDismissed = fileFeatures.filter(f => f.dismissed !== true)
      return notDismissed.length
    },
    // show user dialog to select file to save to
    openSaveFileDialog () {
      const remote = require('electron').remote
      const dialog = remote.dialog
      let defaultFileName = this.sessionNameWithoutSpaces + '.json'
      dialog.showSaveDialog({ defaultPath: defaultFileName }).then(result => {
        this.saveToJSONFile(result.filePath, false)
      })
    },
    // save current state to JSON file on disk
    saveToJSONFile (filepath, suppressToast) {
      const fs = require('fs')
      let jsonString = JSON.stringify(this.brSession)
      fs.writeFile(filepath, jsonString, (err) => {
        if (err) throw err
        // show success toast message unless suppressed
        if (suppressToast === false) {
          this.successMessage(`${filepath} saved`)
        }
      })
    },
    // write CSV report of all features
    downloadCSVFeaturesReport () {
      const remote = require('electron').remote
      const dialog = remote.dialog
      const fastcsv = require('fast-csv')
      const fs = require('fs')
      // show user dialog to select file to save to
      let defaultCSVReportName = this.sessionNameWithoutSpaces + '.csv'
      dialog.showSaveDialog({ defaultPath: defaultCSVReportName }).then(result => {
        const csvFile = result.filePath
        // write csv report to selected file
        const ws = fs.createWriteStream(csvFile)
        let data = this.brSession.features
        fastcsv
          .write(data, { headers: true })
          .pipe(ws)
        this.successMessage(`${csvFile} saved`)
      })
    },
    // determine if python is packaged as executable by checking
    // for presence of backend_dist directory
    guessPackaged () {
      const path = require('path')
      const PY_DIST_FOLDER = path.join(__dirname, '../../main/', 'backend_dist')
      return require('fs').existsSync(PY_DIST_FOLDER)
    },
    // get path to script or executable as appropriate
    getScriptPath () {
      const path = require('path')
      const remote = require('electron').remote
      const app = remote.app
      // check if app has been built
      // if yes, get path to python script in asar
      if (app.isPackaged) {
        const PY_DIST_FOLDER = path.join(__dirname, '../../../backend_dist')
        const PY_MODULE = 'br_processor'
        if (process.platform === 'win32') {
          return path.join(PY_DIST_FOLDER, PY_MODULE, PY_MODULE + '.exe')
        }
        return path.join(PY_DIST_FOLDER, PY_MODULE, PY_MODULE)
      // if no, get script path to development location
      } else {
        const PY_DIST_FOLDER = path.join(__dirname, '../../main/', 'backend_dist')
        const PY_FOLDER = path.join(__dirname, '../../main/', 'backend')
        const PY_MODULE = 'br_processor'
        if (!this.guessPackaged()) {
          return path.join(PY_FOLDER, PY_MODULE + '.py')
        }
        if (process.platform === 'win32') {
          return path.join(PY_DIST_FOLDER, PY_MODULE, PY_MODULE + '.exe')
        }
        return path.join(PY_DIST_FOLDER, PY_MODULE, PY_MODULE)
      }
    },
    // call python backend
    callBackend (scriptParameters) {
      const remote = require('electron').remote
      const app = remote.app

      // fix for mac os to make system PATH available to node
      const fixPath = require('fix-path')
      fixPath()

      // run python executable if built
      if (app.isPackaged) {
        // spawn command in shell
        let script = this.getScriptPath()
        let parametersMinusScript = scriptParameters.slice(1)
        console.log(`Script: ${script}`)
        console.log(`Parameters: ${parametersMinusScript}`)
        let pyProc = require('child_process').spawn(script, parametersMinusScript, { shell: true })

        // show in progress message
        this.inProgressMessage()

        // collect stdout and stderr
        let pyOut = ''
        let pyErr = ''
        pyProc.stdout.on('data', function (data) {
          pyOut += data.toString()
        })
        pyProc.stderr.on('data', function (data) {
          pyErr += data.toString()
        })

        // show user error or success message on completion
        let self = this
        pyProc.stdout.on('end', function (data) {
          if (pyErr.length > 0) {
            self.errorMessage(pyErr)
          } else {
            self.successMessage(pyOut)
          }
        })
      // otherwise, run unbuilt script
      } else {
        let pyProc = require('child_process').spawn('python3', scriptParameters)
        let pyOut = ''
        let pyErr = ''

        // show in progress message
        this.inProgressMessage()

        // collect stdout
        pyProc.stdout.on('data', function (data) {
          pyOut += data.toString()
        })

        // collect stderr
        pyProc.stderr.on('data', function (data) {
          pyErr += data.toString()
        })

        // show user error or success message on completion
        let self = this
        pyProc.stdout.on('end', function (data) {
          if (pyErr.length > 0) {
            self.errorMessage(pyErr)
          } else {
            self.successMessage(pyOut)
          }
        })
      }
    },
    // start file export to user-supplied destination
    exportFiles () {
      const path = require('path')
      const remote = require('electron').remote
      const app = remote.app
      const dialog = remote.dialog

      // prompt user for output directory and call python script
      dialog.showOpenDialog({ properties: ['openDirectory', 'createDirectory'] }).then(result => {
        const outDir = result.filePaths[0].toString()

        // create temp JSON file with current state
        const homeDir = app.getPath('home')
        const brDir = path.join(homeDir, 'bulk-reviewer')
        const jsonTempFile = path.join(brDir, this.sessionNameWithoutSpaces + '_temp.json')
        this.saveToJSONFile(jsonTempFile, true)

        // close modal
        this.isExportModalActive = false

        // build script parameters
        let script = this.getScriptPath()

        let scriptParameters = [
          script,
          '--export',
          jsonTempFile,
          outDir,
          'export' // can be any string
        ]
        if (this.exportType === 'private') {
          scriptParameters.splice(1, 0, '--pii')
        }
        if (this.exportUnallocatedFiles === true) {
          scriptParameters.splice(1, 0, '--unallocated')
        }
        if (this.restoreDates === true) {
          scriptParameters.splice(1, 0, '--restore_dates')
        }
        if (this.exportFlat === true) {
          scriptParameters.splice(1, 0, '--flat')
        }
        if (this.brSession.disk_image === true) {
          scriptParameters.splice(1, 0, '-d')
        }

        // call python backend
        this.callBackend(scriptParameters)
      })
    },
    // trigger backend to write tar exclude file
    downloadTarExcludeFile () {
      const path = require('path')
      const remote = require('electron').remote
      const app = remote.app
      const dialog = remote.dialog

      // show user dialog to select file to save to
      let defaultTarExcludeFilename = this.sessionNameWithoutSpaces + '_tar_exclude.txt'
      dialog.showSaveDialog({ defaultPath: defaultTarExcludeFilename }).then(result => {
        const outFile = result.filePath
        // create temp JSON file with current state
        const homeDir = app.getPath('home')
        const brDir = path.join(homeDir, 'bulk-reviewer')
        const jsonTempFile = path.join(brDir, this.sessionNameWithoutSpaces + '_temp.json')
        this.saveToJSONFile(jsonTempFile, true)

        // build script parameters
        let scriptParameters = [
          this.getScriptPath(),
          '--export',
          '--tar',
          jsonTempFile,
          outFile,
          'export' // can be any string
        ]

        // call python backend
        this.callBackend(scriptParameters)
      })
    },
    // display in progress message while file export occurs
    inProgressMessage () {
      this.$toast.open({
        message: 'File export in progress...'
      })
    },
    // display success message in dialog
    successMessage (msg) {
      this.$dialog.alert({
        title: 'Success',
        message: msg
      })
    },
    // display error message in dialog
    errorMessage (msg) {
      this.$dialog.alert({
        title: 'Error',
        message: msg,
        type: 'is-danger',
        hasIcon: true,
        icon: 'times-circle',
        iconPack: 'fa'
      })
    }
  },
  computed: {
    brSession () {
      return this.$store.state.BRSession.brSession
    },
    fileCount () {
      return this.$store.state.BRSession.brSession.files.length
    },
    featureCount () {
      // filter out dismissed features
      let features = this.$store.state.BRSession.brSession.features
      let notDismissed = features.filter(f => f.dismissed !== true)
      return notDismissed.length
    },
    filesWithFeatures () {
      let files = this.$store.state.BRSession.brSession.files
      return files.filter(f => f.feature_count > 0)
    },
    filesWithFeaturesCount () {
      return this.filesWithFeatures.length
    },
    noSelection () {
      return this.selected === null
    },
    selectedFileFeatures () {
      let features = this.$store.state.BRSession.brSession.features
      let fileFeatures = features.filter(f => f.file === this.selected.id)
      return fileFeatures
    },
    selectedFileFeatureCount () {
      // filter dismissed features from selectedFileFeatures if file is selected
      if (!this.noSelection) {
        let notDismissedFileFeatures = this.selectedFileFeatures.filter(f => f.dismissed !== true)
        return notDismissedFileFeatures.length
      } else {
        return this.featureCount
      }
    },
    currentFeatureContext () {
      return this.noSelection === true ? 'All files' : this.selected.filepath
    },
    tableDataComputed () {
      return this.noSelection === true ? this.brSession.features : this.selectedFileFeatures
    },
    sessionNameWithoutSpaces () {
      return this.brSession.name.replace(/\s/g, '')
    },
    atLeastOneExportOption () {
      // return true if at least one condition for export options is met
      return this.exportType === 'private' || this.brSession.disk_image === true
    }
  }
}
</script>