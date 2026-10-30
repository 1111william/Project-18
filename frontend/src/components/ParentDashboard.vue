<script setup>
import { ref, watch } from 'vue'
import { accountApi } from '../services/accountApi'

// The children list comes from AccountApp, which already loads GET /api/children.
const props = defineProps({
  children: { type: Array, default: () => [] },
})

const reports = ref({})
const openChildID = ref(null)
let loadRound = 0

// Progress and quiz results come from Zihao's and Yuchen's routes.
// Until those routes are merged they return 404, and the card shows "No data yet".
async function optional(path) {
  try {
    return await accountApi(path)
  } catch {
    return null
  }
}

async function loadReport(child) {
  const id = child.childID
  const [home, progress, quizResults] = await Promise.all([
    optional(`/children/${id}/home`),
    optional(`/children/${id}/progress`),
    optional(`/children/${id}/quiz-results`),
  ])

  const progressLessons = Array.isArray(progress?.lessons) ? progress.lessons : null
  const results = Array.isArray(quizResults) ? quizResults : []
  const scores = results.map(result => result.score).filter(score => typeof score === 'number')

  return {
    failed: !home,
    summary: home?.summary ?? { lessonCount: 0, completedLessons: 0, overallProgress: 0 },
    lessons: home?.lessons ?? [],
    minutes: progressLessons
      ? Math.round(progressLessons.reduce((total, lesson) => total + (lesson.secondsSpent || 0), 0) / 60)
      : null,
    latestQuiz: results[0] ?? null,
    averageScore: scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null,
    attempts: results.length,
  }
}

watch(
  () => props.children,
  async (list) => {
    const round = ++loadRound
    const entries = await Promise.all(list.map(async child => [child.childID, await loadReport(child)]))
    if (round === loadRound) reports.value = Object.fromEntries(entries)
  },
  { immediate: true },
)

function formatMinutes(minutes) {
  if (minutes === null) return 'No data yet'
  if (minutes < 60) return `${minutes} min`
  return `${Math.floor(minutes / 60)} h ${minutes % 60} min`
}

function toggle(childID) {
  openChildID.value = openChildID.value === childID ? null : childID
}
</script>

<template>
  <div class="parent-dashboard">
    <h2>Children</h2>
    <p v-if="!children.length" class="muted">No child profiles yet. Add a child profile first.</p>

    <article v-for="child in children" :key="child.childID" class="child-card">
      <header class="child-head">
        <h3>{{ child.nickname }}</h3>
        <span class="level">{{ child.levelTitle || 'No level yet' }}</span>
      </header>

      <p v-if="!reports[child.childID]" class="muted">Loading…</p>
      <p v-else-if="reports[child.childID].failed" class="muted">Progress could not be loaded. Please try again later.</p>
      <template v-else>
        <div class="bar" role="progressbar" aria-label="Overall progress" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="reports[child.childID].summary.overallProgress">
          <span :style="{ width: reports[child.childID].summary.overallProgress + '%' }"></span>
        </div>
        <p class="progress-line">
          <strong>{{ reports[child.childID].summary.overallProgress }}%</strong>
          · {{ reports[child.childID].summary.completedLessons }} of {{ reports[child.childID].summary.lessonCount }} lessons completed
        </p>

        <dl class="stats">
          <div>
            <dt>Learning time</dt>
            <dd>{{ formatMinutes(reports[child.childID].minutes) }}</dd>
          </div>
          <div>
            <dt>Latest quiz</dt>
            <dd>{{ reports[child.childID].latestQuiz ? reports[child.childID].latestQuiz.score + '%' : 'No data yet' }}</dd>
          </div>
        </dl>

        <button class="secondary" type="button" :aria-expanded="openChildID === child.childID" @click="toggle(child.childID)">
          {{ openChildID === child.childID ? 'Hide Progress' : 'View Progress' }}
        </button>

        <div v-if="openChildID === child.childID" class="details">
          <h4>Lesson Progress</h4>
          <p v-if="!reports[child.childID].lessons.length" class="muted">No lessons in this level yet.</p>
          <ul v-else class="lesson-list">
            <li v-for="lesson in reports[child.childID].lessons" :key="lesson.lessonID">
              <span>{{ lesson.title }}</span>
              <span>{{ lesson.completed ? 'Completed' : lesson.percentComplete + '%' }}</span>
            </li>
          </ul>

          <h4>Quiz Results</h4>
          <p v-if="!reports[child.childID].attempts" class="muted">No quiz results yet.</p>
          <ul v-else class="lesson-list">
            <li><span>Latest quiz score</span><span>{{ reports[child.childID].latestQuiz.score }}%</span></li>
            <li><span>Average quiz score</span><span>{{ reports[child.childID].averageScore }}%</span></li>
            <li><span>Quizzes attempted</span><span>{{ reports[child.childID].attempts }}</span></li>
          </ul>
        </div>
      </template>
    </article>

    <section v-if="children.length" class="tip">
      <h4>Parent Recommendations</h4>
      <p>Encourage your child to practise Bangla letters for 10 minutes each day.</p>
    </section>
  </div>
</template>

<style scoped>
.parent-dashboard {
  display: grid;
  gap: 16px;
  margin-bottom: 20px;
}

h2 {
  margin: 8px 0 0;
}

.child-card {
  border: 1px solid #dce4d5;
  border-radius: 16px;
  background: #fff;
  padding: 20px 22px;
}

.child-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 14px;
}

.child-head h3 {
  margin: 0;
  font-size: 20px;
  overflow-wrap: anywhere;
}

.level {
  font-size: 14px;
  font-weight: 700;
  color: #547148;
  background: #f0f5e9;
  border-radius: 999px;
  padding: 4px 12px;
  white-space: nowrap;
}

.bar {
  height: 10px;
  border-radius: 999px;
  background: #eaf0df;
  overflow: hidden;
}

.bar span {
  display: block;
  height: 100%;
  background: #2c513e;
  border-radius: 999px;
}

.progress-line {
  margin: 10px 0 0;
  color: #4f5e63;
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0;
}

.stats div {
  background: #f3f6ed;
  border-radius: 12px;
  padding: 12px 14px;
}

.stats dt {
  font-size: 13px;
  color: #6c7f65;
}

.stats dd {
  margin: 2px 0 0;
  font-size: 18px;
  font-weight: 750;
}

.details {
  margin-top: 16px;
  border-top: 1px solid #e3e9dc;
  padding-top: 6px;
}

h4 {
  margin: 14px 0 8px;
  font-size: 16px;
}

.lesson-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.lesson-list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #eef2ea;
  font-size: 15px;
}

.lesson-list li span:last-child {
  color: #547148;
  font-weight: 700;
  white-space: nowrap;
}

.tip {
  background: #eaf2e2;
  border-radius: 12px;
  padding: 4px 18px 12px;
  color: #426035;
}

.tip p {
  margin: 0;
}

.muted {
  color: #6c7f65;
  margin: 0;
}

@media (max-width: 600px) {
  .child-card {
    padding: 16px;
  }

  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
