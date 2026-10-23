<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  home: { type: Object, required: true },
  progress: { type: Object, default: null },
  avatarSrc: { type: String, required: true },
  busy: { type: Boolean, default: false },
})

const emit = defineEmits(['open-area', 'request-exit'])

const view = ref('home')

const levelTitle = computed(() => props.home.level?.title || props.home.child?.levelTitle || 'Getting started')
const levelDescription = computed(() => props.home.level?.description || 'Build your Bangla skills one small step at a time.')
const overallPercent = computed(() => props.progress?.overallPercent ?? props.home.summary?.overallProgress ?? 0)
const completedLessons = computed(() => props.progress?.completedLessons ?? props.home.summary?.completedLessons ?? 0)
const totalLessons = computed(() => props.progress?.totalLessons ?? props.home.summary?.lessonCount ?? 0)
const progressLessons = computed(() => props.progress?.lessons ?? [])

const lessonById = computed(() => {
  const map = new Map()
  for (const lesson of props.home.lessons || []) map.set(lesson.lessonID, lesson)
  return map
})

const latestProgress = computed(() => {
  const viewed = progressLessons.value
    .filter(item => item.lastViewedAt)
    .slice()
    .sort((a, b) => new Date(b.lastViewedAt) - new Date(a.lastViewedAt))
  return viewed[0] || null
})

const latestLesson = computed(() => latestProgress.value ? lessonById.value.get(latestProgress.value.lessonID) : null)

function inferArea(lesson) {
  if (!lesson) return 'vowels'
  const text = `${lesson.strand || ''} ${lesson.title || ''}`.toLowerCase()
  if (text.includes('culture') || text.includes('history')) return 'culture'
  if (text.includes('consonant')) return 'consonants'
  if (text.includes('word') || text.includes('spell') || text.includes('syllable')) return 'spelling'
  return 'vowels'
}

function continueLearning() {
  const area = inferArea(latestLesson.value)
  if (area === 'culture') {
    view.value = 'culture'
    return
  }
  emit('open-area', area)
}

const cultureLessons = computed(() => (props.home.lessons || []).filter((lesson) => {
  const text = `${lesson.strand || ''} ${lesson.title || ''}`.toLowerCase()
  return text.includes('culture') || text.includes('history')
}))

const lettersLessons = computed(() => (props.home.lessons || []).filter((lesson) => !cultureLessons.value.some(item => item.lessonID === lesson.lessonID)))

const badges = computed(() => [
  { title: 'First Step', detail: 'Started learning', unlocked: overallPercent.value > 0, icon: '🌱' },
  { title: 'Lesson Finisher', detail: 'Completed a lesson', unlocked: completedLessons.value > 0, icon: '⭐' },
  { title: 'Halfway Hero', detail: 'Reached 50%', unlocked: overallPercent.value >= 50, icon: '🚀' },
  { title: 'Level Finisher', detail: 'Completed all lessons', unlocked: totalLessons.value > 0 && completedLessons.value === totalLessons.value, icon: '🏆' },
])

const levelComplete = computed(() => totalLessons.value > 0 && completedLessons.value === totalLessons.value && overallPercent.value === 100)

function formatTime(value) {
  if (!value) return 'Not started'
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
  } catch {
    return 'Recently viewed'
  }
}
</script>

<template>
  <div class="learning-dashboard">
    <template v-if="view === 'home'">
      <section class="hero-card">
        <div class="hero-copy">
          <span class="eyebrow">Welcome back</span>
          <h1>{{ home.child.nickname }}’s learning journey</h1>
          <p>{{ levelDescription }}</p>
          <div class="hero-actions">
            <button class="primary-action" type="button" :disabled="busy" @click="continueLearning">
              {{ latestLesson ? 'Continue learning' : 'Start learning' }}
              <span aria-hidden="true">→</span>
            </button>
            <button class="secondary-action" type="button" @click="view = 'progress'">View progress</button>
          </div>
        </div>

        <div class="learner-card">
          <img :src="avatarSrc" alt="" class="learner-avatar">
          <div>
            <span class="learner-name">{{ home.child.nickname }}</span>
            <span class="level-label">Current level</span>
            <strong>{{ levelTitle }}</strong>
          </div>
          <div class="progress-row">
            <span>{{ overallPercent }}%</span>
            <span>{{ completedLessons }}/{{ totalLessons }} lessons</span>
          </div>
          <div class="progress-track" :aria-label="`Overall progress ${overallPercent}%`">
            <span :style="{ width: `${overallPercent}%` }"></span>
          </div>
        </div>
      </section>

      <section v-if="latestLesson" class="continue-card">
        <div>
          <span class="eyebrow">Pick up where you left off</span>
          <h2>{{ latestLesson.title }}</h2>
          <p>{{ latestLesson.summary || 'Continue from your most recently viewed lesson.' }}</p>
        </div>
        <div class="continue-meta">
          <strong>{{ latestProgress.percentComplete }}%</strong>
          <span>Last viewed {{ formatTime(latestProgress.lastViewedAt) }}</span>
        </div>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Choose a path</span>
            <h2>What do you want to explore?</h2>
          </div>
        </div>

        <div class="path-grid">
          <button class="path-card letters-card" type="button" @click="view = 'letters'">
            <span class="path-symbol" lang="bn">অ আ</span>
            <span class="path-copy">
              <small>Letters & syllables</small>
              <strong>Sounds, letters and words</strong>
              <span>Practice vowels, consonants and word building.</span>
            </span>
            <span class="path-arrow" aria-hidden="true">→</span>
          </button>

          <button class="path-card culture-card" type="button" @click="view = 'culture'">
            <span class="path-symbol" aria-hidden="true">✦</span>
            <span class="path-copy">
              <small>Culture & history</small>
              <strong>Stories behind the language</strong>
              <span>Explore Bangla culture, people and traditions.</span>
            </span>
            <span class="path-arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </section>

      <section class="quick-stats">
        <article>
          <span>Completed</span>
          <strong>{{ completedLessons }}</strong>
          <small>lessons</small>
        </article>
        <article>
          <span>Current level</span>
          <strong>{{ levelTitle }}</strong>
          <small>{{ overallPercent }}% complete</small>
        </article>
        <article>
          <span>Next step</span>
          <strong>{{ latestLesson?.title || 'Start your first lesson' }}</strong>
          <small>{{ latestLesson ? 'Continue learning' : 'Choose a learning path' }}</small>
        </article>
      </section>

      <button class="exit-child-button" type="button" :disabled="busy" @click="emit('request-exit')">
        Exit child mode with parent PIN
      </button>
    </template>

    <template v-else-if="view === 'letters'">
      <button class="back-link" type="button" @click="view = 'home'">← Learning home</button>
      <section class="subpage-header">
        <span class="eyebrow">Letters & syllables</span>
        <h1>Build the sounds of Bangla</h1>
        <p>Choose an activity below. Your progress is saved to the current child profile when a matching published lesson exists.</p>
      </section>
      <div class="activity-grid">
        <button class="activity-card" type="button" @click="emit('open-area', 'vowels')">
          <span lang="bn">অ আ</span><strong>Vowels</strong><small>Learn vowel shapes and sounds.</small>
        </button>
        <button class="activity-card" type="button" @click="emit('open-area', 'consonants')">
          <span lang="bn">ক খ</span><strong>Consonants</strong><small>Practice consonants and vowel signs.</small>
        </button>
        <button class="activity-card" type="button" @click="emit('open-area', 'spelling')">
          <span lang="bn">শব্দ</span><strong>Words & syllables</strong><small>Blend letters into everyday words.</small>
        </button>
      </div>
      <p v-if="lettersLessons.length" class="data-note">{{ lettersLessons.length }} published lesson{{ lettersLessons.length === 1 ? '' : 's' }} are currently available in this level.</p>
    </template>

    <template v-else-if="view === 'culture'">
      <button class="back-link" type="button" @click="view = 'home'">← Learning home</button>
      <section class="subpage-header">
        <span class="eyebrow">Culture & history</span>
        <h1>Discover the world around Bangla</h1>
        <p>This section uses the published culture/history lessons assigned to the child’s current level.</p>
      </section>
      <div v-if="cultureLessons.length" class="lesson-list">
        <article v-for="lesson in cultureLessons" :key="lesson.lessonID" class="lesson-row">
          <div>
            <small>Lesson {{ lesson.lessonID }}</small>
            <h3>{{ lesson.title }}</h3>
            <p>{{ lesson.summary || 'Culture and history lesson.' }}</p>
          </div>
          <span>{{ lesson.estimatedMinutes || 0 }} min</span>
        </article>
      </div>
      <div v-else class="empty-state">
        <span aria-hidden="true">📚</span>
        <h2>No culture lessons published yet</h2>
        <p>The entry point is ready. Lessons will appear here automatically when the content team publishes them.</p>
      </div>
    </template>

    <template v-else-if="view === 'progress'">
      <button class="back-link" type="button" @click="view = 'home'">← Learning home</button>
      <section class="subpage-header progress-header">
        <div>
          <span class="eyebrow">Progress</span>
          <h1>{{ home.child.nickname }}’s progress</h1>
          <p>Current level: <strong>{{ levelTitle }}</strong></p>
        </div>
        <div class="progress-ring" :style="{ '--progress-angle': `${overallPercent * 3.6}deg` }">
          <span>{{ overallPercent }}%</span>
        </div>
      </section>

      <section class="progress-summary-grid">
        <article><span>Completed lessons</span><strong>{{ completedLessons }}</strong><small>of {{ totalLessons }}</small></article>
        <article><span>Current level</span><strong>{{ levelTitle }}</strong><small>Keep building momentum</small></article>
        <article><span>Quiz scores</span><strong>—</strong><small>Waiting for Quiz Results API</small></article>
      </section>

      <section class="section-block">
        <div class="section-heading"><div><span class="eyebrow">Lessons</span><h2>Current level</h2></div></div>
        <div v-if="home.lessons?.length" class="lesson-list">
          <article v-for="lesson in home.lessons" :key="lesson.lessonID" class="lesson-row">
            <div>
              <small>{{ lesson.strand || 'Learning' }}</small>
              <h3>{{ lesson.title }}</h3>
              <p>{{ lesson.completed ? 'Completed' : `${lesson.percentComplete || 0}% complete` }}</p>
            </div>
            <span class="lesson-status" :class="{ complete: lesson.completed }">{{ lesson.completed ? '✓' : `${lesson.percentComplete || 0}%` }}</span>
          </article>
        </div>
        <div v-else class="empty-state compact"><p>No published lessons are assigned to this level yet.</p></div>
      </section>

      <section class="section-block">
        <div class="section-heading"><div><span class="eyebrow">Achievements</span><h2>Badges</h2></div></div>
        <div class="badge-grid">
          <article v-for="badge in badges" :key="badge.title" class="badge-card" :class="{ locked: !badge.unlocked }">
            <span aria-hidden="true">{{ badge.icon }}</span>
            <strong>{{ badge.title }}</strong>
            <small>{{ badge.unlocked ? badge.detail : 'Keep learning to unlock' }}</small>
          </article>
        </div>
        <p class="prototype-note">Badge thresholds are a front-end prototype until the team defines final achievement rules.</p>
      </section>

      <section class="level-up-card" :class="{ ready: levelComplete }">
        <div>
          <span class="eyebrow">Level Up feedback</span>
          <h2>{{ levelComplete ? 'All published lessons completed!' : 'Keep going' }}</h2>
          <p v-if="levelComplete">This feedback screen is ready, but the actual level-up decision remains connected to PB21 after the team agrees the quiz/completion rule.</p>
          <p v-else>Complete the current level’s published lessons to reach the completion feedback stage.</p>
        </div>
        <button v-if="levelComplete" class="secondary-action" type="button" @click="view = 'level-up'">View feedback</button>
      </section>
    </template>

    <template v-else-if="view === 'level-up'">
      <button class="back-link" type="button" @click="view = 'progress'">← Progress</button>
      <section class="celebration-card">
        <div class="celebration-mark" aria-hidden="true">★</div>
        <span class="eyebrow">Level Up feedback preview</span>
        <h1>Amazing work, {{ home.child.nickname }}!</h1>
        <p>You completed every published lesson in <strong>{{ levelTitle }}</strong>.</p>
        <div class="celebration-progress"><span>100%</span><strong>Level lessons complete</strong></div>
        <p class="prototype-note">The backend level-up action is intentionally not triggered here. PB21 will define the final upgrade rule with the team.</p>
        <button class="primary-action" type="button" @click="view = 'home'">Back to learning home</button>
      </section>
    </template>
  </div>
</template>

<style scoped>
.learning-dashboard{width:min(1180px,100%);margin:0 auto;padding:42px 32px 64px;color:#214437}.hero-card{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(280px,.8fr);gap:34px;background:linear-gradient(135deg,#eef7e8 0%,#fff9df 100%);border:1px solid #dce8d5;border-radius:30px;padding:44px;box-shadow:0 22px 60px rgba(42,78,55,.08)}.hero-copy h1,.subpage-header h1,.celebration-card h1{margin:8px 0 14px;font-size:clamp(36px,5vw,62px);line-height:1.02;letter-spacing:-2px}.hero-copy p,.subpage-header p{max-width:680px;margin:0;color:#5f7167;font-size:18px}.eyebrow{display:block;color:#6f8d58;font-size:13px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.hero-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.primary-action,.secondary-action,.back-link,.exit-child-button{border-radius:14px;min-height:48px;padding:12px 18px;font-weight:800}.primary-action{border:0;background:#284f3c;color:#fff}.secondary-action{border:1px solid #bfcfba;background:#fff;color:#284f3c}.learner-card{background:#fff;border:1px solid #dfe8db;border-radius:24px;padding:24px;align-self:stretch}.learner-avatar{width:72px;height:72px;border-radius:22px;object-fit:cover;background:#eef3e8;margin-bottom:16px}.learner-card>div:nth-of-type(1){display:grid}.learner-name{font-size:20px;font-weight:800}.level-label{margin-top:12px;font-size:12px;color:#7b8d83;text-transform:uppercase;letter-spacing:.08em}.learner-card strong{font-size:22px}.progress-row{display:flex;justify-content:space-between;gap:12px;margin-top:24px;font-size:13px;color:#65766d}.progress-track{height:11px;border-radius:999px;background:#e7eee3;overflow:hidden;margin-top:8px}.progress-track span{display:block;height:100%;border-radius:inherit;background:#6f9661;transition:width .35s ease}.continue-card,.level-up-card{display:flex;justify-content:space-between;gap:26px;align-items:center;margin-top:22px;padding:24px 28px;border:1px solid #dce5d7;border-radius:20px;background:#fff}.continue-card h2,.level-up-card h2{margin:4px 0 5px}.continue-card p,.level-up-card p{margin:0;color:#687970}.continue-meta{text-align:right;display:grid;gap:3px}.continue-meta strong{font-size:28px;color:#315a46}.continue-meta span{font-size:13px;color:#7d8b83}.section-block{margin-top:38px}.section-heading{display:flex;justify-content:space-between;align-items:end;margin-bottom:16px}.section-heading h2{margin:5px 0 0;font-size:28px}.path-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.path-card{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:18px;text-align:left;border:1px solid transparent;border-radius:24px;padding:28px;min-height:180px;color:#24473b}.letters-card{background:#edf7e8;border-color:#d6e8d0}.culture-card{background:#fff3dd;border-color:#f0dfc1}.path-symbol{display:grid;place-items:center;width:74px;height:74px;border-radius:22px;background:#fff;font-size:30px;font-weight:800;box-shadow:0 10px 26px rgba(41,72,50,.08)}.path-copy{display:grid;gap:5px}.path-copy small{font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#75836d}.path-copy strong{font-size:22px}.path-copy span{color:#67776f}.path-arrow{font-size:28px}.quick-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:18px}.quick-stats article,.progress-summary-grid article{display:grid;gap:4px;background:#fff;border:1px solid #e1e7dd;border-radius:18px;padding:20px}.quick-stats span,.progress-summary-grid span{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#7d8d84;font-weight:800}.quick-stats strong,.progress-summary-grid strong{font-size:22px}.quick-stats small,.progress-summary-grid small{color:#7b8981}.exit-child-button{display:block;margin:28px 0 0 auto;background:transparent;border:1px solid #d7c8be;color:#815943}.back-link{border:0;background:transparent;padding-left:0;color:#4c6e5c}.subpage-header{padding:18px 0 8px}.activity-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:22px}.activity-card{display:grid;gap:8px;text-align:left;padding:26px;border:1px solid #dfe8db;background:#fff;border-radius:22px;color:#28493b}.activity-card>span:first-child{font-size:34px;font-weight:800}.activity-card strong{font-size:20px}.activity-card small,.data-note{color:#718077}.data-note{margin-top:16px}.lesson-list{display:grid;gap:12px;margin-top:18px}.lesson-row{display:flex;justify-content:space-between;align-items:center;gap:20px;border:1px solid #e0e7dc;border-radius:17px;background:#fff;padding:18px 20px}.lesson-row small{font-size:12px;color:#809087;text-transform:uppercase;letter-spacing:.06em}.lesson-row h3{margin:3px 0 4px}.lesson-row p{margin:0;color:#6e7c74}.lesson-status{display:grid;place-items:center;min-width:48px;height:48px;border-radius:14px;background:#f1f3ef;color:#6a796f;font-weight:800}.lesson-status.complete{background:#e5f1df;color:#42603a}.empty-state{text-align:center;padding:48px 24px;border:1px dashed #d9e1d5;border-radius:22px;background:#fafbf8;margin-top:22px}.empty-state>span{font-size:42px}.empty-state.compact{padding:20px}.progress-header{display:flex;justify-content:space-between;align-items:center}.progress-ring{--progress-angle:0deg;width:112px;height:112px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(#6f9661 var(--progress-angle),#e5ebe1 0);position:relative}.progress-ring::after{content:'';position:absolute;inset:10px;border-radius:50%;background:#fff}.progress-ring span{position:relative;z-index:1;font-size:23px;font-weight:800}.progress-summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:24px}.badge-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.badge-card{display:grid;gap:6px;text-align:center;padding:20px 12px;border:1px solid #dfe7db;border-radius:18px;background:#fff}.badge-card>span{font-size:30px}.badge-card small{color:#75847b}.badge-card.locked{opacity:.45;filter:grayscale(1)}.prototype-note{font-size:13px;color:#7b8981;margin:12px 0 0}.level-up-card{background:#f8f8f4}.level-up-card.ready{background:linear-gradient(135deg,#eef7e8,#fff5d8);border-color:#d4e4c9}.celebration-card{text-align:center;max-width:760px;margin:34px auto;padding:54px 42px;border:1px solid #d9e7d0;border-radius:30px;background:linear-gradient(145deg,#eef7e8,#fff7dc);box-shadow:0 24px 70px rgba(40,79,60,.1)}.celebration-mark{width:86px;height:86px;border-radius:28px;background:#fff4b8;display:grid;place-items:center;margin:0 auto 18px;font-size:40px;color:#b98517}.celebration-progress{display:flex;justify-content:center;gap:14px;align-items:center;margin:24px 0;padding:16px;border-radius:16px;background:#fff}.celebration-progress span{font-size:28px;font-weight:800;color:#507b43}.celebration-card .primary-action{margin-top:24px}.prototype-note{line-height:1.55}
@media(max-width:850px){.learning-dashboard{padding:28px 18px 48px}.hero-card{grid-template-columns:1fr;padding:28px}.path-grid,.progress-summary-grid{grid-template-columns:1fr}.activity-grid{grid-template-columns:1fr}.badge-grid{grid-template-columns:repeat(2,1fr)}.quick-stats{grid-template-columns:1fr}.progress-header{align-items:flex-start}.continue-card,.level-up-card{align-items:flex-start;flex-direction:column}.continue-meta{text-align:left}}
@media(max-width:520px){.hero-copy h1,.subpage-header h1,.celebration-card h1{font-size:36px}.path-card{grid-template-columns:auto 1fr;padding:20px}.path-arrow{display:none}.badge-grid{grid-template-columns:1fr}.progress-ring{width:92px;height:92px}.celebration-card{padding:36px 22px}}
</style>
