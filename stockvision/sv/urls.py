from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage_view, name='home'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('search/', views.search_stock, name='search_stock'),
]