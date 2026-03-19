from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from tests import auth_headers


class AuthApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()
        cls.admin_headers = auth_headers(cls.client)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_manager.__exit__(None, None, None)

    def test_login_returns_access_token_and_user(self) -> None:
        response = self.client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "admin-password"},
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["token_type"], "bearer")
        self.assertEqual(payload["user"]["role"], "admin")

    def test_protected_route_requires_authentication(self) -> None:
        response = self.client.get("/documents")
        self.assertEqual(response.status_code, 401)

    def test_admin_can_create_user_and_user_cannot_delete_documents(self) -> None:
        create_response = self.client.post(
            "/auth/users",
            json={"email": "user@example.com", "password": "user-password", "role": "user"},
            headers=self.admin_headers,
        )
        self.assertEqual(create_response.status_code, 201)

        login_response = self.client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "user-password"},
        )
        user_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        ingest_response = self.client.post(
            "/ingest",
            json={"payload": "shared knowledge", "metadata": {"category": "notes"}, "source_name": "shared-note"},
            headers=self.admin_headers,
        )
        document_id = ingest_response.json()["document_id"]

        delete_response = self.client.delete(f"/documents/{document_id}", headers=user_headers)
        self.assertEqual(delete_response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
