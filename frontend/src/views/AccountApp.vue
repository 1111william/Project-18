<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { accountApi } from '../services/accountApi'

const page = ref('login'), flow = ref('login'), error = ref(''), notice = ref('')
const email = ref(''), password = ref(''), confirm = ref(''), code = ref(''), visible = ref(false)
const fieldErrors = ref({})
const busy = ref(false), booting = ref(true), challenge = ref(null), signedIn = ref(null)
const developmentCodes = ref(false), now = ref(Date.now()), heading = ref(null)
const titles = { login: 'Welcome back.', register: 'Start something wonderful.', verify: 'Check your inbox.' }
const subtitles = { login: 'A little learning. A world of possibility.', register: 'Create your account and begin your journey.', verify: 'Enter the six-digit code to continue.' }
const cooldown = computed(() => Math.max(0, Math.ceil(((challenge.value?.resend_at || 0) * 1000 - now.value) / 1000)))
const timer = setInterval(() => now.value = Date.now(), 1000)
onUnmounted(() => clearInterval(timer))

function go(next) {
  page.value = next; error.value = ''; notice.value = ''; fieldErrors.value = {}; password.value = ''; confirm.value = ''; visible.value = false
  if (next === 'login') { challenge.value = null; code.value = '' }
  nextTick(() => heading.value?.focus())
}
function clearFieldError(field) {
  if (!fieldErrors.value[field]) return
  fieldErrors.value = { ...fieldErrors.value, [field]: '' }
}
function errorField(exception) {
  if (!exception.status || exception.status >= 500) return null
  if (page.value === 'verify') return 'code'
  if (page.value === 'register' && exception.status === 409) return 'email'
  return 'password'
}
function validateFields() {
  const next = {}
  if (['login', 'register'].includes(page.value)) {
    const normalizedEmail = email.value.trim()
    if (!normalizedEmail) next.email = 'Enter your email address.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) next.email = 'Enter a valid email address.'
    if (!password.value) next.password = page.value === 'login' ? 'Please enter your password.' : 'Enter your password.'
    else if (page.value === 'register' && password.value.length < 8) next.password = 'Password must be at least 8 characters.'
    else if (page.value === 'register' && password.value.length > 128) next.password = 'Password must be no more than 128 characters.'
  }
  if (page.value === 'register') {
    if (!confirm.value) next.confirm = 'Enter your password again.'
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
    } catch (e) { if (e.status !== 401) throw e }
  } catch (e) { error.value = e.message }
  finally { booting.value = false }
})
function submit() {
  if (!validateFields()) return
  run(async () => {
    if (page.value === 'verify') {
      const result = await accountApi('/auth/verify-code', { method: 'POST', body: { challenge_id: challenge.value.challenge_id, code: code.value } })
      signedIn.value = result.user; email.value = result.user.email
      go('login')
      notice.value = flow.value === 'register' ? 'Account created successfully. You are signed in.' : 'You have logged in successfully.'
      return
    }
    flow.value = page.value
    challenge.value = await accountApi(`/auth/${page.value}`, { method: 'POST', body: { email: email.value.trim(), password: password.value } })
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
    signedIn.value = null; email.value = ''; go('login')
  })
}
</script>

<template>
  <main class="account-page">
    <section class="account-content" aria-labelledby="page-title" :aria-busy="busy || booting">
      <h1 id="page-title" ref="heading" tabindex="-1">{{ titles[page] }}</h1>
      <p class="subtitle">{{ subtitles[page] }}</p>
      <p v-if="booting" class="notice" role="status">Connecting to your account…</p>
      <p v-if="notice" class="notice" role="status">{{ notice }}</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <template v-if="!booting">
        <div v-if="['login', 'register'].includes(page)" class="tabs" aria-label="Account action"><button :disabled="busy || !!signedIn" :class="{ active: page === 'login' }" :aria-pressed="page === 'login'" @click="go('login')">Log in</button><button :disabled="busy || !!signedIn" :class="{ active: page === 'register' }" :aria-pressed="page === 'register'" @click="go('register')">Create account</button></div>
        <div v-if="signedIn" class="notice" role="status">You are signed in as {{ signedIn.email }}.<br><button class="text-button" :disabled="busy" @click="signOut">Sign out</button></div>
        <form v-else novalidate @submit.prevent="submit"><fieldset :disabled="busy">
          <template v-if="['login', 'register'].includes(page)"><label for="email">Email address</label><input id="email" v-model="email" type="email" autocomplete="email" placeholder="you@example.com" required maxlength="254" :aria-invalid="!!fieldErrors.email" :aria-describedby="fieldErrors.email ? 'email-error' : undefined" @input="clearFieldError('email')"><p v-if="fieldErrors.email" id="email-error" class="field-error" role="alert">{{ fieldErrors.email }}</p></template>
          <template v-if="['login', 'register'].includes(page)"><label for="password">Password</label><div class="password-field"><input id="password" v-model="password" :type="visible ? 'text' : 'password'" :autocomplete="page === 'login' ? 'current-password' : 'new-password'" placeholder="Enter your password" required minlength="8" maxlength="128" :aria-invalid="!!fieldErrors.password" :aria-describedby="fieldErrors.password ? 'password-error' : undefined" @input="clearFieldError('password')"><button type="button" :aria-label="visible ? 'Hide password' : 'Show password'" :aria-pressed="visible" @click="visible = !visible">{{ visible ? 'Hide' : 'Show' }}</button></div><p v-if="fieldErrors.password" id="password-error" class="field-error" role="alert">{{ fieldErrors.password }}</p><p v-if="page !== 'login'" class="field-hint">Use 8–128 characters.</p></template>
          <template v-if="page === 'register'"><label for="confirm">Confirm password</label><input id="confirm" v-model="confirm" :type="visible ? 'text' : 'password'" autocomplete="new-password" placeholder="Enter your password again" required minlength="8" maxlength="128" :aria-invalid="!!fieldErrors.confirm" :aria-describedby="fieldErrors.confirm ? 'confirm-error' : undefined" @input="clearFieldError('confirm')"><p v-if="fieldErrors.confirm" id="confirm-error" class="field-error" role="alert">{{ fieldErrors.confirm }}</p></template>
          <template v-if="page === 'verify'"><div class="email-summary">Verification for <strong>{{ email }}</strong></div><label for="code">6-digit verification code</label><input id="code" v-model="code" class="code-input" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" required :aria-invalid="!!fieldErrors.code" :aria-describedby="fieldErrors.code ? 'code-error code-hint' : 'code-hint'" @input="clearFieldError('code')"><p v-if="fieldErrors.code" id="code-error" class="field-error" role="alert">{{ fieldErrors.code }}</p><p id="code-hint" class="field-hint">Valid for 10 minutes. Up to 5 attempts.</p><div v-if="challenge?.delivery === 'development'" class="development-code">Local development code: <strong>{{ challenge.development_code }}</strong><br>No email was sent.</div></template>
          <button class="primary submit-button" type="submit">{{ busy ? 'Please wait…' : ({ login: 'Continue', register: 'Create account', verify: 'Verify & continue' })[page] }} <span v-if="!busy" aria-hidden="true">→</span></button>
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

</style>
