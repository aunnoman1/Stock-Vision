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

@login_required
def homepage_view(request):
    # Render the homepage view (home.html)
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


def userwatchlist(request):
    # Get the user's watchlist (assuming one watchlist per user)
    # Fetch the first (or only) watchlist for the logged-in user
    watchlist = Watchlist.objects.filter(user=request.user).first()
    if watchlist:
        # If the user has a watchlist, pass the stock items to the template
        watchlist_stocks = watchlist.stocks.all()
    else:
        watchlist_stocks = []  # If no watchlist exists, return an empty list

    return render(request, 'watchlist.html', {
        'watchlist_stocks': watchlist_stocks,  # Pass the stocks in the watchlist
        'user': request.user
    })

def userdetails(request):
    # Render the user details page, passing the current user to the template
    return render(request, 'userdetails.html', {'user': request.user})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('homepage')  # Redirect logged-in users to homepage
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('homepage')  # Redirect to homepage after login
        else:
            messages.error(request, "Invalid email or password")
            return redirect('login')  # Stay on login page if credentials are incorrect
    
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

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
    # Log the user out
    logout(request)
    
    # Redirect the user to the login page after logging out
    return redirect('login')
