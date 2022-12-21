# Developed by: Gordon Lu
# Goal: To predict when to buy and sell a stock

# Packages:
import Constants
import tweepy # To access Twitter API and search tweets
import datetime # To query tweets and generate predictions n days ago
import yfinance as yf
import ratelimit # When there are too many requests, this library will help reset the ratelimit
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer # Among the tweets extracted, determine the percentage that are positive, negative, neutral
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
        self.sid_obj = SentimentIntensityAnalyzer()
        self.portfolio_sentiment_map = {}
    def generate_api(self):
        apis = []
        for api_key, api_secret in self.api_map.items():
            auth = tweepy.OAuth1UserHandler(api_key, api_secret)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            apis.append(api)
        return apis 

    def query_tweets_from_n_days(self, n):
        for stock_ticker in self.portfolio:
            polarity_map = {}
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
            query = " OR ".join([company, stock_ticker,self.ticker_to_company_name(stock_ticker)])
            print(query)
            regex = r'((?<!\w)@[\w+]{1,15}\b)'
            i = 0 # Use a round-robin approach to distribute the requests across the API keys
            while True:
                api = self.apis[i % len(self.apis)]
                i+=1
                # limit to 100 tweets
                for tweet in tweepy.Cursor(api.search_tweets, q=query, since_id = since_id, max_id = max_id, result_type = "recent").items(100):
                    tweets.append(tweet)
                    max_id = tweet.id
                    # Convert the created_at attribute from ISO 8601 with TZ to the UTC time zone before comparing
                    created_at = str(tweet.created_at)
                    created_at = datetime.datetime.strptime(created_at[:created_at.index("+")], '%Y-%m-%d %H:%M:%S')

                    if created_at < n_days_ago: break # If the tweet is older than 5 days, stop searching
                else:
                    tweet_text = [tweet.text for tweet in tweets]
                    for tweet in tweet_text:
                        skip_iter = False
                        matches = re.finditer(regex, tweet, re.MULTILINE)
                        for match in matches:
                            concat = '@' + company
                            concat2 = '@' + stock_ticker
                            #if twitter handle is like @AppleLUVR ignore, if it is @AAPLMUNCHR also ignore
                            if ((concat in match.groups() and match.groups() != concat) or (concat2 in match.groups() and match.groups() != concat2)):
                                skip_iter = True 
                                break
                        print(tweet)
                        if(skip_iter): continue
                        # Now construct polarity map: 
                        # Each company will have a corresponding map that will count the number of tweets that are positive, negative, neutral
                        # Example: {"Negative": 25, "Neutral": 50, "Positive": 25}
                        # We will then determine whether the company was positive, negative, or neutral based on which one, and the map will look like:
                        # {"Apple": "Negative", ...} 
                        polarity_scores = self.sid_obj.polarity_scores(tweet)
                        negative_score = polarity_scores['neg']*100
                        neutral_score = polarity_scores['neu']*100
                        positive_score = polarity_scores['pos']*100
                        # Add polarity scores into map:
                        if('negative' not in polarity_map): polarity_map['negative'] = 1
                        else: polarity_map['negative'] = polarity_map['negative'] + 1 
                        
                        if('neutral' not in polarity_map): polarity_map['neutral'] = 1
                        else: polarity_map['neutral'] = polarity_map['neutral'] + 1 
                        
                        if('positive' not in polarity_map): polarity_map['positive'] = 1
                        else: polarity_map['positive'] = polarity_map['positive'] + 1 
                    # Now classify company:
                    polarity_type, max_count = 0,0
                    for k,v in polarity_map.items():
                        if(max_count < v): polarity_type, max_count = k,v
                    if (polarity_type == "negative"): self.portfolio_sentiment_map[company] = "Negative"
                    elif(polarity_type == "neutral"): self.portfolio_sentiment_map[company] = "Neutral"
                    elif(polarity_type == "positive"): self.portfolio_sentiment_map[company] = "Positive"
                    print
                    print(f'The map looks like: {self.portfolio_sentiment_map} after adding {company}') # If we reach the end of the tweets, stop searching
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