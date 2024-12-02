from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage_view, name='homepage'),
    path('homepage/', views.homepage_view, name='homepage'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('search_stocks/', views.search_stocks, name='search_stocks'),
    path('compare-stocks/', views.compare_stocks, name='compare_stocks'),
    path('compare-selector/', views.compare_selector, name='compare_selector'),
    path('watchlist/', views.userwatchlist, name='userwatchlist'),
    path('user-details/', views.userdetails, name='userdetails'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('add_to_watchlist/<int:stock_id>/', views.add_to_watchlist, name='add_to_watchlist'),
    path('remove_from_watchlist/<int:stock_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('watchlist/remove/<int:stock_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('watchlist/stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
]