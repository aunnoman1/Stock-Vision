from django.shortcuts import render
from django.shortcuts import  get_object_or_404
from .models import Stock
def homepage_view(request):
    return render(request, 'home.html')


def stock_detail(request, symbol):

    stock = get_object_or_404(Stock, ticker=symbol)
    

    latest_price = stock.prices.order_by('-day').first()

    return render(request, 'onestockpage.html', {
        'stock': stock,
        'latest_price': latest_price
    })

from django.http import JsonResponse

def search_stocks(request):
    query = request.GET.get('q', '')
    if query:
        stocks = Stock.objects.filter(name__icontains=query)[:10]
        results = [{'name': stock.name, 'ticker': stock.ticker} for stock in stocks]
    else:
        results = []
    
    return JsonResponse(results, safe=False)