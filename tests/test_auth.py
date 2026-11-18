import logging

import pytest
from django.contrib.auth.models import User

from conftest import PASSWORD

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
ME_URL = "/api/v1/auth/me/"


@pytest.fixture
def register_payload() -> dict:
    return {
        "username": "taras",
        "first_name": "Тарас",
        "last_name": "",
        "email": "taras@example.com",
        "password": "Sunny-Trip-2026",
        "password_confirm": "Sunny-Trip-2026",
    }


@pytest.mark.django_db
def test_register_user(api_client, register_payload):
    response = api_client.post(REGISTER_URL, register_payload, format="json")
    assert response.status_code == 201
    assert "password" not in response.data
    user = User.objects.get(username="taras")
    assert user.password != register_payload["password"]
    assert user.check_password(register_payload["password"])


@pytest.mark.django_db
def test_register_passwords_do_not_match(api_client, register_payload):
    register_payload["password_confirm"] = "Other-Trip-2026"
    response = api_client.post(REGISTER_URL, register_payload, format="json")
    assert response.status_code == 400
    assert "password_confirm" in response.data


@pytest.mark.django_db
def test_register_weak_password(api_client, register_payload):
    register_payload["password"] = register_payload["password_confirm"] = "12345678"
    response = api_client.post(REGISTER_URL, register_payload, format="json")
    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_register_duplicate_email(api_client, user, register_payload):
    register_payload["email"] = user.email
    response = api_client.post(REGISTER_URL, register_payload, format="json")
    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_register_invalid_email_and_missing_fields(api_client):
    response = api_client.post(REGISTER_URL, {"email": "not-an-email"}, format="json")
    assert response.status_code == 400
    for field in ("username", "email", "password", "password_confirm"):
        assert field in response.data


@pytest.mark.django_db
def test_login_returns_tokens(api_client, user):
    response = api_client.post(LOGIN_URL, {"username": user.username, "password": PASSWORD}, format="json")
    assert response.status_code == 200
    assert set(response.data) == {"access", "refresh"}


@pytest.mark.django_db
def test_login_wrong_password_returns_401_and_is_logged(api_client, user, caplog):
    with caplog.at_level(logging.WARNING, logger="accounts"):
        response = api_client.post(LOGIN_URL, {"username": user.username, "password": "wrong-pass"}, format="json")
    assert response.status_code == 401
    assert "Failed login attempt" in caplog.text
    assert "wrong-pass" not in caplog.text


@pytest.mark.django_db
def test_refresh_returns_new_access(api_client, user):
    tokens = api_client.post(LOGIN_URL, {"username": user.username, "password": PASSWORD}, format="json").data
    response = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_refresh_with_invalid_token_returns_401(api_client):
    response = api_client.post(REFRESH_URL, {"refresh": "invalid.token"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_authenticated(user_client, user):
    response = user_client.get(ME_URL)
    assert response.status_code == 200
    assert response.data["username"] == user.username
    assert response.data["is_staff"] is False


@pytest.mark.django_db
def test_me_anonymous_returns_401(api_client):
    response = api_client.get(ME_URL)
    assert response.status_code == 401