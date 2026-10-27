from django.db import models


class TourOperator(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Destination(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name} ({self.country})'


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Tour(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    price = models.IntegerField()
    duration_days = models.IntegerField()
    departure_date = models.DateTimeField()
    seats_available = models.IntegerField()
    operator = models.ForeignKey(TourOperator, on_delete=models.CASCADE, related_name='tours')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='tours')
    categories = models.ManyToManyField(Category, related_name='tours')

    def __str__(self):
        return self.title