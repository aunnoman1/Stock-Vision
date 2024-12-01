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



def fetch_reddit_posts(subreddit, stocks, max_posts_per_stock=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    stock_posts = {stock: [] for stock in stocks}
    base_url = f"https://reddit.com/r/{subreddit}/search.json"
    
    # Calculate the timestamp for 30 days ago (from now)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    thirty_days_ago_timestamp = int(thirty_days_ago.timestamp())
    
    for stock in stocks:
        after = thirty_days_ago_timestamp 
        
        while max_posts_per_stock is None or len(stock_posts[stock]) < max_posts_per_stock:
            params = {
                'q': stock,          # Search for the stock keyword
                'sort': 'new',       # Sort by the newest posts
                'limit': 10000,        # Maximum allowed posts per request
                'restrict_sr': True, # Restrict to the subreddit
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
            if not posts:  # Exit if no more posts
                break
            
            for post in posts:
                post_data = post['data']
                title = post_data['title'].lower()
                author = post_data.get('author', 'N/A')
                created_utc = post_data.get('created_utc')
                created_time = datetime.utcfromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S') if created_utc else "N/A"

                
                if created_utc >= thirty_days_ago_timestamp:
                    stock_posts[stock].append({
                        'title': title,
                        'author': author,
                        'created_time': created_time,
                        'selftext': post_data['selftext'].lower() if 'selftext' in post_data else '',
                    })
                
              
                if max_posts_per_stock and len(stock_posts[stock]) >= max_posts_per_stock:
                    break
            
            # Update `after` for pagination
            after = posts[-1]['data']['created_utc']
            if after < thirty_days_ago_timestamp: 
                break
    
    return stock_posts



# Function to perform sentiment analysis on text
def analyze_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    result = sid.polarity_scores(text)
    return result

# Main function to fetch posts, analyze sentiment, and save to a DataFrame
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
                if Post.objects.filter(stock=stock_obj,text=post['title'] + '. ' + post['selftext']).exists():
                    print(f"Post already exists: {post['title']}")
                    continue
                sentiment = analyze_sentiment(post['title']+ '. ' + post['selftext'])
                
                # Append the post data to the all_posts list
                p=Post.objects.create(
                    stock= stock_obj,
                    author= post['author'],
                    time= post['created_time'],
                    sentiment= sentiment['compound'],
                    neg= sentiment['neg'],
                    neu= sentiment['neu'],
                    pos= sentiment['pos'],
                    text= post['title'] + '. ' + post['selftext']
                )
                p.save()
    


# Django command to execute the script
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        get_aggregated_stock_posts(SUBREDDITS, STOCKS, max_posts_per_stock=700)
