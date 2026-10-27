from rest_framework import serializers
from .models import TourOperator, Destination, Category, Tour


class TourOperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourOperator
        fields = ['id', 'name', 'description', 'email', 'phone']


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'name', 'country']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class TourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tour
        fields = ['id', 'title', 'description', 'price', 'duration_days',
                  'departure_date', 'seats_available',
                  'operator', 'destination', 'categories']