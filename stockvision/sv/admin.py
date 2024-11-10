from django.contrib import admin
from .models import Request, Watchlist, Post, Stock, Price

# Register your models here.
admin.site.register(Request)
admin.site.register(Watchlist)
admin.site.register(Post)
admin.site.register(Stock)
admin.site.register(Price)
