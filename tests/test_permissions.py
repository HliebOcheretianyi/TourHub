import pytest

from tours.models import Destination, TourOperator

OPERATORS_URL = "/api/v1/operators/"
OPERATOR_PAYLOAD = {
    "name": "Mountain Trips", "description": "Гірські тури", "email": "hi@mountain.example", "phone": "+380501112233",
}


@pytest.mark.django_db
def test_list_operators_anonymous(api_client, operator):
    response = api_client.get(OPERATORS_URL)
    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_create_operator_anonymous_returns_401(api_client):
    response = api_client.post(OPERATORS_URL, OPERATOR_PAYLOAD, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_operator_as_user_returns_403(user_client):
    response = user_client.post(OPERATORS_URL, OPERATOR_PAYLOAD, format="json")
    assert response.status_code == 403
    assert response.data["detail"] == "Ця дія доступна лише адміністраторам."
    assert TourOperator.objects.count() == 0


@pytest.mark.django_db
def test_create_operator_as_admin(staff_client):
    response = staff_client.post(OPERATORS_URL, OPERATOR_PAYLOAD, format="json")
    assert response.status_code == 201
    assert TourOperator.objects.filter(name="Mountain Trips").exists()


@pytest.mark.django_db
def test_delete_operator_with_tours_returns_409(staff_client, tour):
    response = staff_client.delete(f"{OPERATORS_URL}{tour.operator_id}/")
    assert response.status_code == 409
    assert TourOperator.objects.filter(id=tour.operator_id).exists()


@pytest.mark.django_db
def test_delete_destination_as_user_returns_403(user_client, destination):
    response = user_client.delete(f"/api/v1/destinations/{destination.id}/")
    assert response.status_code == 403
    assert Destination.objects.filter(id=destination.id).exists()


@pytest.mark.django_db
def test_delete_destination_without_tours_as_admin(staff_client, destination):
    response = staff_client.delete(f"/api/v1/destinations/{destination.id}/")
    assert response.status_code == 204
    assert not Destination.objects.filter(id=destination.id).exists()