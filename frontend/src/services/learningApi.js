import { accountApi } from './accountApi'

export const learningApi = {
  getLevels() {
    return accountApi('/levels')
  },

  getLevelLessons(levelID) {
    return accountApi(`/levels/${levelID}/lessons`)
  },

  getProgress(childID) {
    return accountApi(`/children/${childID}/progress`)
  },

  updateProgress(childID, lessonID, payload) {
    return accountApi(`/children/${childID}/lessons/${lessonID}/progress`, {
      method: 'POST',
      body: payload,
    })
  },
}
