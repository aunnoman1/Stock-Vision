from django.shortcuts import render, get_object_or_404
from .models import Stock
from django.http import JsonResponse
from django.utils import timezone

def homepage_view(request):
    return render(request, 'home.html')

def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, ticker=symbol)
    latest_price = stock.prices.order_by('-date').first()  # Get the latest price
    stock_prices = stock.prices.order_by('date')[:100]  # Sort by date in ascending order (earliest first)
    
    # Calculate the min and max prices from the last 100 stock prices
    if stock_prices.exists():
        min_price = min(price.low for price in stock_prices)
        max_price = max(price.high for price in stock_prices)
    else:
        min_price = max_price = None

    # Prepare chart data
    chart_data = {
        'dates': [price.date.strftime('%Y-%m-%d') for price in stock_prices],
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
        'chart_data': chart_data,  # Pass chart data as a dictionary
    })

def search_stocks(request):
    query = request.GET.get('q', '')
    results = []
    
    if query:
        stocks = Stock.objects.filter(name__icontains=query)[:100]  # Limiting to 100 results
        results = [{'name': stock.name, 'ticker': stock.ticker} for stock in stocks]

    return JsonResponse(results, safe=False)
