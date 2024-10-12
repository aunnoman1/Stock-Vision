from django.core.management.base import BaseCommand
import os
import django
import requests
import time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockvision.settings')  # Replace with your project's settings module
django.setup()

from sv.models import Stock  # Replace with your app name

# Alpha Vantage API configuration
API_KEY = 'Z6KWK2CDX37SX922'
BASE_URL = 'https://www.alphavantage.co/query'
STOCK_SYMBOLS = [
            'NVDA', 'TSLA', 'AAPL', 'META', 'MSFT', 'AMZN', 'AMD',
            'AVGO', 'PLTR', 'MSTR', 'XOM', 'MU', 'JPM', 'GOOG',
            'CRM', 'LLY', 'VST', 'HD', 'NFLX', 'UNH', 'BAC', 
            'COST', 'SMCI', 'CVX', 'V', 'COIN'
        ]

# Loop through each stock and populate database
for symbol in STOCK_SYMBOLS:
    params = {
        'function': 'OVERVIEW',
        'symbol': symbol,
        'apikey': API_KEY,
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()

        # Extract relevant fields from API response
        name = data.get('Name')
        ticker = data.get('Symbol')
        description = data.get('Description')
        sector = data.get('Sector')

        if name and ticker:
            # Save the stock data to your database
            stock, created = Stock.objects.get_or_create(
                ticker=ticker,
                defaults={
                    'name': name,
                    'description': description,
                    'sector': sector
                }
            )
            if created:
                print(f"Successfully added stock: {name}")
            else:
                print(f"Stock {name} already exists.")
    else:
        print(f"Failed to fetch data for {symbol}")

    # Delay to avoid hitting rate limits (assuming 5 requests per minute, so wait 12 seconds)
    time.sleep(12)