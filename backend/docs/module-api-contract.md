# Module API contract: Quiz, Audio, Levels and Progress

Last updated: 23 October 2026. Maintained by Jin Shang. Change this file only through a reviewed pull request.

| Module | Owner | Backlog items |
| --- | --- | --- |
| Quiz | Yuchen Zhang | PB11 to PB14 |
| Audio | Hao Jiang | PB09, PB10 |
| Levels and Progress | Zihao Yuan | PB15, PB16 |

This file adds module routes to `api-contract.md`, and every rule in `api-contract.md` still applies. If you use an AI coding tool, give it both files before asking it to write code, then check its output against the review checklist in section 6.

## 1. Rules for every route in this file

- Return `ok(data)` on success and raise `ApiError`, `NotFound` or `Forbidden` on failure. Never return a bare dictionary.
- JSON field names are camelCase and match the column names in `backend/app/models/entities.py`.
- **Parent** in the tables below means the route uses `Depends(current_parent_id)`. **Owner** means it uses `Depends(owned_child)`, and the path parameter must be named `childID`.
- `POST` and `PUT` routes are already covered by the shared Origin check. Do not bypass it.
- Only lessons with `isPublished = true` are visible. A missing or unpublished lesson returns `404 NOT_FOUND`.
- These routes need no schema change. If you think one is needed, ask Jin first and include an Alembic migration in the same pull request. Never create tables when the app starts.
- Each route needs tests for a successful call, `401` without a session and `404` for a missing ID. Every route with `{childID}` also needs a test where another parent gets `403`. Follow `backend/tests/test_core_children.py` for route tests, and `test_authentication_and_ownership` in `backend/tests/test_integration_mysql.py` for the `401` and `403` cases.
- Open one pull request per module. The Backend CI check must pass before review.

Error responses used in this file: `400 VALIDATION_FAILED` with `fields`, `401 UNAUTHENTICATED`, `403 FORBIDDEN`, `403 CSRF_FAILED` and `404 NOT_FOUND`.

## 2. Quiz: Yuchen Zhang

Tables: `Quiz`, `QuizQuestion`, `QuizOption`, `QuizResult`.

Replace the placeholder routes in `backend/app/routers/quizzes.py`. Keep `calculate_score()` in `backend/app/services/quiz_service.py`, which already compares the chosen options with the correct options as sets, and change its dictionary keys to the new field names. Rename the fields in `backend/app/schemas/quiz.py` to the camelCase names below, and remove `child_id` from the request body, because the child now comes from the path. Declare the list route as `@router.get("")`, as `GET /api/children` does, so its path is `/api/quizzes` without a trailing slash.

`questionKind` values for the Alpha:

| Value | Meaning |
| --- | --- |
| `single` | Exactly one correct option |
| `multiple` | One or more correct options |
| `boolean` | Two options, True and False |

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /api/quizzes?lessonID={lessonID}` | Parent | List the quizzes of a published lesson. `lessonID` is required. |
| `GET /api/quizzes/{quizID}` | Parent | Questions and options, without answers |
| `POST /api/children/{childID}/quizzes/{quizID}/attempts` | Owner | Submit answers. The server scores and saves the attempt. |
| `GET /api/children/{childID}/quiz-results` | Owner | The child's results, newest first. Optional filter `?quizID=`. |

### GET /api/quizzes?lessonID=1

```json
[
  {
    "quizID": 1,
    "lessonID": 1,
    "title": "Vowel letters check",
    "passMark": 70,
    "questionCount": 2
  }
]
```

### GET /api/quizzes/1

`isCorrect` must never appear in this response. If it does, a child can read the answers in the browser's developer tools. Order questions by `questionOrder` and options by `optionOrder`. The example below shows only the first of the quiz's two questions.

```json
{
  "quizID": 1,
  "lessonID": 1,
  "title": "Vowel letters check",
  "passMark": 70,
  "questions": [
    {
      "questionID": 1,
      "questionOrder": 1,
      "questionKind": "single",
      "prompt": "Which letter sounds like the a in father?",
      "mediaPath": null,
      "options": [
        { "optionID": 1, "optionOrder": 1, "optionText": "অ" },
        { "optionID": 2, "optionOrder": 2, "optionText": "আ" },
        { "optionID": 3, "optionOrder": 3, "optionText": "ই" }
      ]
    }
  ]
}
```

### POST /api/children/1/quizzes/1/attempts

Request:

```json
{
  "answers": [
    { "questionID": 1, "selectedOptionIDs": [2] },
    { "questionID": 2, "selectedOptionIDs": [5] }
  ]
}
```

Server rules:

1. A quiz with no questions cannot be attempted and returns `404 NOT_FOUND`. The database rejects a result whose `totalCount` is 0.
2. Return `400 VALIDATION_FAILED` when a `questionID` is not in this quiz, appears twice, or has an option from a different question. Name the field, for example `answers[1].selectedOptionIDs`.
3. A question that is left out counts as wrong.
4. A question is correct only when the chosen options are exactly the correct options.
5. `totalCount` is the number of questions in the quiz. `score` is `round(correctCount * 100 / totalCount)`. `passed` is `score >= passMark`.
6. `attemptNumber` is the number of earlier attempts by this child on this quiz, plus one.
7. Save one `QuizResult` row. The client never sends a score.

Response. This is the only response that reveals the correct answers:

```json
{
  "resultID": 7,
  "quizID": 1,
  "score": 50,
  "correctCount": 1,
  "totalCount": 2,
  "passed": false,
  "attemptNumber": 1,
  "submittedAt": "2026-10-23T11:30:00",
  "feedback": [
    { "questionID": 1, "correct": true, "correctOptionIDs": [2] },
    { "questionID": 2, "correct": false, "correctOptionIDs": [4] }
  ]
}
```

### GET /api/children/1/quiz-results

```json
[
  {
    "resultID": 7,
    "quizID": 1,
    "quizTitle": "Vowel letters check",
    "score": 50,
    "correctCount": 1,
    "totalCount": 2,
    "passed": false,
    "attemptNumber": 1,
    "submittedAt": "2026-10-23T11:30:00"
  }
]
```

Child Home and Jassim's Parent Dashboard read this route.

The two routes under `/api/children/...` can live in `quizzes.py` on a second `APIRouter`, registered in `backend/app/main.py` with the prefix `/api/children`.

## 3. Audio: Hao Jiang

Table: `AudioResource`, with the columns `audioID`, `lessonID`, `contentID`, `label`, `filePath`, `source`, `verified` and `createdAt`.

File storage for the Alpha:

- Put each audio file in `frontend/public/` at the same path as its `filePath`. For example, `filePath = audio/letters/vowel-01.mp3` is the file `frontend/public/audio/letters/vowel-01.mp3`, and the browser loads it from `/audio/letters/vowel-01.mp3`.
- Use `.mp3` files with lower-case names joined by hyphens, and keep each file under 1 MB.
- `source` records where the sound came from, such as a named recording or a text-to-speech tool. `verified` is true only after a Bangla speaker has checked the sound.
- No backend route serves the audio files themselves.

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /api/lessons/{lessonID}/audio` | Parent | All audio for a published lesson, ordered by `audioID` |
| `GET /api/audio/{audioID}` | Parent | One audio item |

Both routes use this item shape. The list route returns an array of items.

```json
{
  "audioID": 1,
  "lessonID": 1,
  "contentID": 3,
  "label": "Vowel one",
  "url": "/audio/letters/vowel-01.mp3",
  "source": "Recorded by a Bangla speaker",
  "verified": false
}
```

`url` is `"/" + filePath`. `contentID` is null when the audio belongs to the whole lesson rather than one content block, and `source` is null until someone fills it in. The player shows a "Draft audio" label when `verified` is false, and shows a short message when a file cannot be loaded.

To add audio, put the files and an SQL file of `INSERT INTO AudioResource` rows in your pull request. Jin imports the rows into the shared database.

Create `backend/app/routers/audio.py` and register it in `backend/app/main.py` with the prefix `/api`.

## 4. Levels and Progress: Zihao Yuan

Tables: `LearningLevel`, `Lesson`, `Progress` and the `currentLevelID` column of `ChildProfile`. `Progress` holds one row per child and lesson, enforced by the unique key `uq_progress_child_lesson`.

Create `backend/app/routers/levels.py`. Register the two level routes in `backend/app/main.py` with the prefix `/api`, and put the two progress routes on a second `APIRouter` registered with the prefix `/api/children`.

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /api/levels` | Parent | All levels, ordered by `levelOrder` |
| `GET /api/levels/{levelID}/lessons` | Parent | Published lessons of one level |
| `GET /api/children/{childID}/progress` | Owner | The child's progress in the current level |
| `POST /api/children/{childID}/lessons/{lessonID}/progress` | Owner | Record progress for one published lesson |

### GET /api/levels

`lessonCount` counts published lessons only.

```json
[
  {
    "levelID": 1,
    "levelOrder": 1,
    "title": "Beginner",
    "description": "Letters and basic sounds",
    "passMark": 70,
    "lessonCount": 3
  }
]
```

### GET /api/levels/1/lessons

Order by `lessonOrder`, then `lessonID`. Do not order by `strand`. The client wants letters before culture, so the content data numbers `lessonOrder` across the whole level. Jin will renumber the seed and the imported lessons, and will change Child Home, `GET /api/children/{childID}/home`, to the same order. That route currently sorts by `strand` first, which puts culture before letters whatever `lessonOrder` says.

```json
[
  {
    "lessonID": 1,
    "levelID": 1,
    "strand": "letters",
    "lessonOrder": 1,
    "title": "Vowel letters",
    "summary": "First group of Bangla vowels",
    "coverImage": null,
    "estimatedMinutes": 5
  }
]
```

### GET /api/children/1/progress

`lessons` lists every published lesson in the child's current level, in the same order as `GET /api/levels/{levelID}/lessons`. A lesson with no `Progress` row shows `percentComplete` 0, `completed` false, `secondsSpent` 0 and `lastViewedAt` null. `overallPercent` uses the same rule as Child Home: the average `percentComplete` of those lessons, rounded. A child with no current level gets `currentLevelID` null, zero counts and an empty list.

```json
{
  "currentLevelID": 1,
  "completedLessons": 1,
  "totalLessons": 3,
  "overallPercent": 48,
  "lessons": [
    {
      "lessonID": 1,
      "percentComplete": 100,
      "completed": true,
      "secondsSpent": 300,
      "lastViewedAt": "2026-10-23T11:00:00"
    },
    {
      "lessonID": 2,
      "percentComplete": 45,
      "completed": false,
      "secondsSpent": 120,
      "lastViewedAt": "2026-10-23T11:20:00"
    },
    {
      "lessonID": 4,
      "percentComplete": 0,
      "completed": false,
      "secondsSpent": 0,
      "lastViewedAt": null
    }
  ]
}
```

### POST /api/children/1/lessons/2/progress

This is a `POST`, not a `PUT`, because each call adds time: sending the same call twice changes the stored total.

Request:

```json
{ "percentComplete": 60, "secondsSpent": 45, "completed": false }
```

Server rules:

1. `percentComplete` is 0 to 100. `secondsSpent` is 0 to 3600 and means the time spent since the last call, which is added to the stored total. `completed` is optional and defaults to false.
2. Create the row if it does not exist. Otherwise update it.
3. `percentComplete` never goes down, so keep the larger of the stored and new values. `completed` stays true once it is true, and `completed: true` sets `percentComplete` to 100.
4. Set `lastViewedAt` to the current time.
5. Two calls at the same moment must not fail or create two rows. If the insert hits the unique key, update the existing row instead.

Response, the saved row:

```json
{
  "lessonID": 2,
  "percentComplete": 60,
  "completed": false,
  "secondsSpent": 165,
  "lastViewedAt": "2026-10-23T11:30:00"
}
```

Level-up, PB21, comes later. Agree the rule with the team before coding it. One option is that every published lesson in the level is completed and every quiz in the level is passed.

## 5. Who calls these routes

| Route | Called by |
| --- | --- |
| Quiz list, quiz detail, attempts | Qi's learning pages |
| Quiz results | Child Home and Jassim's Parent Dashboard |
| Audio | Qi's learning pages, through Hao's player |
| Levels and lessons | Child Home and Qi's learning pages |
| Progress `POST` | Qi's learning pages, when a child finishes part of a lesson |
| Progress `GET` | Child Home and Jassim's Parent Dashboard |

The learning pages need real `lessonID` values. After the content import, Jin will post the IDs of the vowel, consonant and word lessons in the group chat.

## 6. Review checklist

Jin checks every pull request against this list before merging:

- [ ] Every route returns the shared envelope with camelCase fields.
- [ ] Every route with `{childID}` uses `owned_child`.
- [ ] The quiz detail never includes `isCorrect`, and the server calculates the score.
- [ ] Progress never goes down, and there is one row per child and lesson.
- [ ] Tests cover success, `401`, `404`, and `403` for another parent's child.
- [ ] There is no schema change, or an Alembic migration is included and agreed with Jin.
- [ ] The Backend CI check is green.
