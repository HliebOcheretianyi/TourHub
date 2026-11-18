import logging

from drf_spectacular.utils import (
    OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrReadOnly, TourPermission
from .models import TourOperator, Destination, Category, Tour
from .serializers import (
    TourOperatorSerializer, DestinationSerializer, CategorySerializer, TourSerializer,
)

logger = logging.getLogger(__name__)


def not_found(text):
    logger.warning("Not found: %s", text)
    return Response({"detail": text}, status=status.HTTP_404_NOT_FOUND)


def conflict(text):
    logger.warning("Conflict: %s", text)
    return Response({"detail": text}, status=status.HTTP_409_CONFLICT)


def user_label(request):
    """Хто виконує дію: id користувача, без паролів і токенів."""
    return f"user_id={request.user.id}" if request.user.is_authenticated else "anonymous"


# ---------- Спільні описи відповідей для OpenAPI ----------

ErrorSerializer = inline_serializer(name="Error", fields={"detail": serializers.CharField()})

RESP_400 = OpenApiResponse(
    description="Некоректні дані: повідомлення для кожного поля",
    examples=[OpenApiExample(
        "Помилки валідації",
        value={"title": ["Це поле обов'язкове."], "price": ["Необхідне ціле число."]},
    )],
)
RESP_401 = OpenApiResponse(
    ErrorSerializer,
    description="Немає токена або він недійсний чи прострочений",
    examples=[OpenApiExample("Без токена", value={"detail": "Облікові дані не були надані."})],
)
RESP_403_DELETE = OpenApiResponse(
    ErrorSerializer,
    description="Користувач авторизований, але не є адміністратором",
    examples=[OpenApiExample("Не адмін", value={"detail": "Видаляти тури можуть лише адміністратори."})],
)
RESP_403_ADMIN = OpenApiResponse(
    ErrorSerializer,
    description="Користувач авторизований, але не є адміністратором",
    examples=[OpenApiExample("Не адмін", value={"detail": "Ця дія доступна лише адміністраторам."})],
)
RESP_404_TOUR = OpenApiResponse(
    ErrorSerializer,
    description="Тур з таким id не існує",
    examples=[OpenApiExample("Не знайдено", value={"detail": "Тур з id=999 не знайдено"})],
)

TOUR_EXAMPLE = OpenApiExample(
    "Тур",
    value={
        "title": "Тиждень у Єгипті: все включено",
        "description": "Перельот, готель 5*, харчування все включено, трансфер.",
        "price": 28500,
        "duration_days": 7,
        "departure_date": "2026-12-20T08:00:00Z",
        "seats_available": 12,
        "operator": 1,
        "destination": 1,
        "categories": [1],
    },
)


# ---------- Тури ----------

@extend_schema_view(
    get=extend_schema(
        operation_id="tours_list",
        summary="Список турів",
        description="Доступно всім, токен не потрібен.",
        responses={200: TourSerializer(many=True)},
        tags=["Тури"],
    ),
    post=extend_schema(
        operation_id="tours_create",
        summary="Створити тур",
        description="Лише для авторизованих користувачів (заголовок `Authorization: Bearer <access>`).",
        request=TourSerializer,
        responses={201: TourSerializer, 400: RESP_400, 401: RESP_401},
        examples=[TOUR_EXAMPLE],
        tags=["Тури"],
    ),
)
class TourList(APIView):
    permission_classes = [TourPermission]
    serializer_class = TourSerializer

    def get(self, request, format=None):
        tours = Tour.objects.all()
        logger.debug("Tours list requested, count=%s", tours.count())
        return Response(TourSerializer(tours, many=True).data)

    def post(self, request, format=None):
        serializer = TourSerializer(data=request.data)
        if serializer.is_valid():
            tour = serializer.save()
            logger.info("Tour created: id=%s by %s", tour.id, user_label(request))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(
            "Tour create rejected by validation, fields=%s, %s",
            list(serializer.errors.keys()), user_label(request),
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        operation_id="tours_retrieve",
        summary="Один тур",
        description="Доступно всім, токен не потрібен.",
        responses={200: TourSerializer, 404: RESP_404_TOUR},
        tags=["Тури"],
    ),
    put=extend_schema(
        operation_id="tours_update",
        summary="Оновити тур",
        description="Лише для авторизованих користувачів. Передається повний об'єкт туру.",
        request=TourSerializer,
        responses={200: TourSerializer, 400: RESP_400, 401: RESP_401, 404: RESP_404_TOUR},
        examples=[TOUR_EXAMPLE],
        tags=["Тури"],
    ),
    delete=extend_schema(
        operation_id="tours_destroy",
        summary="Видалити тур",
        description="Лише для адміністраторів (`is_staff`).",
        responses={204: OpenApiResponse(description="Тур видалено, тіла немає"),
                   401: RESP_401, 403: RESP_403_DELETE, 404: RESP_404_TOUR},
        tags=["Тури"],
    ),
)
class TourDetail(APIView):
    permission_classes = [TourPermission]
    serializer_class = TourSerializer

    def get_object(self, pk):
        try:
            return Tour.objects.get(pk=pk)
        except Tour.DoesNotExist:
            return None

    def get(self, request, pk, format=None):
        tour = self.get_object(pk)
        if tour is None:
            return not_found(f"Тур з id={pk} не знайдено")
        return Response(TourSerializer(tour).data)

    def put(self, request, pk, format=None):
        tour = self.get_object(pk)
        if tour is None:
            return not_found(f"Тур з id={pk} не знайдено")
        serializer = TourSerializer(tour, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Tour updated: id=%s by %s", tour.id, user_label(request))
            return Response(serializer.data)
        logger.warning(
            "Tour update rejected by validation: id=%s, fields=%s, %s",
            pk, list(serializer.errors.keys()), user_label(request),
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        tour = self.get_object(pk)
        if tour is None:
            return not_found(f"Тур з id={pk} не знайдено")
        tour.delete()
        logger.info("Tour deleted: id=%s by %s", pk, user_label(request))
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Напрямки ----------

@extend_schema_view(
    get=extend_schema(operation_id="destinations_list", summary="Список напрямків",
                      responses={200: DestinationSerializer(many=True)}, tags=["Напрямки"]),
    post=extend_schema(operation_id="destinations_create", summary="Створити напрямок (адмін)",
                       responses={201: DestinationSerializer, 400: RESP_400, 401: RESP_401, 403: RESP_403_ADMIN},
                       tags=["Напрямки"]),
)
class DestinationList(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DestinationSerializer

    def get(self, request, format=None):
        destinations = Destination.objects.all()
        serializer = DestinationSerializer(destinations, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = DestinationSerializer(data=request.data)
        if serializer.is_valid():
            destination = serializer.save()
            logger.info("Destination created: id=%s by %s", destination.id, user_label(request))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(summary="Один напрямок", tags=["Напрямки"]),
    put=extend_schema(summary="Оновити напрямок (адмін)", tags=["Напрямки"]),
    delete=extend_schema(summary="Видалити напрямок (адмін)", tags=["Напрямки"],
                         responses={204: None, 401: RESP_401, 403: RESP_403_ADMIN,
                                    404: ErrorSerializer, 409: ErrorSerializer}),
)
class DestinationDetail(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DestinationSerializer

    def get_object(self, pk):
        try:
            return Destination.objects.get(pk=pk)
        except Destination.DoesNotExist:
            return None

    def get(self, request, pk, format=None):
        destination = self.get_object(pk)
        if destination is None:
            return not_found(f"Напрямок з id={pk} не знайдено")
        return Response(DestinationSerializer(destination).data)

    def put(self, request, pk, format=None):
        destination = self.get_object(pk)
        if destination is None:
            return not_found(f"Напрямок з id={pk} не знайдено")
        serializer = DestinationSerializer(destination, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Destination updated: id=%s by %s", pk, user_label(request))
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        destination = self.get_object(pk)
        if destination is None:
            return not_found(f"Напрямок з id={pk} не знайдено")
        tours = Tour.objects.filter(destination=destination)
        if len(tours) > 0:
            return conflict(
                f"Неможливо видалити напрямок, оскільки до нього привʼязано турів: {len(tours)}. "
                f"Спочатку видаліть ці тури."
            )
        destination.delete()
        logger.info("Destination deleted: id=%s by %s", pk, user_label(request))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(summary="Тури в напрямок", responses={200: TourSerializer(many=True), 404: ErrorSerializer},
               tags=["Напрямки"])
class DestinationTours(APIView):
    serializer_class = TourSerializer

    def get(self, request, pk, format=None):
        destinations = Destination.objects.filter(pk=pk)
        if len(destinations) == 0:
            return not_found(f"Напрямок з id={pk} не знайдено")
        tours = Tour.objects.filter(destination=pk)
        return Response(TourSerializer(tours, many=True).data)


# ---------- Категорії ----------

@extend_schema(summary="Список категорій", responses={200: CategorySerializer(many=True)}, tags=["Категорії"])
@api_view(['GET'])
def category_list(request):
    categories = Category.objects.all()
    return Response(CategorySerializer(categories, many=True).data)


# ---------- Туроператори ----------

@extend_schema(summary="Тури туроператора", responses={200: TourSerializer(many=True), 404: ErrorSerializer},
               tags=["Туроператори"])
class OperatorTours(APIView):
    serializer_class = TourSerializer

    def get(self, request, pk, format=None):
        operators = TourOperator.objects.filter(pk=pk)
        if len(operators) == 0:
            return not_found(f"Туроператора з id={pk} не знайдено")
        tours = Tour.objects.filter(operator=pk)
        return Response(TourSerializer(tours, many=True).data)


@extend_schema_view(
    get=extend_schema(operation_id="operators_list", summary="Список туроператорів",
                      responses={200: TourOperatorSerializer(many=True)}, tags=["Туроператори"]),
    post=extend_schema(operation_id="operators_create", summary="Створити туроператора (адмін)",
                       responses={201: TourOperatorSerializer, 400: RESP_400, 401: RESP_401, 403: RESP_403_ADMIN},
                       tags=["Туроператори"]),
)
class OperatorList(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TourOperatorSerializer

    def get(self, request, format=None):
        operators = TourOperator.objects.all()
        serializer = TourOperatorSerializer(operators, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = TourOperatorSerializer(data=request.data)
        if serializer.is_valid():
            operator = serializer.save()
            logger.info("Operator created: id=%s by %s", operator.id, user_label(request))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(summary="Один туроператор", tags=["Туроператори"]),
    put=extend_schema(summary="Оновити туроператора (адмін)", tags=["Туроператори"]),
    delete=extend_schema(summary="Видалити туроператора (адмін)", tags=["Туроператори"],
                         responses={204: None, 401: RESP_401, 403: RESP_403_ADMIN,
                                    404: ErrorSerializer, 409: ErrorSerializer}),
)
class OperatorDetail(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TourOperatorSerializer

    def get_object(self, pk):
        try:
            return TourOperator.objects.get(pk=pk)
        except TourOperator.DoesNotExist:
            return None

    def get(self, request, pk, format=None):
        operator = self.get_object(pk)
        if operator is None:
            return not_found(f"Туроператора з id={pk} не знайдено")
        return Response(TourOperatorSerializer(operator).data)

    def put(self, request, pk, format=None):
        operator = self.get_object(pk)
        if operator is None:
            return not_found(f"Туроператора з id={pk} не знайдено")
        serializer = TourOperatorSerializer(operator, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Operator updated: id=%s by %s", pk, user_label(request))
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        operator = self.get_object(pk)
        if operator is None:
            return not_found(f"Туроператора з id={pk} не знайдено")
        tours = Tour.objects.filter(operator=operator)
        if len(tours) > 0:
            return conflict(
                f"Неможливо видалити туроператора, оскільки за ним закріплено турів: {len(tours)}. "
                f"Спочатку видаліть ці тури."
            )
        operator.delete()
        logger.info("Operator deleted: id=%s by %s", pk, user_label(request))
        return Response(status=status.HTTP_204_NO_CONTENT)