import unittest

from sqlalchemy import text

from taskhub import create_app
from taskhub.extensions import db


class AppFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(
            {
                "TESTING": True,
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
        user_response = self.client.post("/users", data={"username": "alice"})

        self.assertEqual(user_response.status_code, 200)
        self.assertIn(b"alice", user_response.data)

        create_response = self.client.post(
            "/users/1/tasks",
            data={"title": "Shopping", "content": "Buy apples"},
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertIn(b"Shopping", create_response.data)

        list_response = self.client.get("/users/1/tasks")
        self.assertEqual(list_response.status_code, 200)
        self.assertFalse(list_response.is_json)
        self.assertIn(b"Shopping", list_response.data)

        read_response = self.client.get("/tasks/1")
        self.assertEqual(read_response.status_code, 200)
        self.assertFalse(read_response.is_json)
        self.assertIn(b"Buy apples", read_response.data)

    def test_pages_render_html_even_when_json_is_requested(self) -> None:
        users_page = self.client.get(
            "/users",
            headers={"Accept": "application/json"},
        )
        self.assertEqual(users_page.status_code, 200)
        self.assertFalse(users_page.is_json)
        self.assertIn(b"<h1>Users</h1>", users_page.data)

    def test_create_task_rejects_missing_user_or_content(self) -> None:
        missing_user = self.client.post(
            "/users/999/tasks",
            data={"title": "Shopping", "content": "Buy apples"},
        )
        self.assertEqual(missing_user.status_code, 404)
        self.assertFalse(missing_user.is_json)

        self.client.post("/users", data={"username": "alice"})
        invalid_task = self.client.post(
            "/users/1/tasks",
            data={"title": "Shopping", "content": " "},
        )
        self.assertEqual(invalid_task.status_code, 400)
        self.assertFalse(invalid_task.is_json)


if __name__ == "__main__":
    unittest.main()
