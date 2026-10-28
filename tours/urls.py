from django.urls import path
from . import views

urlpatterns = [
    path('operators/', views.OperatorList.as_view()),
    path('operators/<int:pk>/', views.OperatorDetail.as_view()),
    path('operators/<int:pk>/tours/', views.OperatorTours.as_view()),
    path('destinations/', views.DestinationList.as_view()),
    path('destinations/<int:pk>/', views.DestinationDetail.as_view()),
    path('destinations/<int:pk>/tours/', views.DestinationTours.as_view()),
    path('categories/', views.category_list),
    path('tours/', views.TourList.as_view()),
    path('tours/<int:pk>/', views.TourDetail.as_view()),
]