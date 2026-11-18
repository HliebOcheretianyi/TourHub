import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from tours.models import Category, Destination, Tour, TourOperator

LOGIN_URL = "/api/v1/auth/login/"
PASSWORD = "Test-Pass-2026"


# ---------- Клієнти та користувачі ----------

@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(username="olena", email="olena@example.com", password=PASSWORD)


@pytest.fixture
def staff_user(db) -> User:
    return User.objects.create_user(
        username="admin", email="admin@example.com", password=PASSWORD, is_staff=True,
    )


def login(client: APIClient, username: str) -> APIClient:
    response = client.post(LOGIN_URL, {"username": username, "password": PASSWORD}, format="json")
    assert response.status_code == 200, response.data
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def user_client(user) -> APIClient:
    return login(APIClient(), user.username)


@pytest.fixture
def staff_client(staff_user) -> APIClient:
    return login(APIClient(), staff_user.username)


# ---------- Тестові дані ----------

@pytest.fixture
def operator(db) -> TourOperator:
    return TourOperator.objects.create(
        name="Sunny Travel", description="Пляжні тури", email="info@sunny.example", phone="+380441234567",
    )


@pytest.fixture
def destination(db) -> Destination:
    return Destination.objects.create(name="Хургада", country="Єгипет")


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(name="Пляжний відпочинок")


@pytest.fixture
def tour(operator, destination, category) -> Tour:
    tour = Tour.objects.create(
        title="Тиждень у Єгипті",
        description="Все включено",
        price=28500,
        duration_days=7,
        departure_date="2026-12-20T08:00:00Z",
        seats_available=12,
        operator=operator,
        destination=destination,
    )
    tour.categories.add(category)
    return tour


@pytest.fixture
def tour_payload(operator, destination, category) -> dict:
    return {
        "title": "Лижний тур у Буковелі",
        "description": "5 днів катання",
        "price": 12000,
        "duration_days": 5,
        "departure_date": "2027-01-10T07:00:00Z",
        "seats_available": 20,
        "operator": operator.id,
        "destination": destination.id,
        "categories": [category.id],
    }