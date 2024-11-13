from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path("", views.homepage_view, name='home'),
    path('admin/', admin.site.urls),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('search_stocks/', views.search_stocks, name='search_stocks'),
]