from django.core.management.base import BaseCommand
import os
import csv
from datetime import datetime
from django.db.utils import IntegrityError
from sv.models import Stock, Price

STOCK_SYMBOLS = [
            'NVDA', 'TSLA', 'AAPL', 'META', 'MSFT', 'AMZN', 'AMD',
            'AVGO', 'PLTR', 'MSTR', 'XOM', 'MU', 'JPM', 'GOOG',
            'CRM', 'LLY', 'VST', 'HD', 'NFLX', 'UNH', 'BAC', 
            'COST', 'SMCI', 'CVX', 'V', 'COIN'
        ]

DATA_FOLDER = os.path.join(os.path.dirname(__file__), '..\..\..\..\data')

class Command(BaseCommand):
    help = "Populate the database with stock prices from csv located in 'data' folder in root of project"

    def handle(self, *args, **kwargs):
        for ticker in STOCK_SYMBOLS:
            stock_file = os.path.join(DATA_FOLDER, f"{ticker}.csv")
            print(stock_file)
            # Check if the file exists
            if not os.path.exists(stock_file):
                print(f"File for {ticker} not found, skipping.")
                continue

            # Get the stock object
            try:
                stock = Stock.objects.get(ticker=ticker)
            except Stock.DoesNotExist:
                print(f"Stock with ticker {ticker} does not exist in the database, skipping.")
                continue

            # Read CSV and save data
            with open(stock_file, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                         # Use only the date part if there's time information
                        date_str = row['Date'].split(" ")[0]
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        # Create a new Price instance
                        price = Price(
                            stock=stock,
                            date=date,
                            open=row['Open'],
                            high=row['High'],
                            low=row['Low'],
                            close=row['Close'],
                            volume=row['Volume']
                        )

                        # Save the instance
                        price.save()
                        print(f"Saved data for {ticker} on {date}")

                    except IntegrityError:
                        print(f"Data for {ticker} on {date} already exists, skipping.")
                    except Exception as e:
                        print(f"Error saving data for {ticker} on {row['Date']}: {e}")
