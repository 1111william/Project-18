import os
import unittest

from sqlalchemy import CheckConstraint, inspect
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SESSION_SECRET",
    "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_NAME", "coseat18_test")
os.environ.setdefault("DB_SSL_MODE", "disabled")

from backend.app.database import Base
import backend.app.models  # noqa: F401,E402
from backend.app.models import LearningLevel


EXPECTED_TABLES = {
    "Parent",
    "ChildProfile",
    "LearningLevel",
    "Lesson",
    "LearningContent",
    "AudioResource",
    "Quiz",
    "QuizQuestion",
    "QuizOption",
    "Progress",
    "QuizResult",
}

EXPECTED_CHECKS = {
    "ck_learning_level_order_positive",
    "ck_learning_level_pass_mark_range",
    "ck_lesson_order_positive",
    "ck_lesson_estimated_minutes_nonnegative",
    "ck_learning_content_block_order_positive",
    "ck_quiz_pass_mark_range",
    "ck_quiz_question_order_positive",
    "ck_quiz_option_order_positive",
    "ck_progress_percent_complete_range",
    "ck_progress_seconds_spent_nonnegative",
    "ck_quiz_result_score_range",
    "ck_quiz_result_correct_count_nonnegative",
    "ck_quiz_result_total_count_positive",
    "ck_quiz_result_correct_lte_total",
    "ck_quiz_result_attempt_number_positive",
}


class DatabaseModelContractTests(unittest.TestCase):
    def test_original_eleven_table_names_are_preserved(self):
        self.assertEqual(set(Base.metadata.tables), EXPECTED_TABLES)

    def test_all_tables_declare_utf8mb4_storage(self):
        for table in Base.metadata.tables.values():
            with self.subTest(table=table.name):
                options = table.dialect_options["mysql"]
                self.assertEqual(options["charset"], "utf8mb4")
                self.assertEqual(options["collate"], "utf8mb4_unicode_ci")

                ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))
                self.assertIn("CHARSET=utf8mb4", ddl)
                self.assertIn("COLLATE utf8mb4_unicode_ci", ddl)

    def test_named_check_constraints_match_hardening_contract(self):
        actual = {
            constraint.name
            for table in Base.metadata.tables.values()
            for constraint in table.constraints
            if isinstance(constraint, CheckConstraint)
        }
        self.assertEqual(actual, EXPECTED_CHECKS)

    def test_level_delete_defers_loaded_lessons_to_database_cascade(self):
        relationship = inspect(LearningLevel).relationships["lessons"]
        self.assertEqual(relationship.passive_deletes, "all")


if __name__ == "__main__":
    unittest.main()
