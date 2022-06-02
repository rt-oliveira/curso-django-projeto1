from django.urls import path
from . import views

urlpatterns = [
    # /
    path('', views.home),
    # /recipe
    path('recipes/<int:id>/', views.recipe),
]