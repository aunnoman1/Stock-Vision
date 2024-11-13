from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path('', views.login_view, name='login'),
    path('homepage/', views.homepage_view, name='homepage'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('search_stocks/', views.search_stocks, name='search_stocks'),
    path('watchlist/', views.userwatchlist, name='userwatchlist'),
    path('user-details/', views.userdetails, name='userdetails'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
