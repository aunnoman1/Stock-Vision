from django.contrib import admin
from .models import User, Request, Watchlist, Post, Stock, Price

admin.site.register(User)
admin.site.register(Request)
admin.site.register(Watchlist)
admin.site.register(Post)
admin.site.register(Stock)
admin.site.register(Price)
