from django.shortcuts import render
from django.shortcuts import  get_object_or_404
from .models import Stock
from django.http import JsonResponse
from django.utils import timezone

def homepage_view(request):
    return render(request, 'home.html')


def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, ticker=symbol)
    latest_price = stock.prices.order_by('-date').first()
    stock_prices = stock.prices.order_by('date')[:100]  # Sort by day in ascending order to start from the earliest
    
    if stock_prices.exists():
        min_price = min(price.low_price for price in stock_prices)
        max_price = max(price.high_price for price in stock_prices)
    else:
        min_price = max_price = None

    # Convert Decimal prices to float and collect data for chart
    chart_data = {
        'dates': [price.day.strftime('%Y-%m-%d') for price in stock_prices],
        'open_prices': [float(price.open) for price in stock_prices],
        'close_prices': [float(price.close) for price in stock_prices],
        'high_prices': [float(price.high) for price in stock_prices],
        'low_prices': [float(price.low) for price in stock_prices],
    }

    return render(request, 'stock_detail.html', {
        'stock_data': stock,
        'latest_price': latest_price,
        'stock_prices': stock_prices,
        'min_price': min_price,
        'max_price': max_price,
        'chart_data': chart_data,  # Pass directly as dictionary
    })

def search_stocks(request):
    query = request.GET.get('q', '')
    if query:
        stocks = Stock.objects.filter(name__icontains=query)[:100]
        results = [{'name': stock.name, 'ticker': stock.ticker} for stock in stocks]
    else:
        results = []
    
    return JsonResponse(results, safe=False)