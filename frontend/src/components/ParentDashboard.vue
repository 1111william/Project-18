<script setup>
import { ref } from 'vue'

const showProgress = ref(false)
const lessonsCompleted = 3
const totalLessons = 5
const weeklyMinutes = 45
const weeklyGoal = 60
const latestQuizScore = 80
</script>

<template>
  <div>
    <h1>Parent Dashboard</h1>

    <h2>Children</h2>

    <div>
      <h3>Ayaan (আয়ান)</h3>
      <p>Level: Beginner</p>
      <p>Time this week: 45 minutes</p>
      <p>Latest quiz: {{ latestQuizScore }}%</p>

      <button @click="showProgress = !showProgress">
        {{ showProgress ? 'Hide Progress' : 'View Progress' }}
      </button>
    </div>

    <div v-if="showProgress">
      <h2>Learning Progress</h2>

      <h3>Lesson Progress</h3>
      <p>{{ lessonsCompleted }} of {{ totalLessons }} lessons completed</p>
      <progress :value="lessonsCompleted" :max="totalLessons"></progress>

      <h3>Weekly Learning Goal</h3>
      <p>{{ weeklyMinutes }} of {{ weeklyGoal }} minutes completed</p>
      <progress :value="weeklyMinutes" :max="weeklyGoal"></progress>

      <p>Quiz results and learning activity will be shown here.</p>

      <h2>Weekly Learning Summary</h2>
      <p>Sample data for testing only</p>
      <ul>
        <li>Bangla letters learned: 8</li>
        <li>Lessons completed: 3</li>
        <li>Quizzes attempted: 2</li>
        <li>Average quiz score: 80%</li>
      </ul>

      <h2>Parent Recommendations</h2>
      <p>Encourage your child to practise Bangla letters for 10 minutes each day.</p>
    </div>
  </div>
</template>

<style scoped>
h1 {
  color: #2563eb;
  font-size: 28px;
  margin-bottom: 24px;
}

h2 {
  color: #1e293b;
  margin-top: 28px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
}

h3 {
  color: #334155;
  margin-top: 18px;
}

p, li {
  color: #475569;
  line-height: 1.7;
}

button {
  background-color: #2563eb;
  color: white;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  margin-top: 12px;
}

button:hover {
  background-color: #1d4ed8;
}

progress {
  width: 100%;
  max-width: 400px;
  height: 18px;
  accent-color: #22c55e;
  display: block;
  margin: 12px 0 20px;
}

ul {
  padding-left: 24px;
}
</style>

