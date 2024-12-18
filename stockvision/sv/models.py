from django.db import models
from django.contrib.auth.models import User

class Request(models.Model):
    req_name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requests")

    def __str__(self):
        return f"{self.req_name} ({self.ticker})"
    
class Stock(models.Model):
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    sector = models.CharField(max_length=100)
    prediction = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  

    def __str__(self):
        return f"{self.name} ({self.ticker})"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlists")
    stocks = models.ManyToManyField(Stock, related_name="watchlists")

    def __str__(self):
        return f"{self.user.username}'s Watchlist - {self.stock_ticker}"

class Post(models.Model):
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE, related_name="posts")
    author = models.CharField(max_length=100) 
    time = models.DateTimeField(auto_now_add=True)
    sentiment = models.DecimalField(max_digits=10, decimal_places=2) 
    pos= models.DecimalField(max_digits=10, decimal_places=2)
    neg= models.DecimalField(max_digits=10, decimal_places=2)
    neu= models.DecimalField(max_digits=10, decimal_places=2)
    text = models.TextField()

    def __str__(self):
        return f"Post by {self.author} at {self.time}"



    
class Price(models.Model):
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE, related_name="prices")
    date = models.DateField()  
    open = models.DecimalField(max_digits=14, decimal_places=4, default=0.00)
    high = models.DecimalField(max_digits=14, decimal_places=4, default=0.00)
    low = models.DecimalField(max_digits=14, decimal_places=4, default=0.00)
    close = models.DecimalField(max_digits=14, decimal_places=4, default=0.00)
    volume = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ('stock', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.stock.ticker} - {self.date}: Open: ${self.open}, Close: ${self.close}"