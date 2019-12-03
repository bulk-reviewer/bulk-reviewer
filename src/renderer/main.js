import Vue from 'vue'
import axios from 'axios'

import App from './App'
import router from './router'
import store from './store'

import Buefy from 'buefy'
import 'buefy/dist/buefy.css'

import vSelect from 'vue-select'

import './assets/custom.css'

import { library } from '@fortawesome/fontawesome-svg-core'
import { fas } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

import { remote } from 'electron'

remote.globalShortcut.register('CommandOrControl+Shift+K', () => {
  remote.BrowserWindow.getFocusedWindow().webContents.openDevTools()
})

window.addEventListener('beforeunload', () => {
  remote.globalShortcut.unregisterAll()
})

if (!process.env.IS_WEB) Vue.use(require('vue-electron'))
Vue.http = Vue.prototype.$http = axios
Vue.config.productionTip = false

library.add(fas)
Vue.component('vue-fontawesome', FontAwesomeIcon)
Vue.use(Buefy, {
  defaultIconComponent: 'vue-fontawesome',
  defaultIconPack: 'fas'
})

Vue.component('v-select', vSelect)

/* eslint-disable no-new */
new Vue({
  components: { App },
  router,
  store,
  template: '<App/>'
}).$mount('#app')
