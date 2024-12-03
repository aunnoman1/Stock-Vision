import json
import requests
from datetime import datetime
import nltk
from sv.models import Post, Stock
from django.core.management.base import BaseCommand
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Stock and subreddit configurations
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

# Function to fetch Reddit posts
def fetch_reddit_posts(subreddit, stocks, max_posts_per_stock=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = f"https://reddit.com/r/{subreddit}/search.json"
    stock_posts = {stock: set() for stock in stocks}  # Store unique posts per stock

    for stock in stocks:
        after = None
        while not max_posts_per_stock or len(stock_posts[stock]) < max_posts_per_stock:
            params = construct_params(stock, after)
            response = make_reddit_request(base_url, headers, params)

            if response is None:
                break

            data = response.json()
            posts = process_posts(data)
            stock_posts[stock].update(posts)

            after = data['data'].get('after')
            if not after:  # No more pages
                break

    return stock_posts

# Helper function to construct query parameters
def construct_params(stock, after):
    params = {
        'q': stock,
        'sort': 'new',
        'limit': 700,
        'restrict_sr': True,
        'after': after
    }
    return params

# Helper function to make the request to Reddit
def make_reddit_request(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error {response.status_code} while fetching data from Reddit")
        return None
    return response

# Process the posts retrieved from Reddit
def process_posts(data):
    posts = data['data'].get('children', [])
    stock_posts = []

    for post in posts:
        post_data = post['data']
        title = post_data['title'].lower()
        author = post_data.get('author', 'N/A')
        created_utc = post_data.get('created_utc')
        created_time = datetime.utcfromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S') if created_utc else "N/A"
        stock_posts.append((title, author, created_time))

    return stock_posts

# Function to perform sentiment analysis on text
def analyze_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    result = sid.polarity_scores(text)
    compound = result['compound']
    pos = result['pos']
    neg = result['neg']
    neu = result['neu']
    return compound, pos, neg, neu

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
                sentiment, pos, neg, neu = analyze_sentiment(title)
                save_post(stock_obj, author, created_time, sentiment, pos, neg, neu, title)

# Function to save the post in the database
def save_post(stock_obj, author, created_time, sentiment, pos, neg, neu, title):
    p = Post.objects.create(
        stock=stock_obj,
        author=author,
        time=created_time,
        sentiment=sentiment,
        pos=pos,
        neg=neg,
        neu=neu,
        text=title,
    )
    p.save()

# Django command to execute the script
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        get_aggregated_stock_posts(SUBREDDITS, STOCKS, max_posts_per_stock=700)
