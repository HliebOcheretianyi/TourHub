from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import TourOperator, Destination, Category, Tour
from .serializers import (
    TourOperatorSerializer, DestinationSerializer, CategorySerializer, TourSerializer,
)


def not_found(text):
    return Response({"detail": text}, status=status.HTTP_404_NOT_FOUND)


def conflict(text):
    return Response({"detail": text}, status=status.HTTP_409_CONFLICT)


class DestinationList(APIView):
    def get(self, request, format=None):
        destinations = Destination.objects.all()
        serializer = DestinationSerializer(destinations, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = DestinationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DestinationDetail(APIView):
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
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def category_list(request):
    categories = Category.objects.all()
    return Response(CategorySerializer(categories, many=True).data)


class TourList(APIView):
    def get(self, request, format=None):
        tours = Tour.objects.all()
        return Response(TourSerializer(tours, many=True).data)

    def post(self, request, format=None):
        serializer = TourSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TourDetail(APIView):
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
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        tour = self.get_object(pk)
        if tour is None:
            return not_found(f"Тур з id={pk} не знайдено")
        tour.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OperatorTours(APIView):
    def get(self, request, pk, format=None):
        operators = TourOperator.objects.filter(pk=pk)
        if len(operators) == 0:
            return not_found(f"Туроператора з id={pk} не знайдено")
        tours = Tour.objects.filter(operator=pk)
        return Response(TourSerializer(tours, many=True).data)


class DestinationTours(APIView):
    def get(self, request, pk, format=None):
        destinations = Destination.objects.filter(pk=pk)
        if len(destinations) == 0:
            return not_found(f"Напрямок з id={pk} не знайдено")
        tours = Tour.objects.filter(destination=pk)
        return Response(TourSerializer(tours, many=True).data)


class OperatorList(APIView):
    def get(self, request, format=None):
        operators = TourOperator.objects.all()
        serializer = TourOperatorSerializer(operators, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = TourOperatorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OperatorDetail(APIView):
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
        return Response(status=status.HTTP_204_NO_CONTENT)