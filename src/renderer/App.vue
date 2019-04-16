<template>
  <div id="app">
    <header class="app-header">
      <top-navbar/>
    </header>
    <main>
      <router-view></router-view>
    </main>
  </div>
</template>

<script>
import TopNavbar from './components/TopNavbar'

export default {
  name: 'BulkReviewer',
  components: { TopNavbar }
}
</script>
