import json
import requests
from datetime import datetime, timedelta
import nltk
from sv.models import Post, Stock
from django.core.management.base import BaseCommand

nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer

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

# Function to fetch Reddit posts within the last 20 days
def fetch_reddit_posts(subreddit, stocks, max_posts_per_stock=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    stock_posts = {stock: [] for stock in stocks}
    base_url = f"https://reddit.com/r/{subreddit}/search.json"
    
    twenty_days_ago = datetime.utcnow() - timedelta(days=20)
    twenty_days_ago_timestamp = int(twenty_days_ago.timestamp())
    
    for stock in stocks:
        after = twenty_days_ago_timestamp  # Start fetching posts from 20 days ago
        
        while max_posts_per_stock is None or len(stock_posts[stock]) < max_posts_per_stock:
            params = {
                'q': stock,
                'sort': 'new',
                'limit': 100,
                'restrict_sr': True,
                'after': after
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
            
            for post in posts:
                post_data = post['data']
                title = post_data['title'].lower()
                content = post_data.get('selftext', '').lower()  # Fetch the content (selftext)
                author = post_data.get('author', 'N/A')
                created_utc = post_data.get('created_utc')

                if created_utc and created_utc >= twenty_days_ago_timestamp:
                    created_time = datetime.utcfromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S')
                    stock_posts[stock].append({
                        'title': title,
                        'content': content,
                        'author': author,
                        'created_time': created_time
                    })

                    if max_posts_per_stock and len(stock_posts[stock]) >= max_posts_per_stock:
                        break
            
            after = posts[-1]['data']['created_utc']
            if after < twenty_days_ago_timestamp:
                break
    
    return stock_posts

# Function to perform sentiment analysis on text
def analyze_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    result = sid.polarity_scores(text)
    return result['compound']

# Function to aggregate and save stock posts with sentiment analysis
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
                # Check if post already exists
                if Post.objects.filter(
                    stock=stock_obj,
                    text=post['title'],
                    author=post['author'],
                    time=post['created_time']
                ).exists():
                    print(f"Duplicate post found: {post['title']} - Skipping")
                    continue
                
                # Combine title and content for sentiment analysis
                combined_text = f"{post['title']} {post['content']}"
                sentiment = analyze_sentiment(combined_text)
                
                # Save the post
                p = Post.objects.create(
                    stock=stock_obj,
                    author=post['author'],
                    time=post['created_time'],
                    sentiment=sentiment,
                    title=post['title'],
                    content=post['content']  # Save content
                )
                p.save()

# Django command to execute the script
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        get_aggregated_stock_posts(SUBREDDITS, STOCKS, max_posts_per_stock=700)
