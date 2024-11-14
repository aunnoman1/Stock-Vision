from django.shortcuts import render, get_object_or_404
from .models import Stock
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

def homepage_view(request):
    return render(request, 'home.html')

def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, ticker=symbol)
    latest_price = stock.prices.order_by('-date').first()
    
    time_span = request.GET.get('time_span', '6m')

    if time_span == '1w':
        start_date = timezone.now() - timedelta(days=7)
    elif time_span == '1m':
        start_date = timezone.now() - timedelta(days=30)
    elif time_span == '3m':
        start_date = timezone.now() - timedelta(days=90)
    elif time_span == '6m':
        start_date = timezone.now() - timedelta(days=180)
    else:
        start_date = timezone.now() - timedelta(days=180)

    stock_prices = stock.prices.filter(date__gte=start_date).order_by('date')

    if stock_prices.exists():
        min_price = min(price.low for price in stock_prices)
        max_price = max(price.high for price in stock_prices)
    else:
        min_price = max_price = None

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
        'chart_data': chart_data,
        'time_span': time_span,  
    })

def search_stocks(request):
    query = request.GET.get('q', '')
    if query:
        stocks = Stock.objects.filter(name__icontains=query)[:100]
        results = [{'name': stock.name, 'ticker': stock.ticker} for stock in stocks]
    else:
        results = []
    
    return JsonResponse(results, safe=False)