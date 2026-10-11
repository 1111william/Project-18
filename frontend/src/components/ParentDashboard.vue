<script setup>
import { ref } from 'vue'

const showProgress = ref(false)
const lessonsCompleted = 3
const totalLessons = 5
const weeklyMinutes = 45
const weeklyGoal = 60
</script>
<template>
  <div>
    <h1>Parent Dashboard</h1>

    <h2>Children</h2>

    <div>
      <h3>Ayaan (আয়ান)</h3>
      <p>Level: Beginner</p>
      <p>Time this week: 45 minutes</p>
      <p>Latest quiz: 80%</p>
      <button @click="showProgress = !showProgress">
  {{ showProgress ? 'Hide Progress' : 'View Progress' }}
</button>
    </div>

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
</template>
