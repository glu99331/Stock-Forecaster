# Developed by: Gordon Lu
# Goal: To predict when to buy and sell a stock

# Packages:
import Constants
import tweepy # To access Twitter API and search tweets
import datetime # To query tweets and generate predictions n days ago
import yfinance as yf
import ratelimit # When there are too many requests, this library will help reset the ratelimit
import re
# From internet: For most stock trades, settlement occurs two business days after the day the order executes, or T+2 (trade date plus two days).
# so to predict, we need a 2-day prediction
class Stock_Pred():

    #  Constructor that will take a list of strings (stock tickers) and build predictions
    #  using said list.
    def __init__(self, portfolio, api_map):
        self.portfolio = portfolio
        self.api_map = api_map
        self.apis = self.generate_api()
    
    def generate_api(self):
        apis = []
        for api_key, api_secret in self.api_map.items():
            auth = tweepy.OAuth1UserHandler(api_key, api_secret)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            apis.append(api)
        return apis 

    def query_tweets_from_n_days(self, n):
        for stock_ticker in self.portfolio:
            if len(self.ticker_to_company_name(stock_ticker).split(" ")) > 1: 
                company = self.ticker_to_company_name(stock_ticker).split(" ")[0]
            else:
                company = self.ticker_to_company_name(stock_ticker)
            print(company)
            tweets = []
            # Calculate the tweet ID corresponding to 5 days ago in UTC format
            n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=n)
            since_id = int(n_days_ago.timestamp())
            max_id = None
            print(n_days_ago, type(n_days_ago))
            # Use multiple API keys and the "burst" rate limiting strategy to avoid reaching the rate limit
            print("Starting search on Tweets")
            i = 0 # Use a round-robin approach to distribute the requests across the API keys
            while True:
                api = self.apis[i % len(self.apis)]
                i+=1
                # can limit the number of tweets
                for tweet in tweepy.Cursor(api.search_tweets, q=company, since_id = since_id, max_id = max_id, result_type = "recent").items():
                    tweets.append(tweet)
                    max_id = tweet.id
                    # Convert the created_at attribute from ISO 8601 with TZ to the UTC time zone before comparing
                    created_at = str(tweet.created_at)
                    created_at = datetime.datetime.strptime(created_at[:created_at.index("+")], '%Y-%m-%d %H:%M:%S')

                    if created_at < n_days_ago: break # If the tweet is older than 5 days, stop searching
                else:
                    print(f'The number of tweets containing {company} is {len(tweets)}') # If we reach the end of the tweets, stop searching
                    break
    def ticker_to_company_name(self, stock_ticker):
        msft = yf.Ticker(stock_ticker)
        company_name = msft.info['longName']
        
        return company_name


def main():
    api_map = {Constants.API_KEY1: Constants.API_KEY_SECRET1, Constants.API_KEY2: Constants.API_KEY_SECRET2, Constants.API_KEY3: Constants.API_KEY_SECRET3}
    stock_predictions = Stock_Pred(['AAPL', 'GME'], api_map)
    stock_predictions.query_tweets_from_n_days(5)

if __name__ == "__main__":
    main()