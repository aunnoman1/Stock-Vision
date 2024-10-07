from django.shortcuts import render

def homepage_view(request):
    return render(request, 'home.html')

def stock_detail(request, symbol):
    # Dummy data for demonstration
    stock_data = {
        "symbol": symbol,
        "name": "Apple Inc." if symbol == "AAPL" else symbol,  # Example condition
        "predicted_price": "155.75"  # Placeholder predicted price
    }

    return render(request, 'onestockpage.html', {'stock': stock_data})