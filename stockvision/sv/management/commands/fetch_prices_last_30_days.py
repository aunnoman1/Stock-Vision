import yfinance as yf
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from sv.models import Stock, Price  # Replace 'myapp' with the name of your app
import pandas as pd

class Command(BaseCommand):
    help = "Fetch last month's prices for stock tickers and save them to the database."

    def handle(self, *args, **options):
        # Calculate the date range for the last month
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        # Fetch all stock tickers from the Stock model
        stocks = Stock.objects.all()

        if not stocks.exists():
            self.stdout.write(self.style.WARNING("No stocks found in the database."))
            return

        for stock in stocks:
            ticker = stock.ticker
            self.stdout.write(f"Fetching data for {ticker}...")

            try:
                # Fetch historical data from Yahoo Finance
                data = yf.download(ticker, start=start_date, end=end_date)

                # Iterate through the data and save to the database
                for date, row in data.iterrows():
                    try:
                         # Access the specific numeric values in each row
                        open_price = row["Open"] if not pd.isna(row["Open"]).all() else 0.0
                        high_price = row["High"] if not pd.isna(row["High"]).all() else 0.0
                        low_price = row["Low"] if not pd.isna(row["Low"]).all() else 0.0
                        close_price = row["Close"] if not pd.isna(row["Close"]).all() else 0.0
                        volume = row["Volume"] if not pd.isna(row["Volume"]).all() else 0

                        # Convert values to appropriate types
                        open_price = float(open_price)
                        high_price = float(high_price)
                        low_price = float(low_price)
                        close_price = float(close_price)
                        volume = int(volume)

                        price, created = Price.objects.get_or_create(
                            stock=stock,
                            date=date,
                            defaults={
                                "open": open_price,
                                "high": high_price,
                                "low": low_price,
                                "close": close_price,
                                "volume": volume,
                            },
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Added price for {ticker} on {date}."))
                        else:
                            self.stdout.write(f"Price for {ticker} on {date} already exists.")
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error saving price for {ticker} on {date}: {e}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to fetch data for {ticker}: {e}"))

        self.stdout.write(self.style.SUCCESS("Finished fetching and saving stock prices."))
