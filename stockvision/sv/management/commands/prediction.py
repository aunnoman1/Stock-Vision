import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Avg
from sv.models import Stock, Price, Post
import tensorflow as tf
import joblib
import yfinance as yf
from datetime import datetime
import os

def categorize_sentiment(row):
    if row['pos'] > row['neg'] and row['pos'] > row['neu']:
        return 'positive'
    elif row['neg'] > row['pos'] and row['neg'] > row['neu']:
        return 'negative'
    else:
        return 'neutral'

class Command(BaseCommand):
    help = "Predict stock prices using AI model"

    def handle(self, *args, **options):
        # Load scaler and model
        scaler = joblib.load(os.path.join('sv','models','avg_ratio_scaler.joblib'))
        model = tf.keras.models.load_model(os.path.join('sv','models','avg_ratio_lstm_larger_model.keras'))
        
        # Process each stock
        for stock in Stock.objects.all():
            self.stdout.write(f"Processing {stock.ticker}")
            
            # Fetch the last 20 days of price data
            recent_prices = Price.objects.filter(stock=stock).order_by('-date')[:21]
            if len(recent_prices) < 21:
                print(len(recent_prices))
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
            
            aggregated_posts_df = sentiment_df.groupby("Date", as_index=False)[["pos", "neg", "neu"]].mean()
            
            average_sentiments = sentiment_df.groupby('Date')[['pos', 'neg', 'neu']].mean().reset_index()
            average_sentiments.columns = ['Date', 'average_pos', 'average_neg', 'average_neu']

            sentiment_df['sentiment_category'] = sentiment_df.apply(categorize_sentiment, axis=1)

            # Calculate daily sentiment ratios
            sentiment_ratios = (
                sentiment_df.groupby(['Date', 'sentiment_category'])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )
            if 'negative' not in sentiment_ratios.columns:
                sentiment_ratios['negative'] = 0
            if 'positive' not in sentiment_ratios.columns:
                sentiment_ratios['positive'] = 0

            sentiment_ratios['total_posts'] = sentiment_ratios[['positive', 'negative', 'neutral']].sum(axis=1)
            sentiment_ratios['positive_ratio'] = sentiment_ratios['positive'] / sentiment_ratios['total_posts']
            sentiment_ratios['negative_ratio'] = sentiment_ratios['negative'] / sentiment_ratios['total_posts']
            sentiment_ratios['neutral_ratio'] = sentiment_ratios['neutral'] / sentiment_ratios['total_posts']

            # Merge the average sentiments and sentiment ratios back into the original DataFrame
            combined_sentiments = pd.merge(average_sentiments, sentiment_ratios, on='Date', how='inner')


            combined_sentiments.drop(columns=['positive', 'negative', 'neutral', 'total_posts'], inplace=True)



            # Merge price and sentiment data
            price_data['Date'] = pd.to_datetime(price_data['date']).dt.date
            merged_df = pd.merge(price_data, combined_sentiments, on='Date', how='left')
            #print(merged_df.shape)
            merged_df.fillna(float(0.333333), inplace=True)

            #print(merged_df.info())
            merged_df['close'] = merged_df['close'].astype(float)
            # Compute additional features
            merged_df['LogReturn_Close'] = np.log(merged_df['close'] / merged_df['close'].shift(1))
            merged_df['LogReturn_Volume'] = np.log(merged_df['volume'] / merged_df['volume'].shift(1))
            merged_df.dropna(inplace=True)
            merged_df= merged_df.drop(columns=['close','volume','open','high','low'])

            feature_cols = [
                'LogReturn_Close', 'LogReturn_Volume', 
                'average_pos', 'average_neg', 'average_neu', 
                'positive_ratio', 'negative_ratio', 'neutral_ratio'
            ]
            merged_df[feature_cols] = scaler.transform(merged_df[feature_cols])

            # Prepare input sequence
            X = []
            group = merged_df.sort_values(by='Date').reset_index(drop=True)
            input_sequence = group[feature_cols].iloc[0: 20].values
            X.append(input_sequence)
            X = np.array(X)
            if X.shape[1] < 20:
                #print(X.shape)
                self.stdout.write(f"Insufficient feature data for {stock.ticker}. Skipping.")
                continue

            # Predict
            predicted_log_return = model(X).numpy()[0][0]
            placeholder_data = np.zeros((1, len(feature_cols)))
            placeholder_data[0, feature_cols.index('LogReturn_Close')] = predicted_log_return
            inversed_data = scaler.inverse_transform(placeholder_data)
            inversed_y = inversed_data[0, feature_cols.index('LogReturn_Close')]
            predicted_price = float(price_data['close'].iloc[-1]) * np.exp(inversed_y)

            # Save the prediction to the database
            stock.prediction = round(predicted_price, 2)
            stock.save()

            self.stdout.write(f"Predicted price for {stock.ticker}: {predicted_price:.2f}")
