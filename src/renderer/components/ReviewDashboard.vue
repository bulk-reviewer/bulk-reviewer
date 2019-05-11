<template>
  <section class="padded">
    <!-- Header -->
    <div class="container-fluid">
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
    </div>

    <div class="container-fluid">
      
      <!-- Checkbox for disk image export options -->
      <div style="margin-bottom: 15px;"
        <b-checkbox
          style="margin-top: 15px;"
          size="is-small"
          type="is-info"
          v-model="restoreDates"
          v-show="brSession.disk_image === true">
          Restore modified dates for exported files
        </b-checkbox>
        <br>
        <b-checkbox
          size="is-small"
          type="is-info"
          v-model="exportUnallocatedFiles"
          v-show="brSession.disk_image === true">
          Include unallocated files in file exports
        </b-checkbox>
      </div>

      <!-- Actions -->
      <div class="container-fluid"
        <b-dropdown aria-role="list" style="margin-bottom: 15px;">
          <button class="button is-light" slot="trigger">
            <span>Actions</span>
            <b-icon icon="caret-down"></b-icon>
          </button>

          <b-dropdown-item
            aria-role="listitem"
            @click="openSaveFileDialog">
            Save
          </b-dropdown-item>

          <b-dropdown-item
            aria-role="listitem"
            @click="exportFiles(false)">
            Export cleared files (no PII)
          </b-dropdown-item>

          <b-dropdown-item
            aria-role="listitem"
            @click="exportFiles(true)">
            Export private files
          </b-dropdown-item>

          <b-dropdown-item
            aria-role="listitem"
            @click="downloadCSVFeaturesReport">
            Download CSV report
          </b-dropdown-item>
        </b-dropdown>
      </div>

      <!-- File selector -->
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
      
    </div>
    
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
      restoreDates: false
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
      shell.openItem(fileAbspath)
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
      dialog.showSaveDialog({ defaultPath: defaultFileName }, (filename) => {
        this.saveToJSONFile(filename.toString(), false)
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
      dialog.showSaveDialog({ defaultPath: defaultCSVReportName }, (filename) => {
        let csvFile = filename.toString()
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
        if (!this.guessPyPackaged()) {
          return path.join(PY_FOLDER, PY_MODULE + '.py')
        }
        if (process.platform === 'win32') {
          return path.join(PY_DIST_FOLDER, PY_MODULE, PY_MODULE + '.exe')
        }
        return path.join(PY_DIST_FOLDER, PY_MODULE, PY_MODULE)
      }
    },
    // copy files from source from user-supplied destination
    // copy files with pii if piiBoolean is true
    // copy files without pii if piiBoolean is false
    exportFiles (piiBoolean) {
      const path = require('path')
      const remote = require('electron').remote
      const app = remote.app
      const dialog = remote.dialog

      // prompt user for output directory and call python script
      dialog.showOpenDialog({ properties: ['openDirectory', 'createDirectory'] }, (dirName) => {
        const outDir = dirName.toString()

        // create temp JSON file with current state
        const homeDir = app.getPath('home')
        const brDir = path.join(homeDir, 'bulk-reviewer')
        const jsonTempFile = path.join(brDir, this.sessionNameWithoutSpaces + '_temp.json')
        this.saveToJSONFile(jsonTempFile, true)

        // build script parameters
        let script = this.getScriptPath()

        let scriptParameters = [
          script,
          '--export',
          jsonTempFile,
          outDir,
          'export' // can be any string
        ]
        if (piiBoolean === true) {
          scriptParameters.splice(1, 0, '--pii')
        }
        if (this.exportUnallocatedFiles === true) {
          scriptParameters.splice(1, 0, '--unallocated')
        }
        if (this.restoreDates === true) {
          scriptParameters.splice(1, 0, '--restore_dates')
        }
        if (this.brSession.disk_image === true) {
          scriptParameters.splice(1, 0, '-d')
        }

        // run python script/executable
        if (app.isPackaged) {
          // fix for mac os to make system PATH available to node
          const fixPath = require('fix-path')
          fixPath()

          // spawn command in shell
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
    }
  }
}
</script>