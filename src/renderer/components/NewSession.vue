<template>
  <section class="padded">
    <h1 class="title is-3">New session</h1>
    <form ref="form" @submit.prevent="onSubmit">
      
      <b-field label="Name">
        <b-input
          v-model="name"
          placeholder="Name, accession number, or other identifier"
          style="max-width: 700px;"
          required>
        </b-input>
      </b-field>

      <!-- Disk image? -->
      <b-field label="Source type">
        <b-select
          placeholder="Select type"
          v-model="sourceType"
          required>
          <option value="directory">Directory</option>
          <option value="diskImage">Disk Image</option>
        </b-select>
      </b-field>

      <b-field>
        <section>
          <button
            class="button is-light"
            @click.prevent="chooseDirectory"
            v-if="sourceType === 'directory'">
            Choose directory
          </button>
          <button
            class="button is-light"
            @click.prevent="chooseFile"
            v-else>
            Choose file
          </button>
          <div style="margin: 5px;">
            <span v-if="sourcePath">
              {{ sourcePath }}
              <!-- button to reset sourcePath -->
              <button class="button is-light is-small" @click="resetSourcePath">
                <b-icon icon="times"></b-icon>
              </button>
            </span>
            <span v-else>
              None selected.
            </span>
          </div>
        </section>
    </b-field>

    <!-- Named entity extraction -->

    <b-field label="Regular expressions file">
      <section>
        <button
          class="button is-light"
          @click.prevent="chooseRegexFile">
          Choose file
        </button>
        <div style="margin: 5px;">
          <span v-if="regexFilePath">
            {{ regexFilePath }}
            <!-- button to reset sourcePath -->
            <button class="button is-light is-small" @click="resetRegexFilePath">
              <b-icon icon="times"></b-icon>
            </button>
          </span>
          <span v-else>
            None selected.
          </span>
        </div>
      </section>
    </b-field>

    <b-field label="Social Security Number identification mode">
      <b-select
        placeholder="SSN mode"
        v-model="ssnMode"
        required>
        <option value="0"><strong>Strict:</strong> must be labelled "SSN" (ssn_mode=0)</option>
        <option value="1"><strong>Medium:</strong> No “SSN” required; dashes required (ssn_mode=1)</option>
        <option value="2"><strong>Lenient:</strong> No dashes required (ssn_mode=2)</option>
      </b-select>
    </b-field>

    <b-field label="Scanner options">
      <section>
        <div class="field">
          <b-checkbox v-model="includeExifResults">Include EXIF metadata in results</b-checkbox>
        </div>
        <div class="field">
          <b-checkbox v-model="includeNetworkResults">Include network/web data (domains, URLs, RFC822 headers, HTTP logs) in results</b-checkbox>
        </div>
      </section>
    </b-field>

      <button 
        class="button is-success"
        @click.prevent="onSubmit"
        :disabled="isDisabled">
        Start scan
      </button>
      <button 
        class="button is-light"
        @click="resetForm">
        Reset
      </button>

    </form>

    <!-- Loading indicator -->
    <b-loading :is-full-page="false" :active.sync="loading" :can-cancel="false"></b-loading>

  </section>
</template>

<script>
const remote = require('electron').remote
const dialog = remote.dialog
const app = remote.app

export default {
  name: 'new-session',
  data () {
    return {
      isDisabled: false,
      name: '',
      sourceType: 'directory',
      sourcePath: '',
      regexFilePath: '',
      ssnMode: '0',
      loading: false,
      includeExifResults: false,
      includeNetworkResults: false
    }
  },
  methods: {
    chooseDirectory () {
      dialog.showOpenDialog({ properties: ['openDirectory'] }, (dirName) => {
        this.sourcePath = dirName.toString()
      })
    },
    chooseFile () {
      dialog.showOpenDialog({ properties: ['openFile'] }, (filename) => {
        this.sourcePath = filename.toString()
      })
    },
    chooseRegexFile () {
      dialog.showOpenDialog({ properties: ['openFile'] }, (filename) => {
        this.regexFilePath = filename.toString()
      })
    },
    resetSourcePath () {
      this.sourcePath = ''
    },
    resetRegexFilePath () {
      this.regexFilePath = ''
    },
    resetForm () {
      this.isDisabled = false
      this.name = ''
      this.sourceType = 'directory'
      this.sourcePath = ''
      this.regexFilePath = ''
      this.ssnMode = '0'
      this.includeExifResults = false
      this.includeNetworkResults = false
    },
    // determine if python is packaged as executable by checking
    // for presence of backend_dist directory
    guessPackaged () {
      const path = require('path')
      const PY_DIST_FOLDER = path.join(__dirname, '../../main/', 'backend_dist')
      console.log('guessPackaged:', require('fs').existsSync(PY_DIST_FOLDER))
      return require('fs').existsSync(PY_DIST_FOLDER)
    },
    // get path to script or executable as appropriate
    getScriptPath () {
      const path = require('path')
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
    },
    // run br_processor python script. on completion, display errors
    // or, if no errors, load data from JSON file to store and
    // push router to ReviewDashboard component
    runPythonProcess () {
      const path = require('path')
      const homeDir = app.getPath('home')
      const brDir = path.join(homeDir, 'bulk-reviewer')

      let script = this.getScriptPath()

      let sessionParameters = [
        script,
        '--ssn',
        parseInt(this.ssnMode),
        this.sourcePath,
        brDir,
        this.name
      ]
      if (this.sourceType === 'diskImage') {
        sessionParameters.splice(1, 0, '-d')
      }
      if (this.includeExifResults === true) {
        sessionParameters.splice(1, 0, '--include_exif')
      }
      if (this.includeNetworkResults === true) {
        sessionParameters.splice(1, 0, '--include_network')
      }
      if (this.regexFilePath.length > 0) {
        sessionParameters.splice(1, 0, '--regex')
        sessionParameters.splice(2, 0, this.regexFilePath)
      }

      console.log(sessionParameters)

      if (this.guessPackaged()) {
        let pyProc = require('child_process').execFile(script, sessionParameters.slice(1))
        let jsonPath = ''
        let pyErrors = ''

        pyProc.stdout.on('data', function (data) {
          jsonPath += data.toString()
        })

        pyProc.stderr.on('data', function (data) {
          let errorMessage = data.toString()
          // ignore 'Attempt to open' disk image messages
          if (!errorMessage.includes('Attempt to open')) {
            pyErrors += errorMessage
          }
        })

        // throw error message or load review dashboard
        // when python script has completed
        let self = this
        pyProc.stdout.on('end', function (data) {
          // catch errors
          if (pyErrors.length > 0) {
            self.loading = false
            self.isDisabled = false
            self.errorMessage(`ERROR: ${pyErrors}`)
          // if no errors, load review dashboard
          } else {
            let jsonFile = jsonPath.trim()
            self.loading = false
            self.$store.dispatch('loadFromJSON', jsonFile)
            self.$router.push('review')
          }
        })
      } else {
        let pyProc = require('child_process').spawn('python3', sessionParameters)
        let jsonPath = ''
        let pyErrors = ''

        pyProc.stdout.on('data', function (data) {
          jsonPath += data.toString()
        })

        pyProc.stderr.on('data', function (data) {
          let errorMessage = data.toString()
          // ignore 'Attempt to open' disk image messages
          if (!errorMessage.includes('Attempt to open')) {
            pyErrors += errorMessage
          }
        })

        // throw error message or load review dashboard
        // when python script has completed
        let self = this
        pyProc.stdout.on('end', function (data) {
          // catch errors
          if (pyErrors.length > 0) {
            self.loading = false
            self.isDisabled = false
            self.errorMessage(`ERROR: ${pyErrors}`)
          // if no errors, load review dashboard
          } else {
            let jsonFile = jsonPath.trim()
            self.loading = false
            self.$store.dispatch('loadFromJSON', jsonFile)
            self.$router.push('review')
          }
        })
      }
    },
    onSubmit () {
      if (!this.sourcePath) {
        this.errorMessage('Source directory or disk image required')
      } else {
        // disable submit button
        this.isDisabled = true

        // switch status indicators
        this.loading = true

        // kick off br_processor
        this.runPythonProcess()
      }
    },
    // display error message in toast for 5 seconds
    errorMessage (msg) {
      this.$toast.open({
        duration: 5000,
        message: msg,
        position: 'is-bottom',
        type: 'is-danger'
      })
    }
  },
  computed: {
    brSession () {
      return this.$store.state.BRSession.brSession
    }
  }
}
</script>