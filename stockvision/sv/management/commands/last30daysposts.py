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
    while should_continue_fetching(stock_posts, stock, max_posts_per_stock):
        params = build_request_params(stock, after)
        response = fetch_reddit_data(base_url, headers, params)

        if not response:
            print(f"Error while fetching {stock} from {subreddit}")
            break

        posts = extract_posts_from_response(response)
        if not posts:
            break

        process_posts(posts, stock, stock_posts, max_posts_per_stock)

        after = response['data'].get('after')
        if not after:
            break


def build_request_params(stock, after):
    return {
        'q': stock,
        'sort': 'new',
        'limit': 700,
        'restrict_sr': True,
        'after': after
    }


def fetch_reddit_data(base_url, headers, params):
    try:
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}")
    except ValueError as e:
        print("Error parsing JSON:", e)
    return None


def extract_posts_from_response(data):
    if 'data' in data and 'children' in data['data']:
        return data['data']['children']
    return []


def process_posts(posts, stock, stock_posts, max_posts_per_stock):
    for post in posts:
        add_post_to_stock(post, stock, stock_posts)
        if max_posts_per_stock and len(stock_posts[stock]) >= max_posts_per_stock:
            break


def add_post_to_stock(post, stock, stock_posts):
    post_data = post['data']
    title = post_data['title'].lower()
    author = post_data.get('author', 'N/A')
    created_utc = post_data.get('created_utc')
    created_time = datetime.utcfromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S') if created_utc else "N/A"

    stock_posts[stock].add((title, author, created_time))


def should_continue_fetching(stock_posts, stock, max_posts_per_stock):
    return max_posts_per_stock is None or len(stock_posts[stock]) < max_posts_per_stock

# Function to perform sentiment analysis on text
from decimal import Decimal

# Function to perform sentiment analysis on text and return all components
def analyze_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    sentiment_scores = sid.polarity_scores(text)
    return sentiment_scores

# Main function to aggregate stock posts from multiple subreddits
from decimal import Decimal

def get_aggregated_stock_posts(subreddits, stocks, max_posts_per_stock=None):
    for subreddit in subreddits:
        print(f"Fetching posts from r/{subreddit}")
        stock_posts = fetch_reddit_posts(subreddit, stocks, max_posts_per_stock)
        
        for i, stock in enumerate(stocks):
            process_stock_posts(stock_posts, stock, i)


def process_stock_posts(stock_posts, stock, index):
    print(f"Processing stock: {TICKERS[index]}")
    stock_obj = get_stock_object(TICKERS[index])
    if not stock_obj:
        print(f"Stock {TICKERS[index]} not found in the database.")
        return

    for post in stock_posts[stock]:
        title, author, created_time = post
        sentiment_scores = analyze_sentiment(title)
        sentiment_data = extract_sentiment_scores(sentiment_scores)

        save_post(stock_obj, author, created_time, *sentiment_data, title)


def get_stock_object(ticker):
    try:
        return Stock.objects.get(ticker=ticker)
    except Stock.DoesNotExist:
        return None


def extract_sentiment_scores(sentiment_scores):
    sentiment = safe_decimal_conversion(sentiment_scores['compound'])
    pos_sentiment = safe_decimal_conversion(sentiment_scores['pos'])
    neg_sentiment = safe_decimal_conversion(sentiment_scores['neg'])
    neu_sentiment = safe_decimal_conversion(sentiment_scores['neu'])

    return sentiment, pos_sentiment, neg_sentiment, neu_sentiment


def safe_decimal_conversion(value):
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal(0.0)

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