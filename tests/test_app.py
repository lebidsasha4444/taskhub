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

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_database_connection(self) -> None:
        with self.app.app_context():
            result = db.session.execute(text("SELECT 1")).scalar_one()

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
