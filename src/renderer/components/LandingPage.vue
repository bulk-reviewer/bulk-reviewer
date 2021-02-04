<template>
  <section class="hero">
    <div class="hero-body">
      <div class="container">
        <h1 class="title">
          Identify, review, and remove sensitive files
        </h1>
      </div>
      <div class="container">
        <br><br>
        <button @click="newSession" class="button is-primary">Scan new directory or disk image</button>
        <button @click="loadFromFile" class="button">Load from JSON file</button>
      </div>
    </div>
  </section>
</template>

<script>
const remote = require('electron').remote
const dialog = remote.dialog

export default {
  name: 'landing-page',
  methods: {
    loadFromFile () {
      dialog.showOpenDialog({ properties: ['openFile'] }).then(result => {
        let jsonFile = result.filePaths[0].toString()
        this.$store.dispatch('loadFromJSON', jsonFile)
        this.$router.push('review')
      })
    },
    newSession () {
      this.$router.push('new-session')
    }
  },
  computed: {
    brSession () {
      return this.$store.state.BRSession.brSession
    }
  }
}
</script>