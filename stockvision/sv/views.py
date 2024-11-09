from django.shortcuts import render
from .models import Price,Stock

def homepage_view(request):
    return render(request, 'home.html')

def stock_detail(request, symbol):
    # Retrieve stock data from the database
    stock_data = get_object_or_404(Stock, ticker=symbol)
    
    # Retrieve all historical prices for this stock
    stock_prices = Price.objects.filter(stock=stock_data).order_by('-day')
    
    # Get the most recent closing price as the current price if it exists
    current_price = stock_prices.first().close_price if stock_prices.exists() else None
    
    context = {
        'stock_data': stock_data,
        'stock_prices': stock_prices,
        'current_price': current_price,
    }
    
    return render(request, 'stock_detail.html', context)

def search_stock(request):
    query = request.GET.get('query')
    if query:
        # Filter stocks by name or ticker symbol containing the search query
        search_results = Stock.objects.filter(name__icontains=query) | Stock.objects.filter(ticker__icontains=query)

        # Attach latest price data for each stock
        for stock in search_results:
            latest_price = stock.prices.order_by('-day').first()
            stock.latest_price = latest_price  # Attach entire Price object if it exists
    else:
        search_results = None
    
    context = {
        'query': query,
        'search_results': search_results,
    }
    
    return render(request, 'search_results.html', context)