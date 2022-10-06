<template>
  <nav class="navbar is-dark" role="navigation" aria-label="main navigation">
    <div class="navbar-brand">
      <router-link class="navbar-item" to="/">
        <h1 class="title is-4" style="color: white;">Bulk Reviewer</h1>
      </router-link>
      <router-link class="navbar-item" to="/new-session">
        <span style="color: white; margin-left: 5px; margin-right: 5px;">New</span>
      </router-link>
      <router-link class="navbar-item" to="#">
        <span style="color: white; margin-left: 5px; margin-right: 5px;" @click="loadFromFile">Load</span>
      </router-link>
    </div>
  </nav>
</template>

<script>
const remote = require('@electron/remote')
const dialog = remote.dialog

export default {
  name: 'TopNavbar',
  methods: {
    loadFromFile () {
      dialog.showOpenDialog(remote.getCurrentWindow(), { properties: ['openFile'] }).then(result => {
        let jsonFile = result.filePaths[0].toString()
        this.$store.dispatch('loadFromJSON', jsonFile)
        this.$router.push('review')
      })
    }
  }
}
</script>