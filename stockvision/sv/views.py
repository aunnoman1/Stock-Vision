
from django.shortcuts import render, get_object_or_404,get_list_or_404
from .models import Stock, Watchlist
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import  redirect,render
from django.contrib.auth import logout
from django.utils import timezone
from datetime import timedelta
from .models import Stock,Price
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django import forms
from .models import Request

import json

def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, ticker=symbol)
    latest_price = stock.prices.order_by('-date').first()
    
    # Handle time span for price data
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

    # Prepare chart data
    chart_data = {
        'dates': [price.date.strftime('%Y-%m-%d') for price in stock_prices],
        'open_prices': [float(price.open) for price in stock_prices],
        'close_prices': [float(price.close) for price in stock_prices],
        'high_prices': [float(price.high) for price in stock_prices],
        'low_prices': [float(price.low) for price in stock_prices],
    }
    chart_data_json = json.dumps(chart_data)

    # Retrieve the 5 most recent posts for the stock
    recent_posts = stock.posts.all().order_by('-time')[:5]

    return render(request, 'stock_detail.html', {
        'stock_data': stock,
        'latest_price': latest_price,
        'stock_prices': stock_prices,
        'min_price': min_price,
        'max_price': max_price,
        'chart_data_json': chart_data_json,
        'time_span': time_span,
        'recent_posts': recent_posts,
    })

def search_stocks(request):
    query = request.GET.get('query', '')
    
    if query:
        stocks = Stock.objects.filter(
            Q(name__icontains=query) | Q(ticker__icontains=query)
        )[:100]
    else:
        stocks = []

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        suggestions = [{'name': stock.name, 'ticker': stock.ticker} for stock in stocks]
        return JsonResponse(suggestions, safe=False)

    return render(request, 'search_results.html', {
        'query': query,
        'stocks': stocks,
    })

def userwatchlist(request):
    watchlist = Watchlist.objects.filter(user=request.user).first()
    if watchlist:
      
        watchlist_stocks = watchlist.stocks.all()
    else:
        watchlist_stocks = [] 

    return render(request, 'watchlist.html', {
        'watchlist_stocks': watchlist_stocks,  
        'user': request.user
    })

@login_required
def add_to_watchlist(request, stock_id):
    if request.method == "POST":
        stock = get_object_or_404(Stock, id=stock_id)
        watchlist, created = Watchlist.objects.get_or_create(user=request.user)
        if stock not in watchlist.stocks.all():
            watchlist.stocks.add(stock)
            return JsonResponse({"message": "Stock added to watchlist!", "status": "success"})
        return JsonResponse({"message": "Stock is already in the watchlist.", "status": "info"})
    return JsonResponse({"error": "Invalid request."}, status=400)

@login_required
def remove_from_watchlist(request, stock_id):
    try:
        stock = get_object_or_404(Stock, id=stock_id)
        watchlist = Watchlist.objects.filter(user=request.user).first()
        if not watchlist:
            return JsonResponse({"message": "No watchlist found.", "status": "error"}, status=404)
        if stock in watchlist.stocks.all():
            watchlist.stocks.remove(stock)
            return JsonResponse({"message": "Stock removed successfully.", "status": "success"})
        else:
            return JsonResponse({"message": "Stock not in watchlist.", "status": "info"})

    except Exception as e:
        return JsonResponse({"message": "An error occurred while removing the stock.", "status": "error"}, status=500)

def select_sector(request):
    sectors = Stock.objects.values_list('sector', flat=True).distinct()
    return render(request, 'select_sector.html', {'sectors': sectors})

def sector_stocks(request):
    selected_sector = request.GET.get('sector')
    stocks = Stock.objects.filter(sector=selected_sector)

    stocks_with_prices = []
    for stock in stocks:
        latest_price = Price.objects.filter(stock=stock).order_by('-date').first()
        stocks_with_prices.append({
            'stock': stock,
            'latest_price': latest_price,
        })

    return render(request, 'sector_stocks.html', {
        'sector': selected_sector,
        'stocks_with_prices': stocks_with_prices
    })
#--------------------------------

def homepage_view(request):
    latest_date = Price.objects.latest('date').date
    trending_stocks = Price.objects.filter(date=latest_date).order_by('-volume')[:5]
    context = {
        'trending_stocks': trending_stocks,
    }
    return render(request, 'home.html', context)

def userdetails(request):
    return render(request, 'userdetails.html', {'user': request.user})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('homepage')  
    
    if request.method == 'POST':
        email = request.POST.get('username')  
        password = request.POST.get('password')
   
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('homepage')  
        else:
            messages.error(request, "Invalid email or password") 
            return redirect('login')  
    
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')  
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        if password == confirm_password:
            if not User.objects.filter(username=email).exists():  
                user = User.objects.create_user(username=email, email=email, password=password)
                user.save()
                messages.success(request, "Account created successfully!")
                return redirect('login')
            else:
                messages.error(request, "Email is already in use.")
        else:
            messages.error(request, "Passwords do not match.")
    
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    
    return redirect('login')#donee

def compare_stocks(request):
    stock = get_object_or_404(Stock, ticker=request.GET.get('symbol'))
    compare_stock = get_object_or_404(Stock, ticker=request.GET.get('compare-symbol'))
    latest_price = stock.prices.order_by('-date').first()
    stock_prices = stock.prices.order_by('date')[:100]

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


    
    compare_latest_price = compare_stock.prices.order_by('-date').first()
    compare_stock_prices = compare_stock.prices.order_by('date')[:100]

    if compare_stock_prices.exists():
        compare_min_price = min(price.low for price in compare_stock_prices)
        compare_max_price = max(price.high for price in compare_stock_prices)

    compare_chart_data = {
        'dates': [price.date.strftime('%Y-%m-%d') for price in compare_stock_prices],
        'open_prices': [float(price.open) for price in compare_stock_prices],
        'close_prices': [float(price.close) for price in compare_stock_prices],
        'high_prices': [float(price.high) for price in compare_stock_prices],
        'low_prices': [float(price.low) for price in compare_stock_prices],
    }

    return render(request, 'compare_stocks.html', {
        'stock_data': stock,
        'latest_price': latest_price,
        'stock_prices': stock_prices,
        'min_price': min_price,
        'max_price': max_price,
        'chart_data': chart_data,

        'compare_stock_data': compare_stock,
        'compare_latest_price': compare_latest_price,
        'compare_stock_prices': compare_stock_prices,
        'compare_min_price': compare_min_price,
        'compare_max_price': compare_max_price,
        'compare_chart_data': compare_chart_data,
    })
def compare_selector(request):
    stocks = Stock.objects.all()

    return render(request, 'compare-selector.html', {
        'stocks': stocks,
    })

def request_stock(request):
    if request.method == 'POST':
        req_name = request.POST.get('req_name')
        ticker = request.POST.get('ticker')
        new_request = Request(req_name=req_name, ticker=ticker, user=request.user)
        new_request.save()
        messages.success(request, 'Your stock request has been submitted.')

        return redirect('request_stock')  
    
    return render(request, 'request_stock.html')