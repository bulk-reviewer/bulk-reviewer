const state = {
  brSession: {}
}

const mutations = {
  LOAD_JSON_DATA (state, data) {
    state.brSession = data
  },
  TOGGLE_FEATURE_CLEARED (state, featureID) {
    let index = featureID - 1
    state.brSession.features[index].cleared = !state.brSession.features[index].cleared
  },
  TOGGLE_FILE_VERIFIED (state, fileID) {
    let index = fileID - 1
    state.brSession.files[index].verified = !state.brSession.files[index].verified
  }
}

const actions = {
  loadFromJSON ({ commit }, jsonFile) {
    let data = JSON.parse(require('fs').readFileSync(jsonFile, 'utf8'))
    console.log(data)
    commit('LOAD_JSON_DATA', data)
  },
  toggleFeatureCleared ({ commit }, featureID) {
    commit('TOGGLE_FEATURE_CLEARED', featureID)
  },
  toggleFileVerified ({ commit }, fileID) {
    commit('TOGGLE_FILE_VERIFIED', fileID)
  }
}

export default {
  state,
  mutations,
  actions
}
