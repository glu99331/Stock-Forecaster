# Developed by: Gordon Lu
# Goal: To predict when to buy and sell a stock

# Packages:
import Constants
import tweepy # To access Twitter API and search tweets
import datetime # To query tweets and generate predictions n days ago
import yfinance as yf
import ratelimit # When there are too many requests, this library will help reset the ratelimit
# From internet: For most stock trades, settlement occurs two business days after the day the order executes, or T+2 (trade date plus two days).
# so to predict, we need a 2-day prediction
class Stock_Pred():

    #  Constructor that will take a list of strings (stock tickers) and build predictions
    #  using said list.
    def __init__(self, portfolio, api_key, api_secret):
        self.portfolio = portfolio
        self.api_key = api_key
        self.api_secret = api_secret
        self.api = self.generate_api()
    def generate_api(self):
        auth = tweepy.OAuth1UserHandler(self.api_key, self.api_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        return api    
    @ratelimit.wrap(limit=180, every=15*60) # 180 reqs every 15 mins    
    def query_tweets_from_n_days(self, n):
        for stock_ticker in self.portfolio:
            if len(self.ticker_to_company_name(stock_ticker).split(" ")) > 1: 
                company = self.ticker_to_company_name(stock_ticker).split(" ")[0]
            else:
                company = self.ticker_to_company_name(stock_ticker)
            print(company)
            tweets = []
            n_days_ago = datetime.datetime.now() - datetime.timedelta(days=n)
            since_id = int(n_days_ago.timestamp())
            for tweet in tweepy.Cursor(self.api.search_tweets, q=company, since_id = since_id, count = 100).items():
                tweets.append(tweet)
            print(f'The number of tweets containing {company} is {len(tweets)}')
    def ticker_to_company_name(self, stock_ticker):
        msft = yf.Ticker(stock_ticker)
        company_name = msft.info['longName']
        
        return company_name


def main():
    api_key = Constants.API_KEY
    api_secret = Constants.API_KEY_SECRET
    stock_predictions = Stock_Pred(['AAPL', 'GME'], api_key, api_secret)
    stock_predictions.query_tweets_from_n_days(5)

if __name__ == "__main__":
    main()