import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Avg
from sv.models import Stock, Price, Post  # Replace 'myapp' with the name of your app
import tensorflow as tf
import joblib
import yfinance as yf
from datetime import datetime
import os

class Command(BaseCommand):
    help = "Predict stock prices using AI model"

    def handle(self, *args, **options):
        # Load scaler and model
        scaler = joblib.load(os.path.join('..','..','models','avg_ratio_scaler.joblib'))
        model = tf.keras.models.load_model(os.path.join('..','..','models','avg_ratio_lstm_larger_model.keras'))
        
        # Process each stock
        for stock in Stock.objects.all():
            self.stdout.write(f"Processing {stock.ticker}")
            
            # Fetch the last 20 days of price data
            recent_prices = Price.objects.filter(stock=stock).order_by('-date')[:21]
            if len(recent_prices) < 20:
                self.stdout.write(f"Not enough price data for {stock.ticker}. Skipping.")
                continue

            # Prepare the price DataFrame
            price_data = pd.DataFrame.from_records(
                recent_prices.values('date', 'open', 'high', 'low', 'close', 'volume')
            ).sort_values('date')

            # Fetch sentiment data
            posts = Post.objects.filter(stock=stock).values('time', 'pos', 'neg', 'neu')
            sentiment_df = pd.DataFrame(posts)
            if sentiment_df.empty:
                self.stdout.write(f"No sentiment data for {stock.ticker}. Skipping.")
                continue

            sentiment_df['Date'] = pd.to_datetime(sentiment_df['time']).dt.date
            average_sentiments = sentiment_df.groupby('Date')[['pos', 'neg', 'neu']].mean().reset_index()
            average_sentiments.columns = ['Date', 'average_pos', 'average_neg', 'average_neu']

            # Merge price and sentiment data
            price_data['Date'] = pd.to_datetime(price_data['date']).dt.date
            merged_df = pd.merge(price_data, average_sentiments, on='Date', how='left')
            merged_df.fillna(0.333333, inplace=True)

            # Compute additional features
            merged_df['LogReturn_Close'] = np.log(merged_df['Close'] / merged_df['Close'].shift(1))
            merged_df['LogReturn_Volume'] = np.log(merged_df['Volume'] / merged_df['Volume'].shift(1))
            merged_df.dropna(inplace=True)
            feature_cols = [
                'LogReturn_Close', 'LogReturn_Volume',
                'average_pos', 'average_neg', 'average_neu'
            ]
            merged_df[feature_cols] = scaler.transform(merged_df[feature_cols])

            # Prepare input sequence
            X = np.array([merged_df[feature_cols].iloc[:20].values])
            if X.shape[1] < 20:
                self.stdout.write(f"Insufficient feature data for {stock.ticker}. Skipping.")
                continue

            # Predict
            predicted_log_return = model(X).numpy()[0][0]
            placeholder_data = np.zeros((1, len(feature_cols)))
            placeholder_data[0, feature_cols.index('LogReturn_Close')] = predicted_log_return
            inversed_data = scaler.inverse_transform(placeholder_data)
            inversed_y = inversed_data[0, feature_cols.index('LogReturn_Close')]
            predicted_price = float(price_20days['Close'].iloc[-1]) * np.exp(inversed_y)

            # Save the prediction to the database
            stock.prediction = round(predicted_price, 2)
            stock.save()

            self.stdout.write(f"Predicted price for {stock.ticker}: {predicted_price:.2f}")
