import requests
import time
from django.core.management.base import BaseCommand
from sv.models import Stock, Price
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetch stock prices from Alpha Vantage and store them in the database'

    def handle(self, *args, **kwargs):
        api_key = ' U3NSOB8CY8BITP3H' #my api P0GACQZ64BSA3V14 , Z6KWK2CDX37SX922
        base_url = "https://www.alphavantage.co/query"
        
        # Stocks to fetch prices for
        stocks_to_fetch = [
            'NVDA', 'TSLA', 'AAPL', 'META', 'MSFT', 'AMZN', 'AMD',
            'AVGO', 'PLTR', 'MSTR', 'XOM', 'MU', 'JPM', 'GOOG',
            'CRM', 'LLY', 'VST', 'HD', 'NFLX', 'UNH', 'BAC', 
            'COST', 'SMCI', 'CVX', 'V', 'COIN'
        ]

        for stock in stocks_to_fetch:
            response = requests.get(base_url, params={
                'function': 'TIME_SERIES_DAILY',
                'symbol': stock,  
                'apikey': api_key,
                'outputsize': 'compact'
            })

            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f'Raw data for {stock}: {data}')  # Log the raw data

                # Check for error in response
                if "Error Message" in data:
                    self.stdout.write(self.style.ERROR(f'Error fetching data for {stock}: {data.get("Error Message", "No error message provided.")}'))
                    continue

                time_series = data.get('Time Series (Daily)', {})
                
                # Check if time_series is empty
                if not time_series:
                    self.stdout.write(self.style.ERROR(f'No data returned for {stock}.'))
                    continue

                # Get prices for the last 25 days
                days = list(time_series.keys())[:210]

                # Fetch or create the Stock object
                stock_obj, created = Stock.objects.get_or_create(ticker=stock)

                for day in days:
                    price_data = time_series[day]
                    
                    try:
                        # Convert string to float safely
                        open_price = float(price_data.get('1. open', 0))
                        high_price = float(price_data.get('2. high', 0))
                        low_price = float(price_data.get('3. low', 0))
                        close_price = float(price_data.get('4. close', 0))
                        
                        # Convert day string to a date object
                        day_date = datetime.strptime(day, '%Y-%m-%d').date()

                        # Save the price data to the database
                        Price.objects.update_or_create(
                            stock=stock_obj,
                            day=day_date,
                            defaults={
                                'open_price': open_price,
                                'high_price': high_price,
                                'low_price': low_price,
                                'close_price': close_price
                            }
                        )
                        self.stdout.write(self.style.SUCCESS(f'Updated or created price for {stock} on {day_date}'))

                    except KeyError as ke:
                        self.stdout.write(self.style.ERROR(f'Missing expected key for {stock} on {day}: {ke}'))
                    except ValueError as ve:
                        self.stdout.write(self.style.ERROR(f'Error converting price data for {stock} on {day}: {ve}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error saving price for {stock} on {day}: {e}'))
                        # Log additional debug information
                        self.stdout.write(f'Debug data - Day: {day}, Stock: {stock}, Prices: {price_data}')
            
            else:
                self.stdout.write(self.style.ERROR(f'Failed to fetch prices for {stock}: {response.status_code}'))
            
            # Sleep to avoid hitting the API rate limit
            time.sleep(12)  # Alpha Vantage allows 5 requests per minute
