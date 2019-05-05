<template>
  <div
    class="container-fluid"
    id="featureExplorer">

    <h2 class="title is-4">Features ({{ selectedFileFeatureCount }})</h2>
    <h4 class="subtitle is-6">
      Showing results from: {{ currentFeatureContext }}
      <button
        v-show="selectedFile !== null"
        class="button is-small is-info"
        @click="openFileOnDesktop(selectedFile.filepath)">
        Open
      </button>
      <button 
        v-show="selectedFile !== null"
        class="button is-small is-danger"
        @click="nullifySelected">
        x Return to all files
      </button>
    </h4>

    <!-- Feature filters -->
    <b-field grouped group-multiline>
      
      <!-- Feature type -->
      <b-select v-model="typeFilter">
        <option value="all">
          Feature type: All 
          ({{ selectedFileFeatureCount }})
        </option>
        <option value="ssn">
          Social Security Number (USA)
          ({{ featureCountByType(ssnFilter) }})
        </option>
        <option value="sin">
          Social Insurance Number (Canada)
          ({{ featureCountByType(sinFilter) }})
        </option>
        <option value="ccn">
          Credit card number 
          ({{ featureCountByType(ccnFilter) }})
        </option>
        <option value="phone">
          Phone number 
          ({{ featureCountByType(phoneFilter) }})
        </option>
        <option value="email">
          Email address 
          ({{ featureCountByType(emailFilter) }})
        </option>
        <option value="regex">
          User-supplied regular expressions 
          ({{ featureCountByType(regexFilter) }})
        </option>
        <option value="url">
          URL 
          ({{ featureCountByType(urlFilter) }})
        </option>
        <option value="domain">
          Domain 
          ({{ featureCountByType(domainFilter) }})
        </option>
        <option value="rfc822">
          Email/HTTP header (RFC822) 
          ({{ featureCountByType(rfc822Filter) }})
        </option>
        <option value="httplog">
          HTTP log 
          ({{ featureCountByType(httplogFilter) }})
        </option>
        <option value="gps">
          GPS data 
          ({{ featureCountByType(gpsFilter) }})
        </option>
        <option value="exif">
          EXIF metadata 
          ({{ featureCountByType(exifFilter) }})
        </option>
      </b-select>

      <!-- Show all details -->
      <b-switch
        v-model="showAllDetails"
        v-on:input="toggleShowAllDetails()">
        Show details
      </b-switch>

      <!-- Button group -->
      <b-field grouped style="margin-left: 30px; margin-top: 10px;">

        <!-- Dismiss all button -->
        <button
          class="button is-small is-light"
          style="margin-left: 5px;"
          @click="dismissAllFeatures">
          x Dismiss all
        </button>

        <!-- Undismiss all button -->
        <button
          class="button is-small is-primary"
          style="margin-left: 5px;"
          @click="undismissAllFeatures">
          Undo all
        </button>

      </b-field>

    </b-field>

    <!-- Feature table -->
    <b-table
      :data="tableDataToDisplay"
      :opened-detailed="defaultOpenedDetails"
      :paginated="true"
      :per-page="perPage"
      :current-page.sync="currentPage"
      :default-sort-direction="defaultSortDirection"
      default-sort="feature_type"
      detail-key="id"
      :show-detail-icon="true"
      detailed
      focusable
      narrowed>

      <template slot-scope="props">
        
        <b-table-column
          field="feature"
          label="Feature"
          :class="{'dismissed':props.row.dismissed === true}"
          sortable>
          {{ unescapeText(props.row.feature) }}
        </b-table-column>

        <b-table-column
          field="feature_type"
          label="Type"
          :class="{'dismissed':props.row.dismissed === true}"
          sortable>
          {{ props.row.feature_type }}
        </b-table-column>

        <b-table-column
          field="note"
          label="Note"
          sortable>
          <span v-if="props.row.note !== null">
            {{ props.row.note }}
          </span>
          <span class="dismissed" v-else>
            n/a
          </span>
          <!-- Edit note button -->
          <button 
            class="button is-small"
            @click="openNoteDialog(props.row.id)">
            <b-tooltip
              label="Edit note"
              position="is-right"
              type="is-light">
              <b-icon icon="pencil-alt"></b-icon>
            </b-tooltip>
          </button>
          <!-- Delete note button -->
          <button
            class="button is-small"
            v-show="props.row.note !== null"
            @click="deleteNote(props.row.id)">
            <b-tooltip
              label="Delete note"
              position="is-right"
              type="is-light">
              <b-icon icon="times"></b-icon>
            </b-tooltip>
          </button>
          
        </b-table-column>

        <b-table-column
          field="dismissed"
          label="Dismiss"
          :class="{'dismissed':props.row.dismissed === true}"
          sortable>
          <span v-if="props.row.dismissed === false">
            <button
              class="button is-small is-light"
              @click="toggleFeatureDismissedStatus(props.row.id)">
              x Dismiss
            </button>
          </span>
          <span v-else>
            Dismissed
            <button
              class="button is-small is-primary"
              @click="toggleFeatureDismissedStatus(props.row.id)">
              Undo
            </button>
          </span>
        </b-table-column>

      </template>

      <!-- Expandable detail (context) -->
      <template slot="detail" slot-scope="props">

        <article class="media">
          <div class="media-content" >
            <div class="content">
              <!-- Filepath -->
              <p>
                <strong>File:</strong> {{ props.row.filepath }}
                <button
                  class="button is-small is-info"
                  @click="openFileOnDesktop(props.row.filepath)">
                  Open
                </button>
              </p>
              <!-- Feature in context -->
              <p v-if="props.row.context"><strong>Feature in context:</strong> {{ unescapeText(props.row.context) }}</p>
              <p v-else><strong>Feature in context:</strong> n/a</p>
              <!-- Forensic path (directories only) -->
              <span v-if="props.row.forensic_path" style="margin-top: 5px;">
                <p><strong>Forensic path:</strong> {{ unescapeText(props.row.forensic_path) }}</p>
              </span>
              <span v-else></span>
            </div>
          </div>
        </article>

      </template>

    </b-table>
  </div>
</template>

<script>
export default {
  name: 'feature-table',
  props: [ 'tableData', 'currentFeatureContext', 'selected' ],
  data () {
    return {
      defaultSortDirection: 'desc',
      currentPage: 1,
      perPage: 10,
      typeFilter: 'all',
      showAllDetails: false,
      defaultOpenedDetails: []
    }
  },
  methods: {
    // display text after unescaping characters
    unescapeText (escapedText) {
      return escapedText.replace(/\\x[a-fA-F0-9]{2}/g, String.fromCharCode('$1'))
    },
    // toggle dismissed boolean for feature with given id
    toggleFeatureDismissedStatus (featureID) {
      this.$store.dispatch('toggleFeatureDismissed', featureID)
    },
    // set dismissed for all features in table to true
    dismissAllFeatures () {
      this.$store.dispatch('setFeaturesDismissedTrue', this.selectedIDArray)
    },
    // set dismissed for all features in table to false
    undismissAllFeatures () {
      this.$store.dispatch('setFeaturesDismissedFalse', this.selectedIDArray)
    },
    // open file using default system program
    // doesn't work for disk images
    openFileOnDesktop (myFile) {
      const shell = require('electron').shell
      const path = require('path')
      let fileAbspath = path.join(this.$store.state.BRSession.brSession.source_path, myFile)
      shell.openItem(fileAbspath)
    },
    // send signal to parent component to make selected null
    nullifySelected () {
      this.$emit('nullify')
    },
    // return count of non-dismissed features in given array
    // used for the counts in feature type selector
    featureCountByType (filteredFeatureArray) {
      let filteredNotDismissed = filteredFeatureArray.filter(f => f.dismissed !== true)
      return filteredNotDismissed.length
    },
    // if switch has been toggled on, expand details for all rows
    // if switch has been toggled off, collapse details for all rows
    toggleShowAllDetails () {
      if (this.showAllDetails === true) {
        let arrayOfAllFeatureIDs = this.tableData.map(f => f.id)
        this.defaultOpenedDetails = arrayOfAllFeatureIDs
      } else {
        this.defaultOpenedDetails = []
      }
    },
    // open dialog to edit note and trigger dispatch on confirm
    openNoteDialog (featureID) {
      let featureIndex = featureID - 1
      let currentNote = this.brSession.features[featureIndex].note
      let notePlaceholder = currentNote === null ? '' : currentNote
      this.$dialog.prompt({
        title: `Edit note`,
        inputAttrs: {
          type: 'string',
          value: notePlaceholder
        },
        onConfirm: (value) => this.dispatchEditNoteVuexAction(featureID, value)
      })
    },
    // dispatch Vuex action to edit note
    dispatchEditNoteVuexAction (featureID, editedNote) {
      let notePayload = {
        'featureID': featureID,
        'note': editedNote
      }
      this.$store.dispatch('editFeatureNote', notePayload)
    },
    // dispatch Vuex action to delete note
    deleteNote (featureID) {
      this.$store.dispatch('deleteFeatureNote', featureID)
    }
  },
  computed: {
    selectedFile () {
      return this.selected
    },
    brSession () {
      return this.$store.state.BRSession.brSession
    },
    // return true if no file currently selected
    // otherwise return false
    noSelection () {
      return this.selectedFile === null
    },
    // return count of features in session, not counting dismissed
    featureCount () {
      let features = this.$store.state.BRSession.brSession.features
      let notDismissed = features.filter(f => f.dismissed !== true)
      return notDismissed.length
    },
    // return array of features in currently selected file
    selectedFileFeatures () {
      let features = this.$store.state.BRSession.brSession.features
      let fileFeatures = features.filter(f => f.file === this.selectedFile.id)
      return fileFeatures
    },
    // return count of features
    // if file is currently selected, filter out dismissed features first
    selectedFileFeatureCount () {
      if (!this.noSelection) {
        let notDismissedFileFeatures = this.selectedFileFeatures.filter(f => f.dismissed !== true)
        return notDismissedFileFeatures.length
      } else {
        return this.featureCount
      }
    },
    // return array of IDs from tableDataToDisplay
    selectedIDArray () {
      return this.tableDataToDisplay.map(f => f.id)
    },
    // filter table data by feature type
    // if not feature type selected, return tableData
    tableDataToDisplay () {
      switch (this.typeFilter) {
        case 'all':
          return this.tableData
        case 'ssn':
          return this.ssnFilter
        case 'sin':
          return this.sinFilter
        case 'ccn':
          return this.ccnFilter
        case 'phone':
          return this.phoneFilter
        case 'email':
          return this.emailFilter
        case 'regex':
          return this.regexFilter
        case 'url':
          return this.urlFilter
        case 'domain':
          return this.domainFilter
        case 'rfc822':
          return this.rfc822Filter
        case 'httplog':
          return this.httplogFilter
        case 'gps':
          return this.gpsFilter
        case 'exif':
          return this.exifFilter
      }
    },
    ssnFilter () {
      return this.tableData.filter(f => f.feature_type === 'Social Security Number (USA)')
    },
    sinFilter () {
      return this.tableData.filter(f => f.feature_type === 'Social Insurance Number (Canada)')
    },
    ccnFilter () {
      return this.tableData.filter(f => f.feature_type === 'Credit card number')
    },
    phoneFilter () {
      return this.tableData.filter(f => f.feature_type === 'Phone number')
    },
    emailFilter () {
      return this.tableData.filter(f => f.feature_type === 'Email address')
    },
    regexFilter () {
      return this.tableData.filter(f => f.feature_type === 'Regular expression')
    },
    urlFilter () {
      return this.tableData.filter(f => f.feature_type === 'URL')
    },
    domainFilter () {
      return this.tableData.filter(f => f.feature_type === 'Domain')
    },
    rfc822Filter () {
      return this.tableData.filter(f => f.feature_type === 'Email/HTTP header (RFC822)')
    },
    httplogFilter () {
      return this.tableData.filter(f => f.feature_type === 'HTTP log')
    },
    gpsFilter () {
      return this.tableData.filter(f => f.feature_type === 'GPS data')
    },
    exifFilter () {
      return this.tableData.filter(f => f.feature_type === 'EXIF metadata')
    }
  }
}
</script>