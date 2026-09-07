def calculate_score(submitted_answers, correct_answers):
    score = 0

    for answer in submitted_answers:
        question_id = answer["question_id"]

        submitted = set(answer["selected_option_ids"])
        correct = set(correct_answers.get(question_id, []))

        if submitted == correct:
            score += 1

    return score