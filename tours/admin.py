from django.contrib import admin
from .models import TourOperator, Destination, Category, Tour

admin.site.register(TourOperator)
admin.site.register(Destination)
admin.site.register(Category)
admin.site.register(Tour)