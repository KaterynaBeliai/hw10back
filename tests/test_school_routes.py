import unittest
from types import SimpleNamespace
from unittest.mock import patch

import routes


def make_request(path="/students/en", params=None, method="GET", body=""):
    return SimpleNamespace(
        method=method,
        path=path,
        params=params or {},
        body=body,
        query={},
        cookies={},
        headers={},
    )


class SchoolRouteTests(unittest.TestCase):
    @patch("routes.db.fetch_all")
    def test_students_list_includes_department_name(self, fetch_all):
        fetch_all.return_value = [
            {
                "id": 1,
                "full_name": "Emma Wilson",
                "department_id": 5,
                "department_name": "Grade 1",
                "status": "active",
            }
        ]

        response = routes.student_list_en(make_request())

        self.assertEqual(response.status, 200)
        self.assertIn("Emma Wilson", response.body)
        self.assertIn("Grade 1", response.body)

    @patch("routes.db.fetch_all")
    def test_student_detail_shows_courses_hierarchy_and_profile(self, fetch_all):
        fetch_all.side_effect = [
            [
                {
                    "id": 1,
                    "full_name": "Emma Wilson",
                    "email": "emma.wilson@school.edu",
                    "birth_date": "2010-05-14",
                    "status": "active",
                    "department_id": 5,
                    "department_name": "Grade 1",
                }
            ],
            [
                {"id": 1, "title": "Algebra I"},
                {"id": 2, "title": "Biology Basics"},
            ],
            [
                {"name": "School", "depth": 0},
                {"name": "Primary School", "depth": 1},
                {"name": "Grade 1", "depth": 2},
            ],
            [
                {
                    "student_id": 1,
                    "phone": "+1-555-0101",
                    "emergency_contact": "Anna Wilson",
                    "notes": "Enjoys mathematics club.",
                }
            ],
        ]

        response = routes.student_detail_en(make_request(path="/student/1/en", params={"id": "1"}))

        self.assertEqual(response.status, 200)
        self.assertIn("Emma Wilson", response.body)
        self.assertIn("Algebra I", response.body)
        self.assertIn("School", response.body)
        self.assertIn("+1-555-0101", response.body)

    @patch("routes.db.fetch_all")
    def test_unknown_student_id_returns_404(self, fetch_all):
        fetch_all.return_value = []

        response = routes.student_detail_en(make_request(path="/student/999/en", params={"id": "999"}))

        self.assertEqual(response.status, 404)

    @patch("routes.db.fetch_all")
    def test_invalid_student_id_does_not_query_database(self, fetch_all):
        response = routes.student_detail_en(make_request(path="/student/not-a-number/en", params={"id": "abc"}))

        self.assertIsNone(response)
        fetch_all.assert_not_called()

    @patch("routes.db.execute")
    @patch("routes.db.fetch_all")
    def test_valid_extra_form_calls_execute_once(self, fetch_all, execute):
        fetch_all.side_effect = [
            [{"id": 1, "full_name": "Emma Wilson", "email": "emma.wilson@school.edu"}],
            [],
        ]
        execute.return_value = None

        response = routes.student_extra_post(
            make_request(
                path="/student/1/en/extra",
                params={"id": "1"},
                method="POST",
                body="phone=%2B1-555-0123&emergency_contact=Jane+Smith&notes=Needs+support",
            )
        )

        self.assertEqual(response.status, 302)
        execute.assert_called_once()
        self.assertIn("INSERT INTO student_profiles", execute.call_args[0][0])

    @patch("routes.db.execute")
    @patch("routes.db.fetch_all")
    def test_duplicate_extra_profile_returns_400_without_execute(self, fetch_all, execute):
        fetch_all.side_effect = [
            [{"id": 1, "full_name": "Emma Wilson", "email": "emma.wilson@school.edu"}],
            [{"student_id": 1}],
        ]

        response = routes.student_extra_post(
            make_request(
                path="/student/1/en/extra",
                params={"id": "1"},
                method="POST",
                body="phone=%2B1-555-0123&emergency_contact=Jane+Smith&notes=Needs+support",
            )
        )

        self.assertEqual(response.status, 400)
        execute.assert_not_called()

    @patch("routes.db.fetch_all")
    def test_course_detail_lists_teacher_and_linked_students(self, fetch_all):
        fetch_all.side_effect = [
            [{
                "id": 1,
                "title": "Algebra I",
                "credits": 3,
                "schedule": "Mon/Wed 09:00",
                "teacher_id": 1,
                "teacher_name": "Nora Smith",
            }],
            [
                {"id": 1, "full_name": "Emma Wilson"},
                {"id": 2, "full_name": "Liam Martin"},
            ],
        ]

        response = routes.course_detail_en(make_request(path="/course/1/en", params={"id": "1"}))

        self.assertEqual(response.status, 200)
        self.assertIn("Algebra I", response.body)
        self.assertIn("Nora Smith", response.body)
        self.assertIn("Emma Wilson", response.body)
        self.assertIn("Liam Martin", response.body)

    @patch("routes.db.fetch_all")
    def test_unknown_course_id_returns_404(self, fetch_all):
        fetch_all.return_value = []

        response = routes.course_detail_en(make_request(path="/course/999/en", params={"id": "999"}))

        self.assertEqual(response.status, 404)


if __name__ == "__main__":
    unittest.main()
