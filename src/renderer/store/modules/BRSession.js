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
  SET_FEATURES_DISMISSED_TRUE (state, featureArray) {
    featureArray.forEach(function (featureID) {
      let index = featureID - 1
      state.brSession.features[index].dismissed = true
    })
  },
  SET_FEATURES_DISMISSED_FALSE (state, featureArray) {
    featureArray.forEach(function (featureID) {
      let index = featureID - 1
      state.brSession.features[index].dismissed = false
    })
  },
  TOGGLE_FILE_VERIFIED (state, fileID) {
    let index = fileID - 1
    state.brSession.files[index].verified = !state.brSession.files[index].verified
  },
  EDIT_FEATURE_NOTE (state, notePayload) {
    let index = notePayload.featureID - 1
    state.brSession.features[index].note = notePayload.note
  },
  DELETE_FEATURE_NOTE (state, featureID) {
    let index = featureID - 1
    state.brSession.features[index].note = null
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
  setFeaturesDismissedTrue ({ commit }, featureArray) {
    commit('SET_FEATURES_DISMISSED_TRUE', featureArray)
  },
  setFeaturesDismissedFalse ({ commit }, featureArray) {
    commit('SET_FEATURES_DISMISSED_FALSE', featureArray)
  },
  toggleFileVerified ({ commit }, fileID) {
    commit('TOGGLE_FILE_VERIFIED', fileID)
  },
  editFeatureNote ({ commit }, notePayload) {
    commit('EDIT_FEATURE_NOTE', notePayload)
  },
  deleteFeatureNote ({ commit }, featureID) {
    commit('DELETE_FEATURE_NOTE', featureID)
  }
}

export default {
  state,
  mutations,
  actions
}
