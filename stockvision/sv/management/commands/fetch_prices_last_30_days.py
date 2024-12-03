from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from sv.models import Stock, Price


class Command(BaseCommand):
    help = "Fetch last month's prices for stock tickers and save them to the database."

    def handle(self, *args, **options):
        start_date, end_date = self.get_date_range()
        stocks = Stock.objects.all()

        if not stocks.exists():
            self.stdout.write(self.style.WARNING("No stocks found in the database."))
            return

        for stock in stocks:
            self.process_stock(stock, start_date, end_date)

        self.stdout.write(self.style.SUCCESS("Finished fetching and saving stock prices."))

    def get_date_range(self):
        """Calculate the date range for the last month."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        return start_date, end_date

    def process_stock(self, stock, start_date, end_date):
        """Fetch and process data for a single stock."""
        ticker = stock.ticker
        self.stdout.write(f"Fetching data for {ticker}...")
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            self.save_prices(stock, data)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch data for {ticker}: {e}"))

    def save_prices(self, stock, data):
        """Save historical price data to the database."""
        for date, row in data.iterrows():
            try:
                price_data = self.extract_price_data(row)
                if price_data:
                    self.save_price(stock, date, price_data)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error saving price for {stock.ticker} on {date}: {e}"))

    def extract_price_data(self, row):
        """Extract price data from a row and handle missing values."""
        try:
            return {
                "open": float(row["Open"]) if not pd.isna(row["Open"]) else 0.0,
                "high": float(row["High"]) if not pd.isna(row["High"]) else 0.0,
                "low": float(row["Low"]) if not pd.isna(row["Low"]) else 0.0,
                "close": float(row["Close"]) if not pd.isna(row["Close"]) else 0.0,
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
            }
        except Exception:
            return None

    def save_price(self, stock, date, price_data):
        """Save a single price entry to the database."""
        _, created = Price.objects.get_or_create(
            stock=stock,
            date=date,
            defaults=price_data,
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Added price for {stock.ticker} on {date}."))
        else:
            self.stdout.write(f"Price for {stock.ticker} on {date} already exists.")
