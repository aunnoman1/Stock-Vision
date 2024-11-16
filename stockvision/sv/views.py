
from django.shortcuts import render, get_object_or_404
from .models import Stock, Watchlist
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import  redirect
from django.contrib.auth import logout
from django.utils import timezone
from datetime import timedelta
from .models import Stock 
from django.db.models import Q

def homepage_view(request):
    return render(request, 'home.html')

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

    chart_data = {
        'dates': [price.date.strftime('%Y-%m-%d') for price in stock_prices],
        'open_prices': [float(price.open) for price in stock_prices],
        'close_prices': [float(price.close) for price in stock_prices],
        'high_prices': [float(price.high) for price in stock_prices],
        'low_prices': [float(price.low) for price in stock_prices],
    }

    # Retrieve the 5 most recent posts for the stock
    recent_posts = stock.posts.all().order_by('-time')[:5]

    return render(request, 'stock_detail.html', {
        'stock_data': stock,
        'latest_price': latest_price,
        'stock_prices': stock_prices,
        'min_price': min_price,
        'max_price': max_price,
        'chart_data': chart_data,
        'time_span': time_span,
        'recent_posts': recent_posts,  # Include recent posts in the context
    })

def search_stocks(request):
    query = request.GET.get('query', '')
    
    # Check if there's a query, then filter by name or ticker
    if query:
        stocks = Stock.objects.filter(
            Q(name__icontains=query) | Q(ticker__icontains=query)
        )[:100]
    else:
        stocks = []

    # Handle AJAX request for suggestions
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        suggestions = [{'name': stock.name, 'ticker': stock.ticker} for stock in stocks]
        return JsonResponse(suggestions, safe=False)

    # Render results for a normal request
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