// store/index.js
import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    logs: []
  },
  mutations: {
    ADD_LOG(state, logEntry) {
      state.logs.push(logEntry);
    }
  },
  actions: {
    logAction({ commit }, logEntry) {
      commit('ADD_LOG', logEntry);
    }
  }
});