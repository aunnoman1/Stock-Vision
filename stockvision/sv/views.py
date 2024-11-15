
from django.shortcuts import render, get_object_or_404
from .models import Stock, Watchlist
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import  redirect
from django.contrib.auth import logout


def homepage_view(request):
    return render(request, 'home.html')

def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, ticker=symbol)
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

    return render(request, 'stock_detail.html', {
        'stock_data': stock,
        'latest_price': latest_price,
        'stock_prices': stock_prices,
        'min_price': min_price,
        'max_price': max_price,
        'chart_data': chart_data,
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
