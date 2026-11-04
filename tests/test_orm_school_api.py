import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_session
from models import Department, Student
from school_app import app
from seed import seed

engine = create_engine(
    "sqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class TestSchoolOrmApi(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        with TestSession() as session:
            seed(session)

        def override():
            session = TestSession()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_session] = override
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)

    def test_list_students_page(self):
        response = self.client.get("/students")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)
        names = {item["full_name"] for item in response.json()}
        self.assertIn("Emma Wilson", names)

    def test_create_student_returns_201(self):
        payload = {
            "full_name": "Test Student",
            "email": "test.student@school.edu",
            "birth_date": "2020-01-15",
            "department_id": 5,
            "status": "active",
        }
        response = self.client.post("/students", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["full_name"], "Test Student")

    def test_create_validation_422(self):
        payload = {
            "full_name": "",
            "email": "bad",
            "birth_date": "2020-01-15",
            "department_id": 5,
            "status": "active",
        }
        response = self.client.post("/students", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_missing_student_404(self):
        response = self.client.get("/students/99999")
        self.assertEqual(response.status_code, 404)

    def test_partial_patch_updates_fields(self):
        response = self.client.patch("/students/1", json={"status": "on_leave"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "on_leave")

    def test_delete_student_removes_row(self):
        response = self.client.delete("/students/1")
        self.assertEqual(response.status_code, 204)
        response = self.client.get("/students/1")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
