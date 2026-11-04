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
        self.assertEqual(response.json, {"status": "ok"})

    def test_database_connection(self) -> None:
        with self.app.app_context():
            result = db.session.execute(text("SELECT 1")).scalar_one()

        self.assertEqual(result, 1)

    def test_create_and_read_tasks_for_user(self) -> None:
        user_response = self.client.post("/users", json={"username": "alice"})

        self.assertEqual(user_response.status_code, 201)
        user_id = user_response.json["id"]

        create_response = self.client.post(
            f"/users/{user_id}/tasks",
            json={"title": "Shopping", "content": "Buy apples"},
        )

        self.assertEqual(create_response.status_code, 201)
        task = create_response.json
        self.assertEqual(task["title"], "Shopping")
        self.assertEqual(task["content"], "Buy apples")
        self.assertEqual(task["user_id"], user_id)
        self.assertIn("created_at", task)

        list_response = self.client.get(f"/users/{user_id}/tasks")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json, [task])

        read_response = self.client.get(f"/tasks/{task['id']}")
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json, task)

    def test_create_task_rejects_missing_user_or_content(self) -> None:
        missing_user = self.client.post(
            "/users/999/tasks",
            json={"title": "Shopping", "content": "Buy apples"},
        )
        self.assertEqual(missing_user.status_code, 404)

        user_response = self.client.post("/users", json={"username": "alice"})
        invalid_task = self.client.post(
            f"/users/{user_response.json['id']}/tasks",
            json={"title": "Shopping", "content": " "},
        )
        self.assertEqual(invalid_task.status_code, 400)


if __name__ == "__main__":
    unittest.main()
