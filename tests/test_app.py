import unittest

from sqlalchemy import text

from taskhub import create_app
from taskhub.extensions import db
from taskhub.models import User


class AppFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.drop_all()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.is_json)
        self.assertIn(b"Taskhub is running", response.data)

    def test_database_connection(self) -> None:
        with self.app.app_context():
            result = db.session.execute(text("SELECT 1")).scalar_one()

        self.assertEqual(result, 1)

    def test_create_and_read_tasks_for_user(self) -> None:
        self.register_and_login()

        create_response = self.client.post(
            "/users/1/tasks",
            data={
                "title": "Shopping",
                "content": "Buy apples",
                "due_date": "2026-12-01",
                "priority": "high",
            },
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertIn(b"Shopping", create_response.data)
        self.assertIn(b"high", create_response.data)
        self.assertIn(b"Dec 01, 2026", create_response.data)

        list_response = self.client.get("/users/1/tasks")
        self.assertEqual(list_response.status_code, 200)
        self.assertFalse(list_response.is_json)
        self.assertIn(b"Shopping", list_response.data)

        read_response = self.client.get("/tasks/1")
        self.assertEqual(read_response.status_code, 200)
        self.assertFalse(read_response.is_json)
        self.assertIn(b"Buy apples", read_response.data)

    def test_pages_render_html_even_when_json_is_requested(self) -> None:
        login_page = self.client.get(
            "/login",
            headers={"Accept": "application/json"},
        )
        self.assertEqual(login_page.status_code, 200)
        self.assertFalse(login_page.is_json)
        self.assertIn(b"Welcome back", login_page.data)

    def test_create_task_rejects_missing_user_or_content(self) -> None:
        self.register_and_login()
        missing_user = self.client.post(
            "/users/999/tasks",
            data={"title": "Shopping", "content": "Buy apples"},
        )
        self.assertEqual(missing_user.status_code, 404)
        self.assertFalse(missing_user.is_json)

        invalid_task = self.client.post(
            "/users/1/tasks",
            data={"title": "Shopping", "content": " "},
        )
        self.assertEqual(invalid_task.status_code, 400)
        self.assertFalse(invalid_task.is_json)

    def test_registration_login_and_password_hashing(self) -> None:
        registration_page = self.client.get("/register")
        for field in (
            b'name="username"',
            b'name="email"',
            b'name="password"',
            b'name="confirm_password"',
        ):
            self.assertIn(field, registration_page.data)
        self.assertIn(b'placeholder="Choose a username"', registration_page.data)
        self.assertIn(b'placeholder="you@example.com"', registration_page.data)

        invalid_registration = self.client.post(
            "/register",
            data={
                "username": "alice",
                "email": "alice@example.com",
                "password": "password123",
                "confirm_password": "different123",
            },
        )
        self.assertEqual(invalid_registration.status_code, 400)
        self.assertIn(b"Passwords do not match", invalid_registration.data)

        registration = self.client.post(
            "/register",
            data={
                "username": "alice",
                "email": "ALICE@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
        )
        self.assertEqual(registration.status_code, 302)
        self.assertIn("/users/1/overview", registration.headers["Location"])
        with self.app.app_context():
            user = db.session.scalar(
                db.select(User).where(User.email == "alice@example.com")
            )
            self.assertIsNotNone(user)
            assert user is not None
            self.assertNotEqual(user.password_hash, "password123")

        incorrect_login = self.client.post(
            "/login",
            data={"email": "alice@example.com", "password": "wrong-password"},
        )
        self.assertEqual(incorrect_login.status_code, 401)
        self.assertIn(b"email or password is incorrect", incorrect_login.data)

        login = self.client.post(
            "/login",
            data={"email": "alice@example.com", "password": "password123"},
        )
        self.assertEqual(login.status_code, 302)
        self.assertIn("/users/1/overview", login.headers["Location"])

    def test_dashboard_task_creation_and_logout_flow(self) -> None:
        self.register_and_login()

        overview = self.client.get("/users/1/overview")
        self.assertEqual(overview.status_code, 200)
        self.assertIn(b"All your tasks", overview.data)
        self.assertIn(b"Create new task", overview.data)

        tasks = self.client.get("/users/1/tasks")
        self.assertEqual(tasks.status_code, 200)
        for field in (b'name="title"', b'name="content"', b'name="due_date"', b'name="priority"'):
            self.assertIn(field, tasks.data)

        created = self.client.post(
            "/users/1/tasks",
            data={
                "title": "Prepare demo",
                "content": "Walk through the new dashboard",
                "due_date": "2026-12-02",
                "priority": "middle",
            },
        )
        self.assertEqual(created.status_code, 200)
        self.assertIn(b"middle", created.data)

        detail = self.client.get("/tasks/1")
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b"Walk through the new dashboard", detail.data)
        self.assertIn(b"Dec 02, 2026", detail.data)

        logout = self.client.post("/logout")
        self.assertEqual(logout.status_code, 302)
        self.assertIn("/login", logout.headers["Location"])
        self.assertEqual(self.client.get("/users/1/overview").status_code, 302)

    def register_and_login(self) -> None:
        registration = self.client.post(
            "/register",
            data={
                "username": "alice",
                "email": "alice@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
        )
        self.assertEqual(registration.status_code, 302)
        login = self.client.post(
            "/login",
            data={"email": "alice@example.com", "password": "password123"},
        )
        self.assertEqual(login.status_code, 302)


if __name__ == "__main__":
    unittest.main()
