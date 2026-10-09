<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { accountApi } from '../services/accountApi'
import bunnyAvatar from '../assets/avatars/bunny.png'
import flowerAvatar from '../assets/avatars/flower.png'
import koalaAvatar from '../assets/avatars/koala.png'
import sproutAvatar from '../assets/avatars/sprout.png'

const page = ref('login'), flow = ref('login'), error = ref(''), notice = ref('')
const email = ref(''), password = ref(''), confirm = ref(''), code = ref('')
const fieldErrors = ref({})
const busy = ref(false), booting = ref(true), challenge = ref(null), signedIn = ref(null)
const children = ref([]), childrenLoading = ref(false)
const studentHome = ref(null)
const developmentCodes = ref(false), now = ref(Date.now()), heading = ref(null)
const childNickname = ref(''), childAgeBand = ref('junior'), selectedAvatar = ref('sprout')
const editingChildId = ref(null)
const deleteConfirmId = ref(null)
const deleteChallenge = ref(null), deleteCode = ref('')
const pinEditorOpen = ref(false), parentPin = ref(''), confirmParentPin = ref('')
const parentAccessPin = ref('')
const customAvatarUrl = ref(''), customAvatarName = ref('')
const customAvatarFile = ref(null), existingCustomAvatar = ref('')
const avatarSources = { sprout: sproutAvatar, bunny: bunnyAvatar, koala: koalaAvatar, flower: flowerAvatar }
const avatarChoices = [
  { id: 'sprout', label: 'Sprout', src: sproutAvatar },
  { id: 'bunny', label: 'Bunny', src: bunnyAvatar },
  { id: 'koala', label: 'Koala', src: koalaAvatar },
  { id: 'flower', label: 'Flower', src: flowerAvatar },
]
const titles = { login: 'Welcome back.', register: 'Start something wonderful.', forgot: 'Reset your password.', verify: 'Check your inbox.', reset: 'Set a new password.' }
const subtitles = { login: 'A little learning. A world of possibility.', register: 'Create your account and begin your journey.', forgot: 'Enter your email and we will send you a verification code.', verify: 'Enter the six-digit code to continue.', reset: 'Choose a secure password for your account.' }
const isChildCreate = computed(() => !!signedIn.value && page.value === 'child-create')
const isChildEdit = computed(() => isChildCreate.value && editingChildId.value !== null)
const isStudentHome = computed(() => !!signedIn.value && page.value === 'student-home')
const isParentPinSet = computed(() => !!signedIn.value && page.value === 'parent-pin-set')
const isParentPinVerify = computed(() => !!signedIn.value && page.value === 'parent-pin')
const isParentPlaceholder = computed(() => !!signedIn.value && page.value === 'parent-dashboard')
const currentTitle = computed(() => {
  if (!signedIn.value) return titles[page.value]
  if (isStudentHome.value) return `${studentHome.value?.child?.nickname || 'Student'}’s learning`
  if (isChildCreate.value) return isChildEdit.value ? 'Edit child profile' : 'Add child profile'
  if (isParentPinSet.value) return 'Set parent PIN'
  if (isParentPinVerify.value) return 'Enter parent area'
  if (isParentPlaceholder.value) return 'Parent area'
  return 'Child profiles'
})
const currentSubtitle = computed(() => {
  if (!signedIn.value) return subtitles[page.value]
  if (isStudentHome.value) return studentHome.value?.level?.description || 'Choose a lesson and keep learning.'
  if (isChildCreate.value) return isChildEdit.value ? 'Update their profile details.' : 'Create a space that feels like their own.'
  if (isParentPinSet.value) return 'A small PIN keeps parent-only areas safe.'
  if (isParentPinVerify.value) return 'Enter your 4-digit PIN to continue.'
  if (isParentPlaceholder.value) return 'Parent access has been verified.'
  return 'Create a profile for each child who uses this account.'
})
const cooldown = computed(() => Math.max(0, Math.ceil(((challenge.value?.resend_at || 0) * 1000 - now.value) / 1000)))
const deleteCooldown = computed(() => Math.max(0, Math.ceil(((deleteChallenge.value?.resend_at || 0) * 1000 - now.value) / 1000)))
const timer = setInterval(() => now.value = Date.now(), 1000)
onUnmounted(() => {
  clearInterval(timer)
  if (customAvatarUrl.value.startsWith('blob:')) URL.revokeObjectURL(customAvatarUrl.value)
})

function isCustomAvatar(avatar) {
  return typeof avatar === 'string' && avatar.startsWith('custom:')
}
function avatarSource(avatar) {
  if (isCustomAvatar(avatar)) return `/api/children/avatars/${avatar.slice('custom:'.length)}`
  return avatarSources[avatar] || sproutAvatar
}

function go(next) {
  page.value = next; error.value = ''; notice.value = ''; fieldErrors.value = {}; password.value = ''; confirm.value = ''
  if (next === 'login') { challenge.value = null; code.value = '' }
  nextTick(() => heading.value?.focus())
}
function clearFieldError(field) {
  if (!fieldErrors.value[field]) return
  fieldErrors.value = { ...fieldErrors.value, [field]: '' }
}
function resetChildForm() {
  editingChildId.value = null
  childNickname.value = ''
  childAgeBand.value = 'junior'
  selectedAvatar.value = 'sprout'
  customAvatarName.value = ''
  customAvatarFile.value = null
  existingCustomAvatar.value = ''
  if (customAvatarUrl.value.startsWith('blob:')) URL.revokeObjectURL(customAvatarUrl.value)
  customAvatarUrl.value = ''
}
function openChildCreate() {
  deleteConfirmId.value = null
  deleteChallenge.value = null
  deleteCode.value = ''
  resetChildForm()
  go('child-create')
}
function openChildEdit(child) {
  deleteConfirmId.value = null
  deleteChallenge.value = null
  deleteCode.value = ''
  resetChildForm()
  editingChildId.value = child.childID
  childNickname.value = child.nickname
  childAgeBand.value = child.ageBand
  if (isCustomAvatar(child.avatar)) {
    selectedAvatar.value = 'custom'
    existingCustomAvatar.value = child.avatar
    customAvatarUrl.value = avatarSource(child.avatar)
    customAvatarName.value = 'Current custom avatar'
  } else {
    selectedAvatar.value = child.avatar
  }
  go('child-create')
}
function cancelChildCreate() {
  resetChildForm()
  go('login')
}
function openStudentHome(child) {
  cancelDeleteConfirm()
  run(async () => {
    studentHome.value = await accountApi(`/children/${child.childID}/home`)
    go('student-home')
  })
}
function closeStudentHome() {
  studentHome.value = null
  go('login')
}
function openDeleteConfirm(childId) {
  deleteConfirmId.value = childId
  deleteChallenge.value = null
  deleteCode.value = ''
  clearFieldError('deleteCode')
}
function cancelDeleteConfirm() {
  deleteConfirmId.value = null
  deleteChallenge.value = null
  deleteCode.value = ''
  clearFieldError('deleteCode')
}
function requestDeleteCode(child) {
  run(async () => {
    deleteChallenge.value = await accountApi(`/children/${child.childID}/delete-code`, { method: 'POST', body: {} })
    deleteCode.value = ''
    now.value = Date.now()
  }, { field: 'deleteCode' })
}
function resendDeleteCode() {
  if (!deleteChallenge.value || deleteCooldown.value) return
  run(async () => {
    deleteChallenge.value = await accountApi('/auth/resend-code', {
      method: 'POST',
      body: { challenge_id: deleteChallenge.value.challenge_id },
    })
    deleteCode.value = ''
    now.value = Date.now()
  }, { field: 'deleteCode' })
}
function confirmDeleteChild(child) {
  if (!/^\d{6}$/.test(deleteCode.value)) {
    fieldErrors.value = { ...fieldErrors.value, deleteCode: 'Enter the 6-digit verification code.' }
    return
  }
  run(async () => {
    await accountApi(`/children/${child.childID}`, {
      method: 'DELETE',
      body: { challenge_id: deleteChallenge.value.challenge_id, code: deleteCode.value },
    })
    cancelDeleteConfirm()
    await loadChildren()
    notice.value = `${child.nickname}'s profile was deleted.`
  }, { field: 'deleteCode' })
}
function openPinEditor() {
  pinEditorOpen.value = true
  parentPin.value = ''
  confirmParentPin.value = ''
  fieldErrors.value = {}
  error.value = ''
  notice.value = ''
  go('parent-pin-set')
}
function cancelPinEditor() {
  pinEditorOpen.value = false
  parentPin.value = ''
  confirmParentPin.value = ''
  clearFieldError('pin')
  clearFieldError('pinConfirm')
  if (signedIn.value && page.value === 'parent-pin-set') go('login')
}
function submitParentPin() {
  const next = {}
  if (!/^\d{4}$/.test(parentPin.value)) next.pin = 'Enter a 4-digit PIN.'
  if (!confirmParentPin.value) next.pinConfirm = 'Enter the PIN again.'
  else if (parentPin.value !== confirmParentPin.value) next.pinConfirm = 'The PINs do not match.'
  fieldErrors.value = next
  if (Object.keys(next).length) return
  run(async () => {
    await accountApi('/auth/pin', { method: 'PUT', body: { pin: parentPin.value } })
    signedIn.value = { ...signedIn.value, hasPin: true }
    cancelPinEditor()
    notice.value = 'Your parent PIN has been set.'
  }, { field: 'pin' })
}
function openParentArea() {
  parentAccessPin.value = ''
  pinEditorOpen.value = false
  go('parent-pin')
}
function closeParentArea() {
  parentAccessPin.value = ''
  go('login')
}
function verifyParentAccess() {
  if (!/^\d{4}$/.test(parentAccessPin.value)) {
    fieldErrors.value = { ...fieldErrors.value, parentAccessPin: 'Enter your 4-digit PIN.' }
    return
  }
  run(async () => {
    await accountApi('/auth/pin/verify', { method: 'POST', body: { pin: parentAccessPin.value } })
    parentAccessPin.value = ''
    go('parent-dashboard')
    notice.value = 'Parent access verified.'
  }, { field: 'parentAccessPin' })
}
function selectAvatar(id) {
  selectedAvatar.value = id
  clearFieldError('avatar')
}
function uploadAvatar(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    fieldErrors.value = { ...fieldErrors.value, avatar: 'Choose a PNG, JPG, or WebP image.' }
    event.target.value = ''
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    fieldErrors.value = { ...fieldErrors.value, avatar: 'Choose an image smaller than 2 MB.' }
    event.target.value = ''
    return
  }
  if (customAvatarUrl.value.startsWith('blob:')) URL.revokeObjectURL(customAvatarUrl.value)
  customAvatarUrl.value = URL.createObjectURL(file)
  customAvatarName.value = file.name
  customAvatarFile.value = file
  selectedAvatar.value = 'custom'
  clearFieldError('avatar')
}
function submitChildProfile() {
  const next = {}
  const nickname = childNickname.value.trim()
  if (!nickname) next.nickname = "Enter the child's nickname."
  else if (nickname.length > 60) next.nickname = 'Nickname must be no more than 60 characters.'
  if (!['junior', 'senior'].includes(childAgeBand.value)) next.ageBand = 'Choose an age group.'
  if (selectedAvatar.value === 'custom' && !customAvatarFile.value && !existingCustomAvatar.value) {
    next.avatar = 'Choose an image to use as the custom avatar.'
  }
  fieldErrors.value = next
  if (Object.keys(next).length) return
  run(async () => {
    const childId = editingChildId.value
    let avatar = selectedAvatar.value
    if (avatar === 'custom') {
      if (customAvatarFile.value) {
        const uploaded = await accountApi('/children/avatar', {
          method: 'POST',
          body: customAvatarFile.value,
        })
        avatar = uploaded.avatar
      } else {
        avatar = existingCustomAvatar.value
      }
    }
    await accountApi(childId === null ? '/children' : `/children/${childId}`, {
      method: childId === null ? 'POST' : 'PUT',
      body: { nickname, ageBand: childAgeBand.value, avatar },
    })
    await loadChildren()
    resetChildForm()
    go('login')
    notice.value = childId === null ? 'Child profile created successfully.' : 'Child profile updated successfully.'
  })
}
async function loadChildren() {
  childrenLoading.value = true
  try {
    children.value = await accountApi('/children')
  } finally {
    childrenLoading.value = false
  }
}
function errorField(exception) {
  if (!exception.status || exception.status >= 500) return null
  if (page.value === 'reset' && exception.fields?.includes('new_password')) return 'password'
  if (exception.fields?.length) return exception.fields[0]
  if (page.value === 'verify') return 'code'
  if (page.value === 'forgot') return 'email'
  if (page.value === 'register' && exception.status === 409) return 'email'
  if (page.value === 'child-create') return null
  return 'password'
}
function validateFields() {
  const next = {}
  if (['login', 'register', 'forgot'].includes(page.value)) {
    const normalizedEmail = email.value.trim()
    if (!normalizedEmail) next.email = 'Enter your email address.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) next.email = 'Enter a valid email address.'
  }
  if (['login', 'register', 'reset'].includes(page.value)) {
    if (!password.value) next.password = page.value === 'login' ? 'Please enter your password.' : page.value === 'reset' ? 'Enter your new password.' : 'Enter your password.'
    else if (['register', 'reset'].includes(page.value) && password.value.length < 8) next.password = 'Password must be at least 8 characters.'
    else if (['register', 'reset'].includes(page.value) && password.value.length > 128) next.password = 'Password must be no more than 128 characters.'
  }
  if (['register', 'reset'].includes(page.value)) {
    if (!confirm.value) next.confirm = page.value === 'reset' ? 'Enter your new password again.' : 'Enter your password again.'
    else if (password.value !== confirm.value) next.confirm = 'Your passwords do not match.'
  }
  if (page.value === 'verify' && !/^\d{6}$/.test(code.value)) {
    next.code = 'Enter the 6-digit verification code.'
  }
  fieldErrors.value = next
  return Object.keys(next).length === 0
}
async function run(action, { field } = {}) {
  if (busy.value) return
  busy.value = true; error.value = ''; notice.value = ''
  try { await action() }
  catch (e) {
    const target = field || errorField(e)
    if (target) fieldErrors.value = { ...fieldErrors.value, [target]: e.message }
    else error.value = e.message
  }
  finally { busy.value = false }
}
onMounted(async () => {
  try {
    const config = await accountApi('/auth/config')
    developmentCodes.value = config.development_codes
    try {
      signedIn.value = await accountApi('/auth/me')
      email.value = signedIn.value.email
      await loadChildren()
    } catch (e) { if (e.status !== 401) throw e }
  } catch (e) {
    if (![0, 404].includes(e.status)) error.value = e.message
  }
  finally { booting.value = false }
})
function submit() {
  if (!validateFields()) return
  run(async () => {
    if (page.value === 'verify') {
      const result = await accountApi('/auth/verify-code', { method: 'POST', body: { challenge_id: challenge.value.challenge_id, code: code.value } })
      if (flow.value === 'forgot' && result.password_reset) {
        go('reset')
        notice.value = 'Code verified. Set your new password.'
        return
      }
      signedIn.value = result.user; email.value = result.user.email
      await loadChildren()
      go('login')
      notice.value = flow.value === 'register' ? 'Account created successfully. You are signed in.' : 'You have logged in successfully.'
      return
    }
    if (page.value === 'reset') {
      await accountApi('/auth/reset-password', { method: 'POST', body: { challenge_id: challenge.value.challenge_id, new_password: password.value } })
      go('login')
      notice.value = 'Your password has been reset. Log in with your new password.'
      return
    }
    if (page.value === 'login') {
      const result = await accountApi('/auth/login', {
        method: 'POST',
        body: { email: email.value.trim(), password: password.value },
      })
      signedIn.value = result.user
      email.value = result.user.email
      password.value = ''
      await loadChildren()
      go('login')
      notice.value = 'You have logged in successfully.'
      return
    }
    flow.value = page.value
    const endpoint = page.value === 'forgot' ? 'forgot-password' : page.value
    const body = page.value === 'forgot' ? { email: email.value.trim() } : { email: email.value.trim(), password: password.value }
    challenge.value = await accountApi(`/auth/${endpoint}`, { method: 'POST', body })
    now.value = Date.now(); code.value = ''; go('verify')
  })
}
function resend() {
  if (cooldown.value) return
  run(async () => {
    challenge.value = await accountApi('/auth/resend-code', { method: 'POST', body: { challenge_id: challenge.value.challenge_id } })
    code.value = ''; now.value = Date.now(); notice.value = 'A new code is ready.'
  }, { field: 'code' })
}
function signOut() {
  run(async () => {
    await accountApi('/auth/logout', { method: 'POST', body: {} })
    cancelPinEditor()
    parentAccessPin.value = ''
    signedIn.value = null; children.value = []; studentHome.value = null; email.value = ''; password.value = ''; go('login')
  })
}
</script>

<template>
  <main class="account-page">
    <section class="account-content" :class="{ 'profiles-content': signedIn }" aria-labelledby="page-title" :aria-busy="busy || booting">
      <button v-if="isChildCreate && !booting" class="child-back-button" type="button" @click="cancelChildCreate">← Back to child profiles</button>
      <button v-else-if="isStudentHome && !booting" class="child-back-button" type="button" @click="closeStudentHome">← Back to child profiles</button>
      <button v-else-if="isParentPinSet && !booting" class="child-back-button" type="button" @click="cancelPinEditor">← Back to child profiles</button>
      <button v-else-if="(isParentPinVerify || isParentPlaceholder) && !booting" class="child-back-button" type="button" @click="closeParentArea">← Back to child profiles</button>
      <div v-else-if="signedIn && !booting" class="account-session">
        <strong>{{ signedIn.email }}</strong>
        <div class="account-session-actions">
          <template v-if="signedIn.hasPin">
            <span class="pin-status">PIN protected</span>
            <button class="text-button" type="button" :disabled="busy" @click="openParentArea">Parent area</button>
          </template>
          <button v-else class="text-button" type="button" :disabled="busy || pinEditorOpen" @click="openPinEditor">Set parent PIN</button>
          <button class="text-button" type="button" :disabled="busy" @click="signOut">Sign out</button>
        </div>
      </div>
      <h1 id="page-title" ref="heading" tabindex="-1">{{ currentTitle }}</h1>
      <p class="subtitle">{{ currentSubtitle }}</p>
      <p v-if="booting" class="notice" role="status">Connecting to your account…</p>
      <p v-if="notice" class="notice" role="status">{{ notice }}</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <template v-if="!booting">
        <div v-if="!signedIn && ['login', 'register'].includes(page)" class="tabs" aria-label="Account action"><button :disabled="busy" :class="{ active: page === 'login' }" :aria-pressed="page === 'login'" @click="go('login')">Log in</button><button :disabled="busy" :class="{ active: page === 'register' }" :aria-pressed="page === 'register'" @click="go('register')">Create account</button></div>
        <template v-if="signedIn">
          <form v-if="isParentPinSet" class="pin-editor" novalidate @submit.prevent="submitParentPin">
            <fieldset :disabled="busy">
              <div class="pin-editor-icon" aria-hidden="true">
                <svg viewBox="0 0 64 72"><path d="M20 31V21a12 12 0 0 1 24 0v10" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><rect x="12" y="29" width="40" height="34" rx="11" fill="currentColor" opacity=".18"/><path d="M32 42v9" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><path d="M31 13C22 8 20 2 21 0c8 0 13 4 10 13Zm3-1C35 5 41 1 47 3c0 6-6 11-13 9Z" fill="currentColor" opacity=".7"/></svg>
              </div>
              <p>Choose a PIN that children cannot easily guess.</p>
              <label for="parent-pin">4-digit PIN</label>
              <input id="parent-pin" v-model="parentPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.pin" :aria-describedby="fieldErrors.pin ? 'pin-error' : undefined" @input="clearFieldError('pin')">
              <p v-if="fieldErrors.pin" id="pin-error" class="field-error" role="alert">{{ fieldErrors.pin }}</p>
              <label for="parent-pin-confirm">Confirm PIN</label>
              <input id="parent-pin-confirm" v-model="confirmParentPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.pinConfirm" :aria-describedby="fieldErrors.pinConfirm ? 'pin-confirm-error' : undefined" @input="clearFieldError('pinConfirm')">
              <p v-if="fieldErrors.pinConfirm" id="pin-confirm-error" class="field-error" role="alert">{{ fieldErrors.pinConfirm }}</p>
              <div class="pin-editor-actions">
                <button class="secondary" type="button" @click="cancelPinEditor">Cancel</button>
                <button class="primary" type="submit">Set PIN</button>
              </div>
            </fieldset>
          </form>
          <form v-else-if="isParentPinVerify" class="parent-pin-gate" novalidate @submit.prevent="verifyParentAccess">
            <fieldset :disabled="busy">
              <label for="parent-access-pin">Parent PIN</label>
              <input id="parent-access-pin" v-model="parentAccessPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.parentAccessPin" :aria-describedby="fieldErrors.parentAccessPin ? 'parent-access-pin-error' : 'parent-access-pin-hint'" @input="clearFieldError('parentAccessPin')">
              <p v-if="fieldErrors.parentAccessPin" id="parent-access-pin-error" class="field-error" role="alert">{{ fieldErrors.parentAccessPin }}</p>
              <p id="parent-access-pin-hint" class="field-hint">Five incorrect attempts will temporarily lock parent access.</p>
              <button class="primary submit-button" type="submit">{{ busy ? 'Checking…' : 'Continue to parent area' }} <span v-if="!busy" aria-hidden="true">→</span></button>
            </fieldset>
          </form>
          <section v-else-if="isParentPlaceholder" class="parent-dashboard-placeholder">
            <div aria-hidden="true">✓</div>
            <h2>Parent access verified</h2>
            <p>The Parent Dashboard will be connected here by the team member responsible for that page.</p>
            <button class="secondary" type="button" @click="closeParentArea">Back to child profiles</button>
          </section>
          <section v-else-if="isStudentHome && studentHome" class="student-home" aria-label="Student homepage">
            <div class="student-hero">
              <img class="student-avatar" :class="{ custom: isCustomAvatar(studentHome.child.avatar) }" :src="avatarSource(studentHome.child.avatar)" alt="">
              <div>
                <span class="student-eyebrow">Welcome back</span>
                <h2>{{ studentHome.child.nickname }}</h2>
                <p>{{ studentHome.child.ageBand === 'senior' ? 'Senior learner' : 'Junior learner' }} · {{ studentHome.child.levelTitle || 'Learning path' }}</p>
              </div>
            </div>
            <div class="student-summary">
              <div>
                <strong>{{ studentHome.summary.overallProgress }}%</strong>
                <span>Overall progress</span>
              </div>
              <div>
                <strong>{{ studentHome.summary.completedLessons }}/{{ studentHome.summary.lessonCount }}</strong>
                <span>Lessons completed</span>
              </div>
            </div>
            <div class="progress-track" role="progressbar" aria-label="Overall learning progress" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="studentHome.summary.overallProgress">
              <span :style="{ width: `${studentHome.summary.overallProgress}%` }"></span>
            </div>
            <div class="learning-path-heading">
              <div>
                <span class="student-eyebrow">Current level</span>
                <h2>{{ studentHome.level?.title || 'Getting started' }}</h2>
              </div>
              <span>{{ studentHome.summary.lessonCount }} {{ studentHome.summary.lessonCount === 1 ? 'lesson' : 'lessons' }}</span>
            </div>
            <div v-if="studentHome.lessons.length" class="lesson-grid">
              <article v-for="lesson in studentHome.lessons" :key="lesson.lessonID" class="lesson-card">
                <div class="lesson-card-topline">
                  <span>{{ lesson.strand }}</span>
                  <span>{{ lesson.estimatedMinutes }} min</span>
                </div>
                <h3>{{ lesson.title }}</h3>
                <p>{{ lesson.summary || 'A new learning activity is ready.' }}</p>
                <div class="lesson-progress">
                  <span :style="{ width: `${lesson.percentComplete}%` }"></span>
                </div>
                <small>{{ lesson.completed ? 'Completed' : `${lesson.percentComplete}% complete` }}</small>
              </article>
            </div>
            <div v-else class="student-empty-lessons">
              <h2>New lessons are coming soon.</h2>
              <p>This profile is ready for learning content at the current level.</p>
            </div>
          </section>
          <form v-else-if="isChildCreate" class="child-profile-form" novalidate @submit.prevent="submitChildProfile">
            <fieldset>
              <label for="child-nickname">Child’s nickname</label>
              <input id="child-nickname" v-model="childNickname" type="text" autocomplete="off" maxlength="60" placeholder="Enter a nickname" required :aria-invalid="!!fieldErrors.nickname" :aria-describedby="fieldErrors.nickname ? 'nickname-error' : undefined" @input="clearFieldError('nickname')">
              <p v-if="fieldErrors.nickname" id="nickname-error" class="field-error" role="alert">{{ fieldErrors.nickname }}</p>

              <fieldset class="avatar-fieldset" :aria-describedby="fieldErrors.avatar ? 'avatar-error avatar-hint' : 'avatar-hint'">
                <legend>Choose an avatar</legend>
                <div class="profile-avatar-options" role="radiogroup" aria-label="Choose an avatar">
                  <button v-for="avatar in avatarChoices" :key="avatar.id" class="profile-avatar-choice" :class="{ selected: selectedAvatar === avatar.id }" type="button" role="radio" :aria-checked="selectedAvatar === avatar.id" :aria-label="avatar.label" @click="selectAvatar(avatar.id)">
                    <img :src="avatar.src" alt="">
                    <span v-if="selectedAvatar === avatar.id" class="avatar-check" aria-hidden="true">✓</span>
                  </button>
                  <label class="profile-avatar-choice upload-avatar-choice" :class="{ selected: selectedAvatar === 'custom' }" :title="customAvatarName || 'Upload your own'">
                    <input class="sr-only" type="file" accept="image/png,image/jpeg,image/webp" @change="uploadAvatar">
                    <img v-if="customAvatarUrl" :src="customAvatarUrl" alt="Custom avatar preview">
                    <svg v-else viewBox="0 0 64 64" aria-hidden="true"><path d="M17 20h8l3-5h9l3 5h7a6 6 0 0 1 6 6v20a6 6 0 0 1-6 6H17a6 6 0 0 1-6-6V26a6 6 0 0 1 6-6Z" fill="currentColor" opacity=".2"/><circle cx="32" cy="36" r="9" fill="none" stroke="currentColor" stroke-width="4"/><path d="M49 11v12m-6-6h12" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg>
                    <span class="upload-label">Upload your own</span>
                    <span v-if="selectedAvatar === 'custom'" class="avatar-check" aria-hidden="true">✓</span>
                  </label>
                </div>
                <p id="avatar-hint" class="field-hint">PNG, JPG, or WebP · up to 2 MB.</p>
                <p v-if="fieldErrors.avatar" id="avatar-error" class="field-error" role="alert">{{ fieldErrors.avatar }}</p>
              </fieldset>

              <label for="child-age-band">Age group</label>
              <select id="child-age-band" v-model="childAgeBand" required :aria-invalid="!!fieldErrors.ageBand" :aria-describedby="fieldErrors.ageBand ? 'age-band-error' : 'age-band-hint'" @change="clearFieldError('ageBand')">
                <option value="junior">Junior learner</option>
                <option value="senior">Senior learner</option>
              </select>
              <p id="age-band-hint" class="field-hint">The age group determines the child’s starting learning content.</p>
              <p v-if="fieldErrors.ageBand" id="age-band-error" class="field-error" role="alert">{{ fieldErrors.ageBand }}</p>

              <div class="child-form-actions">
                <button class="secondary" type="button" @click="cancelChildCreate">Cancel</button>
                <button class="primary" type="submit">{{ isChildEdit ? 'Save changes' : 'Create profile' }} <span aria-hidden="true">→</span></button>
              </div>
            </fieldset>
          </form>
          <div v-else-if="childrenLoading" class="notice" role="status">Loading child profiles…</div>
          <section v-else-if="children.length" aria-label="Your child profiles">
            <div class="family-meta">
              <span>Your child profiles</span>
              <span>{{ children.length }} of 5 profiles</span>
            </div>
            <div class="profile-grid">
              <article v-for="child in children" :key="child.childID" class="profile-card">
                <img class="profile-avatar-image" :class="{ custom: isCustomAvatar(child.avatar) }" :src="avatarSource(child.avatar)" alt="">
                <strong>{{ child.nickname }}</strong>
                <small>{{ child.ageBand === 'senior' ? 'Senior learner' : 'Junior learner' }}<template v-if="child.levelTitle"> · {{ child.levelTitle }}</template></small>
                <button class="profile-learn-button" type="button" :aria-label="`Open ${child.nickname}'s student homepage`" @click="openStudentHome(child)">Start learning <span aria-hidden="true">→</span></button>
                <div class="profile-card-actions">
                  <button class="profile-edit-button" type="button" :aria-label="`Edit ${child.nickname}'s profile`" @click="openChildEdit(child)">Edit</button>
                  <button class="profile-delete-button" type="button" :aria-label="`Delete ${child.nickname}'s profile`" @click="openDeleteConfirm(child.childID)">Delete</button>
                </div>
                <div v-if="deleteConfirmId === child.childID" class="profile-delete-confirm" role="alert">
                  <p>Delete {{ child.nickname }}’s profile? This cannot be undone.</p>
                  <template v-if="!deleteChallenge">
                    <p>A verification code will be sent to {{ signedIn.email }}.</p>
                    <div>
                      <button class="danger" type="button" :disabled="busy" @click="requestDeleteCode(child)">Send code</button>
                      <button class="secondary" type="button" :disabled="busy" @click="cancelDeleteConfirm">Cancel</button>
                    </div>
                  </template>
                  <template v-else>
                    <label :for="`delete-code-${child.childID}`">6-digit verification code</label>
                    <input :id="`delete-code-${child.childID}`" v-model="deleteCode" class="delete-code-input" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" :aria-invalid="!!fieldErrors.deleteCode" :aria-describedby="fieldErrors.deleteCode ? `delete-code-error-${child.childID}` : undefined" @input="clearFieldError('deleteCode')">
                    <p v-if="fieldErrors.deleteCode" :id="`delete-code-error-${child.childID}`" class="field-error" role="alert">{{ fieldErrors.deleteCode }}</p>
                    <p class="delete-code-hint">Valid for 10 minutes. Up to 5 attempts.</p>
                    <div class="delete-resend-row">
                      <button class="text-button" type="button" :disabled="deleteCooldown > 0 || busy" @click="resendDeleteCode">{{ deleteCooldown > 0 ? `Resend in ${deleteCooldown}s` : 'Resend code' }}</button>
                    </div>
                    <div>
                      <button class="danger" type="button" :disabled="busy" @click="confirmDeleteChild(child)">Verify & delete</button>
                      <button class="secondary" type="button" :disabled="busy" @click="cancelDeleteConfirm">Cancel</button>
                    </div>
                  </template>
                </div>
              </article>
              <button v-if="children.length < 5" class="add-profile" type="button" @click="openChildCreate">
                <span aria-hidden="true">＋</span>
                <strong>Add child profile</strong>
                <small>{{ 5 - children.length }} {{ 5 - children.length === 1 ? 'place' : 'places' }} remaining</small>
              </button>
            </div>
          </section>
          <div v-else class="child-empty-state">
            <svg class="child-empty-icon" viewBox="0 0 72 82" aria-hidden="true">
              <path d="M36 30V16" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
              <path d="M35 20C19 21 14 10 15 3C28 2 37 8 35 20ZM38 18C39 7 49 2 59 5C59 15 50 22 38 18Z" fill="currentColor" opacity=".78"/>
              <circle cx="36" cy="51" r="25" fill="currentColor" opacity=".16"/>
              <path d="M25 49c1-4 6-4 7 0m8 0c1-4 6-4 7 0M28 59c5 6 12 6 17 0" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
            </svg>
            <h2>No child profiles yet.</h2>
            <p>Add a child profile to get started.</p>
            <button class="primary add-child-button" type="button" @click="openChildCreate">Add child profile <span aria-hidden="true">→</span></button>
          </div>
        </template>
        <form v-else novalidate @submit.prevent="submit"><fieldset :disabled="busy">
          <template v-if="['login', 'register', 'forgot'].includes(page)"><label for="email">Email address</label><input id="email" v-model="email" type="email" autocomplete="email" placeholder="you@example.com" required maxlength="254" :aria-invalid="!!fieldErrors.email" :aria-describedby="fieldErrors.email ? 'email-error' : undefined" @input="clearFieldError('email')"><p v-if="fieldErrors.email" id="email-error" class="field-error" role="alert">{{ fieldErrors.email }}</p></template>
          <template v-if="['login', 'register', 'reset'].includes(page)"><label for="password">{{ page === 'reset' ? 'New password' : 'Password' }}</label><div class="password-field"><input id="password" v-model="password" type="password" :autocomplete="page === 'login' ? 'current-password' : 'new-password'" :placeholder="page === 'reset' ? 'Enter your new password' : 'Enter your password'" required minlength="8" maxlength="128" :aria-invalid="!!fieldErrors.password" :aria-describedby="fieldErrors.password ? 'password-error' : undefined" @input="clearFieldError('password')"></div><p v-if="fieldErrors.password" id="password-error" class="field-error" role="alert">{{ fieldErrors.password }}</p><button v-if="page === 'login'" class="text-button forgot" type="button" @click="go('forgot')">Forgot password?</button><p v-if="page !== 'login'" class="field-hint">Use 8–128 characters.</p></template>
          <template v-if="['register', 'reset'].includes(page)"><label for="confirm">{{ page === 'reset' ? 'Confirm new password' : 'Confirm password' }}</label><input id="confirm" v-model="confirm" type="password" autocomplete="new-password" :placeholder="page === 'reset' ? 'Enter your new password again' : 'Enter your password again'" required minlength="8" maxlength="128" :aria-invalid="!!fieldErrors.confirm" :aria-describedby="fieldErrors.confirm ? 'confirm-error' : undefined" @input="clearFieldError('confirm')"><p v-if="fieldErrors.confirm" id="confirm-error" class="field-error" role="alert">{{ fieldErrors.confirm }}</p></template>
          <template v-if="page === 'verify'"><div class="email-summary">Verification for <strong>{{ email }}</strong></div><label for="code">6-digit verification code</label><input id="code" v-model="code" class="code-input" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" required :aria-invalid="!!fieldErrors.code" :aria-describedby="fieldErrors.code ? 'code-error code-hint' : 'code-hint'" @input="clearFieldError('code')"><p v-if="fieldErrors.code" id="code-error" class="field-error" role="alert">{{ fieldErrors.code }}</p><p id="code-hint" class="field-hint">Valid for 10 minutes. Up to 5 attempts.</p><div v-if="challenge?.delivery === 'development'" class="development-code">Local development code: <strong>{{ challenge.development_code }}</strong><br>No email was sent.</div></template>
          <button class="primary submit-button" type="submit">{{ busy ? 'Please wait…' : ({ login: 'Continue', register: 'Create account', forgot: 'Send verification code', verify: 'Verify & continue', reset: 'Reset password' })[page] }} <span v-if="!busy" aria-hidden="true">→</span></button>
          <button v-if="page === 'forgot'" class="back-button" type="button" @click="go('login')">← Back to log in</button>
          <div v-if="page === 'verify'" class="resend-row"><span>Need another code?</span><button class="text-button" type="button" :disabled="cooldown > 0 || busy" @click="resend">{{ cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend code' }}</button></div><button v-if="page === 'verify'" class="back-button" type="button" @click="go('login')">← Back to log in</button>
        </fieldset></form>
      </template>
      <footer class="account-footer"><div class="sprout-divider" aria-hidden="true"><span></span><svg viewBox="0 0 32 32"><path d="M16 27V15" stroke="currentColor" stroke-width="2"/><path d="M15 21C4 22 2 13 3 7C12 6 17 12 15 21M17 18C17 8 24 5 29 6C30 15 24 21 17 18" fill="currentColor"/></svg><span></span></div><p>A parent account. A shared adventure.</p></footer>
      <p v-if="developmentCodes" class="development-note">Local development · Email verification uses an on-screen code.</p>
    </section>
  </main>
</template>

<style scoped>
input[aria-invalid='true'] {
  border-color: #b44435;
  box-shadow: 0 0 0 3px #b4443518;
}

.field-error {
  color: #b44435;
  font-size: 14px;
  font-weight: 700;
  margin: 7px 0 0;
}

.account-session {
  align-items: center;
  background: #edf3e5;
  border: 1px solid #c8d5ba;
  border-radius: 18px;
  color: #263c50;
  display: flex;
  justify-content: space-between;
  margin-bottom: 54px;
  padding: 22px 28px;
}

.account-session strong {
  overflow-wrap: anywhere;
}

.account-session-actions {
  align-items: center;
  display: flex;
}

.account-session .text-button {
  border-left: 1px solid #c8d5ba;
  margin-left: 24px;
  padding-left: 28px;
}

.pin-status {
  color: #55724d;
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
}

.pin-editor {
  background: #f5f8f0;
  border: 1px solid #c8d5ba;
  border-radius: 18px;
  margin-bottom: 30px;
  padding: 24px;
}

.pin-editor h2 {
  margin-bottom: 6px;
}

.pin-editor-icon {
  align-items: center;
  background: #e7f0df;
  border: 2px solid #c8d8bd;
  border-radius: 50%;
  color: #2c6248;
  display: flex;
  height: 92px;
  justify-content: center;
  margin: 0 auto 18px;
  width: 92px;
}

.pin-editor-icon svg {
  height: 58px;
  width: 52px;
}

.pin-editor > fieldset > p:not(.field-error) {
  color: #6c7f65;
  margin: 0 0 20px;
}

.pin-editor label {
  margin-top: 16px;
}

.pin-editor input {
  font-size: 24px;
  letter-spacing: 9px;
  text-align: center;
}

.pin-editor-actions {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr 1fr;
  margin-top: 24px;
}

.parent-pin-gate {
  background: #f5f8f0;
  border: 1px solid #c8d5ba;
  border-radius: 18px;
  padding: 28px;
}

.parent-pin-gate label {
  margin-top: 0;
}

.parent-pin-gate input {
  font-size: 26px;
  letter-spacing: 10px;
  text-align: center;
}

.parent-dashboard-placeholder {
  align-items: center;
  background: #edf3e5;
  border: 1px solid #c8d5ba;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  padding: 46px 28px;
  text-align: center;
}

.parent-dashboard-placeholder > div {
  align-items: center;
  background: #2c6248;
  border-radius: 50%;
  color: white;
  display: flex;
  font-size: 28px;
  height: 58px;
  justify-content: center;
  margin-bottom: 18px;
  width: 58px;
}

.parent-dashboard-placeholder p {
  color: #5e7165;
  margin: 0 0 24px;
  max-width: 440px;
}

.child-empty-state {
  align-items: center;
  background: #edf3e5;
  border: 1px solid #c8d5ba;
  border-radius: 24px;
  color: #174b39;
  display: flex;
  flex-direction: column;
  margin-top: 42px;
  padding: 48px 32px;
  text-align: center;
}

.child-empty-icon {
  height: 82px;
  margin-bottom: 18px;
  width: 72px;
}

.child-empty-state h2 {
  font-size: clamp(28px, 4vw, 38px);
  margin: 0 0 12px;
}

.child-empty-state p {
  color: #42566b;
  font-size: 20px;
  margin: 0 0 28px;
}

.add-child-button {
  max-width: 430px;
  width: 100%;
}

.child-back-button {
  background: none;
  border: 0;
  color: #2c6248;
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 26px;
  min-height: 44px;
  padding: 8px 0;
}

.child-profile-form {
  margin-top: 4px;
}

.avatar-fieldset {
  margin-top: 25px;
}

.avatar-fieldset legend {
  margin: 0 0 12px;
}

.profile-avatar-options {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.profile-avatar-choice {
  align-items: center;
  aspect-ratio: 1;
  background: #f3f6ed;
  border: 2px solid transparent;
  border-radius: 50%;
  color: #2c6248;
  display: flex;
  justify-content: center;
  margin: 0;
  min-width: 0;
  padding: 8px;
  position: relative;
}

button.profile-avatar-choice {
  width: 100%;
}

.profile-avatar-choice:hover,
.profile-avatar-choice.selected {
  border-color: #547963;
}

.profile-avatar-choice img {
  height: 100%;
  object-fit: contain;
  width: 100%;
}

.avatar-check {
  align-items: center;
  background: #2c6248;
  border: 2px solid #fcfcf8;
  border-radius: 50%;
  color: #fff;
  display: flex;
  font-size: 14px;
  font-weight: 800;
  height: 26px;
  justify-content: center;
  position: absolute;
  right: -3px;
  top: -3px;
  width: 26px;
}

.upload-avatar-choice {
  cursor: pointer;
  flex-direction: column;
  gap: 3px;
  overflow: hidden;
  text-align: center;
}

.upload-avatar-choice svg {
  height: 43%;
  width: 43%;
}

.upload-avatar-choice img {
  border-radius: 50%;
  inset: 0;
  object-fit: cover;
  position: absolute;
}

.upload-label {
  font-size: 11px;
  font-weight: 700;
  line-height: 1.05;
}

.child-form-actions {
  display: grid;
  gap: 14px;
  grid-template-columns: 1fr 1fr;
  margin-top: 30px;
}

.child-form-actions button {
  min-height: 56px;
}

.child-form-actions .primary {
  align-items: center;
  display: flex;
  gap: 18px;
  justify-content: center;
}

.profile-card {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 200px;
}

.profile-avatar-image {
  background: #f3f6ed;
  border: 2px solid #cbd8c7;
  border-radius: 50%;
  height: 104px;
  object-fit: contain;
  padding: 7px;
  width: 104px;
}

.profile-avatar-image.custom {
  object-fit: cover;
  padding: 0;
}

.profile-card strong {
  font-size: 18px;
  overflow-wrap: anywhere;
}

.profile-card small {
  color: #72816a;
  font-size: 14px;
}

.profile-learn-button {
  background: #2c513e;
  border: 1px solid #2c513e;
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  font-weight: 750;
  margin-top: 8px;
  min-height: 44px;
  padding: 10px 18px;
  width: 100%;
}

.profile-learn-button:hover:not(:disabled) {
  background: #203f30;
}

.student-home {
  display: grid;
  gap: 24px;
}

.student-hero {
  align-items: center;
  background: linear-gradient(135deg, #edf3e5, #f8f3df);
  border: 1px solid #c8d5ba;
  border-radius: 24px;
  display: flex;
  gap: 22px;
  padding: 28px;
}

.student-avatar {
  background: #fff;
  border: 2px solid #cbd8c7;
  border-radius: 50%;
  height: 112px;
  object-fit: contain;
  padding: 7px;
  width: 112px;
}

.student-avatar.custom {
  object-fit: cover;
  padding: 0;
}

.student-eyebrow {
  color: #66815b;
  display: block;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .08em;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.student-hero h2,
.learning-path-heading h2 {
  color: #174b39;
  margin: 0 0 5px;
}

.student-hero p {
  color: #52675e;
  margin: 0;
}

.student-summary {
  display: grid;
  gap: 14px;
  grid-template-columns: 1fr 1fr;
}

.student-summary > div {
  background: #fff;
  border: 1px solid #dce4d5;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  padding: 18px 20px;
}

.student-summary strong {
  color: #174b39;
  font-size: 26px;
}

.student-summary span {
  color: #6c7f65;
  font-size: 13px;
}

.progress-track,
.lesson-progress {
  background: #e1e8da;
  border-radius: 999px;
  height: 10px;
  overflow: hidden;
}

.progress-track span,
.lesson-progress span {
  background: #6f915b;
  border-radius: inherit;
  display: block;
  height: 100%;
}

.learning-path-heading {
  align-items: end;
  display: flex;
  justify-content: space-between;
}

.learning-path-heading > span {
  color: #6c7f65;
  font-size: 14px;
}

.lesson-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.lesson-card {
  background: #fff;
  border: 1px solid #dce4d5;
  border-radius: 18px;
  padding: 20px;
}

.lesson-card-topline {
  color: #718069;
  display: flex;
  font-size: 12px;
  justify-content: space-between;
  text-transform: capitalize;
}

.lesson-card h3 {
  color: #24473b;
  font-size: 18px;
  margin: 14px 0 7px;
}

.lesson-card p {
  color: #63716d;
  font-size: 14px;
  margin: 0 0 18px;
}

.lesson-card small {
  color: #6c7f65;
  display: block;
  margin-top: 8px;
}

.student-empty-lessons {
  background: #f3f6ed;
  border: 1px dashed #c8d5ba;
  border-radius: 18px;
  padding: 30px;
  text-align: center;
}

.student-empty-lessons p {
  color: #6c7f65;
  margin-bottom: 0;
}

.profile-card-actions {
  display: flex;
  gap: 8px;
}

.profile-edit-button,
.profile-delete-button {
  background: transparent;
  border: 0;
  font-size: 15px;
  font-weight: 700;
  min-height: 40px;
  padding: 8px 16px;
}

.profile-edit-button {
  color: #2c6248;
}

.profile-delete-button {
  color: #914832;
}

.profile-edit-button:hover,
.profile-delete-button:hover {
  text-decoration: underline;
}

.profile-delete-confirm {
  background: #faf0e9;
  border-radius: 12px;
  color: #713b2c;
  padding: 14px;
  width: 100%;
}

.profile-delete-confirm p {
  font-size: 14px;
  margin: 0 0 12px;
}

.profile-delete-confirm label {
  font-size: 14px;
  margin: 0 0 7px;
  text-align: left;
}

.profile-delete-confirm input {
  font-size: 15px;
  min-height: 48px;
  padding: 11px 14px;
}

.profile-delete-confirm .field-error {
  margin: 7px 0 0;
  text-align: left;
}

.profile-delete-confirm > div {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.profile-delete-confirm .danger,
.profile-delete-confirm .secondary {
  margin: 0;
  min-height: 44px;
  padding: 10px 12px;
}

.sr-only {
  clip: rect(0, 0, 0, 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}

.password-field input {
  padding-right: 50px;
}

@media (max-width: 600px) {
  .account-session {
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 38px;
    padding: 18px 20px;
  }

  .account-session .text-button {
    margin-left: 0;
    padding-left: 18px;
  }

  .child-empty-state {
    margin-top: 30px;
    padding: 38px 20px;
  }

  .profile-avatar-options {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .child-form-actions {
    grid-template-columns: 1fr;
  }

  .student-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .student-summary,
  .lesson-grid {
    grid-template-columns: 1fr;
  }
}

</style>
