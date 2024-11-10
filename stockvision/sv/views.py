from django.shortcuts import render
from django.shortcuts import  get_object_or_404
from .models import Stock
from django.http import JsonResponse

def homepage_view(request):
    return render(request, 'home.html')


def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, ticker=symbol)
    
    # Get the latest price entry for the stock
    latest_price = stock.prices.order_by('-day').first()
    
    # Get the last 100 prices, already ordered by day in descending order
    stock_prices = stock.prices.order_by('-day')[:100]
    
    # Calculate min and max prices without reordering the sliced queryset
    if stock_prices.exists():
        min_price = min(price.low_price for price in stock_prices)
        max_price = max(price.high_price for price in stock_prices)
    else:
        min_price = max_price = None

    return render(request, 'stock_detail.html', {
        'stock_data': stock,
        'latest_price': latest_price,
        'stock_prices': stock_prices,
        'min_price': min_price,
        'max_price': max_price,
    })

def search_stocks(request):
    query = request.GET.get('q', '')
    if query:
        stocks = Stock.objects.filter(name__icontains=query)[:100]
        results = [{'name': stock.name, 'ticker': stock.ticker} for stock in stocks]
    else:
        results = []
    
    return JsonResponse(results, safe=False)