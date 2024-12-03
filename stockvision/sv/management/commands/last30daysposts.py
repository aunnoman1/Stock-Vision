import json
import requests
from datetime import datetime, timedelta
import nltk
from sv.models import Post, Stock
from django.core.management.base import BaseCommand
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download NLTK resources
nltk.download('vader_lexicon')

# Constants
STOCKS = [
    'nvidia', 'tesla', 'apple', 'facebook', 'microsoft', 'amazon', 'amd',
    'broadcom', 'palantir', 'microstrategy', 'exxon', 'micron', 'jpmorgan', 'google',
    'salesforce', 'lilly', 'vistra', 'home depot', 'netflix', 'unitedhealth',
    'bank of america', 'costco', 'super micro', 'chevron', 'visa', 'coinbase'
]

TICKERS = [
    'NVDA', 'TSLA', 'AAPL', 'META', 'MSFT', 'AMZN', 'AMD',
    'AVGO', 'PLTR', 'MSTR', 'XOM', 'MU', 'JPM', 'GOOG',
    'CRM', 'LLY', 'VST', 'HD', 'NFLX', 'UNH', 'BAC',
    'COST', 'SMCI', 'CVX', 'V', 'COIN'
]

SUBREDDITS = ['Investing', 'Stocks', 'WallStreetBets', 'Options', 'GlobalMarkets']

# Function to calculate 30 days ago using a more maintainable approach
def get_thirty_days_ago():
    return datetime.now() - timedelta(days=30)

# Refactored function to fetch Reddit posts
def fetch_reddit_posts(subreddit, stocks, max_posts_per_stock=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    stock_posts = {stock: set() for stock in stocks}  # Use set to store unique posts
    base_url = f"https://reddit.com/r/{subreddit}/search.json"

    # Fetch posts for each stock
    for stock in stocks:
        fetch_posts_for_stock(stock, base_url, headers, stock_posts, subreddit, max_posts_per_stock)

    return stock_posts

def fetch_posts_for_stock(stock, base_url, headers, stock_posts, subreddit, max_posts_per_stock):
    after = None
    while max_posts_per_stock is None or len(stock_posts[stock]) < max_posts_per_stock:
        params = {
            'q': stock,  # Search for the stock keyword
            'sort': 'new',  # Sort by the newest posts
            'limit': 700,  # Maximum allowed posts per request
            'restrict_sr': True,  # Restrict to the subreddit
            'after': after  # Pagination parameter
        }

        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error {response.status_code} while fetching {stock} from {subreddit}")
            break

        try:
            data = response.json()
        except ValueError as e:
            print("Error parsing JSON:", e)
            break

        if 'data' not in data or 'children' not in data['data']:
            break

        posts = data['data']['children']
        if not posts:  
            break

        # Process each post and add to stock posts
        for post in posts:
            post_data = post['data']
            title = post_data['title'].lower()
            author = post_data.get('author', 'N/A')
            created_utc = post_data.get('created_utc')
            created_time = datetime.utcfromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S') if created_utc else "N/A"

            stock_posts[stock].add((title, author, created_time))

            if max_posts_per_stock and len(stock_posts[stock]) >= max_posts_per_stock:
                break

        # Update `after` for pagination
        after = data['data'].get('after')
        if not after:
            break

# Function to perform sentiment analysis on text
from decimal import Decimal

# Function to perform sentiment analysis on text and return all components
def analyze_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    sentiment_scores = sid.polarity_scores(text)
    return sentiment_scores

# Main function to aggregate stock posts from multiple subreddits
def get_aggregated_stock_posts(subreddits, stocks, max_posts_per_stock=None):
    for subreddit in subreddits:
        print(f"Fetching posts from r/{subreddit}")
        stock_posts = fetch_reddit_posts(subreddit, stocks, max_posts_per_stock)
        
        for i, stock in enumerate(stocks):
            print(f"Processing stock: {TICKERS[i]}")
            try:
                stock_obj = Stock.objects.get(ticker=TICKERS[i])
            except Stock.DoesNotExist:
                print(f"Stock {TICKERS[i]} not found in the database.")
                continue

            for post in stock_posts[stock]:
                title, author, created_time = post
                sentiment_scores = analyze_sentiment(title)
                
                # Ensure we get valid Decimal values for the fields
                sentiment = Decimal(str(sentiment_scores['compound']))  # Compound sentiment score
                pos_sentiment = Decimal(str(sentiment_scores['pos']))  # Positive sentiment score
                neg_sentiment = Decimal(str(sentiment_scores['neg']))  # Negative sentiment score
                neu_sentiment = Decimal(str(sentiment_scores['neu']))  # Neutral sentiment score
                
                # Check if the values are valid (in case of any issues with the analysis)
                if not isinstance(sentiment, Decimal):
                    sentiment = Decimal(0.0)
                if not isinstance(pos_sentiment, Decimal):
                    pos_sentiment = Decimal(0.0)
                if not isinstance(neg_sentiment, Decimal):
                    neg_sentiment = Decimal(0.0)
                if not isinstance(neu_sentiment, Decimal):
                    neu_sentiment = Decimal(0.0)
                
                save_post(stock_obj, author, created_time, sentiment, pos_sentiment, neg_sentiment, neu_sentiment, title)

# Function to save the post in the database, including the sentiment fields
def save_post(stock_obj, author, created_time, sentiment, pos_sentiment, neg_sentiment, neu_sentiment, title):
    p = Post.objects.create(
        stock=stock_obj,
        author=author,
        time=created_time,
        sentiment=sentiment,
        pos=pos_sentiment,
        neg=neg_sentiment,
        neu=neu_sentiment,
        text=title,
    )
    p.save()
# Django command to execute the script
class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        get_aggregated_stock_posts(SUBREDDITS, STOCKS, max_posts_per_stock=1000)
