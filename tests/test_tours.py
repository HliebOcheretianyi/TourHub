import logging

import pytest

from tours.models import Tour

TOURS_URL = "/api/v1/tours/"


def detail_url(tour_id: int) -> str:
    return f"{TOURS_URL}{tour_id}/"


# ---------- GET: доступно всім ----------

@pytest.mark.django_db
def test_list_tours_empty(api_client):
    response = api_client.get(TOURS_URL)
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_list_tours_anonymous(api_client, tour):
    response = api_client.get(TOURS_URL)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["title"] == tour.title


@pytest.mark.django_db
def test_retrieve_tour(api_client, tour):
    response = api_client.get(detail_url(tour.id))
    assert response.status_code == 200
    assert response.data["id"] == tour.id
    assert response.data["operator"] == tour.operator_id
    assert response.data["categories"] == [c.id for c in tour.categories.all()]


@pytest.mark.django_db
def test_retrieve_nonexistent_tour_returns_404(api_client):
    response = api_client.get(detail_url(9999))
    assert response.status_code == 404
    assert "9999" in response.data["detail"]


# ---------- POST: лише авторизовані ----------

@pytest.mark.django_db
def test_create_tour_anonymous_returns_401(api_client, tour_payload):
    response = api_client.post(TOURS_URL, tour_payload, format="json")
    assert response.status_code == 401
    assert Tour.objects.count() == 0


@pytest.mark.django_db
def test_create_tour_with_invalid_token_returns_401(api_client, tour_payload):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
    response = api_client.post(TOURS_URL, tour_payload, format="json")
    assert response.status_code == 401
    assert Tour.objects.count() == 0


@pytest.mark.django_db
def test_create_tour_as_user(user_client, tour_payload):
    response = user_client.post(TOURS_URL, tour_payload, format="json")
    assert response.status_code == 201
    assert response.data["title"] == tour_payload["title"]
    assert Tour.objects.filter(title=tour_payload["title"]).exists()


@pytest.mark.django_db
def test_create_tour_missing_required_fields_returns_400(user_client):
    response = user_client.post(TOURS_URL, {}, format="json")
    assert response.status_code == 400
    for field in ("title", "price", "duration_days", "departure_date", "operator", "destination"):
        assert field in response.data
    assert Tour.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("price", "дуже дорого"),
        ("departure_date", "завтра"),
        ("operator", 9999),
        ("categories", [9999]),
    ],
)
def test_create_tour_with_invalid_field_returns_400(user_client, tour_payload, field, bad_value):
    tour_payload[field] = bad_value
    response = user_client.post(TOURS_URL, tour_payload, format="json")
    assert response.status_code == 400
    assert field in response.data


# ---------- PUT: лише авторизовані ----------

@pytest.mark.django_db
def test_update_tour_anonymous_returns_401(api_client, tour, tour_payload):
    response = api_client.put(detail_url(tour.id), tour_payload, format="json")
    assert response.status_code == 401
    tour.refresh_from_db()
    assert tour.title == "Тиждень у Єгипті"


@pytest.mark.django_db
def test_update_tour_as_user(user_client, tour, tour_payload):
    tour_payload["price"] = 15000
    response = user_client.put(detail_url(tour.id), tour_payload, format="json")
    assert response.status_code == 200
    tour.refresh_from_db()
    assert tour.price == 15000
    assert tour.title == tour_payload["title"]


@pytest.mark.django_db
def test_update_nonexistent_tour_returns_404(user_client, tour_payload):
    response = user_client.put(detail_url(9999), tour_payload, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_tour_with_invalid_data_returns_400(user_client, tour, tour_payload):
    tour_payload["seats_available"] = "багато"
    response = user_client.put(detail_url(tour.id), tour_payload, format="json")
    assert response.status_code == 400
    assert "seats_available" in response.data


# ---------- DELETE: лише адміністратори ----------

@pytest.mark.django_db
def test_delete_tour_anonymous_returns_401(api_client, tour):
    response = api_client.delete(detail_url(tour.id))
    assert response.status_code == 401
    assert Tour.objects.filter(id=tour.id).exists()


@pytest.mark.django_db
def test_delete_tour_as_user_returns_403(user_client, tour):
    response = user_client.delete(detail_url(tour.id))
    assert response.status_code == 403
    assert response.data["detail"] == "Видаляти тури можуть лише адміністратори."
    assert Tour.objects.filter(id=tour.id).exists()


@pytest.mark.django_db
def test_delete_tour_as_admin(staff_client, tour):
    response = staff_client.delete(detail_url(tour.id))
    assert response.status_code == 204
    assert not Tour.objects.filter(id=tour.id).exists()


@pytest.mark.django_db
def test_delete_nonexistent_tour_as_admin_returns_404(staff_client):
    response = staff_client.delete(detail_url(9999))
    assert response.status_code == 404


# ---------- Логування ----------

@pytest.mark.django_db
def test_create_tour_is_logged_without_secrets(user_client, user, tour_payload, caplog):
    with caplog.at_level(logging.INFO, logger="tours"):
        response = user_client.post(TOURS_URL, tour_payload, format="json")
    assert response.status_code == 201
    assert f"Tour created: id={response.data['id']} by user_id={user.id}" in caplog.text
    assert "Bearer" not in caplog.text