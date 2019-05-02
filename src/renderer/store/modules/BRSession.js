const state = {
  brSession: {}
}

const mutations = {
  LOAD_JSON_DATA (state, data) {
    state.brSession = data
  },
  TOGGLE_FEATURE_DISMISSED (state, featureID) {
    let index = featureID - 1
    state.brSession.features[index].dismissed = !state.brSession.features[index].dismissed
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
  toggleFeatureDismissed ({ commit }, featureID) {
    commit('TOGGLE_FEATURE_DISMISSED', featureID)
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
