from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage_view, name='home'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('search_stocks/', views.search_stocks, name='search_stocks'),
]