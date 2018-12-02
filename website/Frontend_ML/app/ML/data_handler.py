import pandas as pd
import numpy as np
import mysql.connector
import csv, math
from datetime import datetime
import os.path
import pickle
import logging

timeframe_days = {
    "long": {
        "tweet_days": 180,
        "stock_days": 60,
        "go_back": 200
    },
    "mid": {
        "tweet_days": 30,
        "stock_days": 7,
        "go_back": 75
    },
    "short": {
        "tweet_days": 7,
        "stock_days": 3,
        "go_back": 20
    }
}

logging.basicConfig(level=logging.INFO)

def save_obj(obj, name, type):
    # type = "stocks" or "tweets"
    # https://stackoverflow.com/a/19201448
    with open('training_data/'+ type + '/' + name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name, type):
    with open('training_data/'+ type + '/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

def pull_rds_to_csv(company):
    filename_stocks = "./training_data/stocks/raw_" + company + ".csv"
    filename_tweets = "./training_data/tweets/raw_" + company + ".csv"
    
    if os.path.isfile(filename_stocks) and os.path.isfile(filename_tweets):
        # https://stackoverflow.com/a/82852
        logging.info("Found raw stocks and tweets data for " + company)
        return filename_stocks, filename_tweets
    
    rds = mysql.connector.connect(
        host="",
        user="",
        passwd="",
        database="",
        port=""
    )
    cur = rds.cursor()
    # stock data
    select_stmt = "SELECT date, open, high, low, close, volume FROM stockData WHERE company=%(comp)s ORDER BY date ASC"
    cur.execute(select_stmt, {'comp': company})
    rows = cur.fetchall()
    fp = open(filename_stocks, "w")
    file = csv.writer(fp)
    headers = ["date", "open", "high", "low", "close", "volume"]
    file.writerow(headers)
    file.writerows(rows)
    fp.close()
    
    #tweets
    select_stmt = "SELECT date, positive, negative, neutral FROM tweetSentimentNew WHERE company=%(comp)s ORDER BY date ASC" 
    cur.execute(select_stmt, {'comp': company})
    rows = cur.fetchall()
    fp = open(filename_tweets, "w")
    file = csv.writer(fp)
    headers = ["date", "positive", "negative", "neutral"]
    file.writerow(headers)
    file.writerows(rows)
    fp.close()
    logging.info("Stored raw stocks and tweets data for " + company)
    return filename_stocks, filename_tweets

def get_twitter_days(company, fn_tweets):
    dict_filename = "twitterDays_" + company
    dict_filename_path = "./training_data/tweets/" + dict_filename + ".pkl"
    if os.path.isfile(dict_filename_path):
        logging.info("Found twitterDays for " + company)
        return load_obj(dict_filename, "tweets")
    
    twitterData = pd.read_csv(fn_tweets, index_col=0)
    twitterDays = {}
    count = 0
    for date, tweet in twitterData.iterrows():
        if date not in twitterDays:
            twitterDays[date] = {
                "dayCount": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }
        twitterDays[date]['dayCount'] += 1
        twitterDays[date]['positive'] += tweet.positive
        twitterDays[date]['negative'] += tweet.negative
        twitterDays[date]['neutral'] += tweet.neutral
    
    for day in twitterDays:
        ct = twitterDays[day]['dayCount']
        twitterDays[day]['positive'] /= ct
        twitterDays[day]['negative'] /= ct
        twitterDays[day]['neutral'] /= ct
    
    save_obj(twitterDays, dict_filename, "tweets")
    logging.info("Stored raw twitterDays for " + company)
    return twitterDays
        
def get_stock_diffs(company, fn_stocks, twitterDays):
    dict_filename = "stockDiffs_" + company
    dict_filename_path = "./training_data/stocks/" + dict_filename + ".pkl"

    stockDataDF = pd.read_csv(fn_stocks, index_col=0)
    stockData = stockDataDF.to_dict('index')
    stocks_sorted_keys = sorted(stockData, key = lambda x:datetime.strptime(x, '%Y-%m-%d'))
    twitter_sorted_keys = sorted(twitterDays, key = lambda x:datetime.strptime(x, '%Y-%m-%d'))
    
    if os.path.isfile(dict_filename_path):
        logging.info("Found stockDiffs for " + company)
        return load_obj(dict_filename, "stocks"), twitter_sorted_keys, stocks_sorted_keys
    
    stockDiffs = {}
    for i in range(1, len(stocks_sorted_keys)):
        prev_date = stocks_sorted_keys[i-1]
        date = stocks_sorted_keys[i]
        avged_price_date = ( stockData[date]['close'] + stockData[date]['high'] ) / 2
        avged_price_prev = ( stockData[prev_date]['close'] + stockData[prev_date]['high'] ) / 2
        delta_avged_percent = (avged_price_date - avged_price_prev) / avged_price_prev
        # delta_volume_percent = (stockData[date]['volume'] - stockData[prev_date]['volume']) / stockData[prev_date]['volume']
        stockDiffs[date] = {
            'price': delta_avged_percent
            # 'volume': delta_volume_percent
        }
    
    save_obj(stockDiffs, dict_filename, "stocks")
    logging.info("Stored stockDiffs for " + company)
    return stockDiffs, twitter_sorted_keys, stocks_sorted_keys

def test_train_split(twitter_train, timeframe):
    header = []
    header.append("quality_score")
    # for i in range(180):
    for i in range(timeframe_days[timeframe]["tweet_days"]):
        day = "day"+str(i)
        header.append(day+"pos")
        header.append(day+"neg")
        header.append(day+"neut")
    
    df = pd.DataFrame(data=twitter_train, columns=header)
    train_data, test_data = np.split(df.sample(frac=1), [int(0.8 * len(df))])
    logging.info("Data set shape: " + str(df.shape))
    logging.info("Training set shape: " + str(train_data.shape))
    logging.info("Testing set shape: " + str(test_data.shape))
    return train_data, test_data

def format_training_and_testing_data(company, timeframe, twitter_sorted_keys, stocks_sorted_keys, stockDiffs, twitterDays):
    filename = "data_" + company + "_" + timeframe
    filename_path = "./training_data/" + filename + ".pkl"
    if os.path.isfile(filename_path):
        logging.info("Found data set for " + company + " for " + timeframe)
        return test_train_split(load_obj(filename, ""), timeframe)
    
    twitter_train = []
    dayNum = 0
    i = 0
    day = twitter_sorted_keys[0]
    # last_ind = twitter_sorted_keys.index(stocks_sorted_keys[-200]) #hardcoded to -200 for now
    last_ind = twitter_sorted_keys.index(stocks_sorted_keys[timeframe_days[timeframe]['go_back'] * -1]) 
    while i < last_ind:
        data_point = []
        j = 0
        # while j < 180: # look 6 months back
        while j < timeframe_days[timeframe]['tweet_days']:
            data_point.append(twitterDays[twitter_sorted_keys[i+j]]['positive'])
            data_point.append(twitterDays[twitter_sorted_keys[i+j]]['negative'])
            data_point.append(twitterDays[twitter_sorted_keys[i+j]]['neutral'])
            j += 1
        stock_start_date = twitter_sorted_keys[i+j]
        while stock_start_date not in stocks_sorted_keys:
            j += 1
            stock_start_date = twitter_sorted_keys[i+j]
        stock_start_index = stocks_sorted_keys.index(stock_start_date)
        k = stock_start_index
        quality_score = 0
        # while k < (stock_start_index + 60): #60 trading days (3 months forward)
        while k < (stock_start_index + timeframe_days[timeframe]['stock_days']):
            date = stocks_sorted_keys[k]
            #sqrt function to prefer future days
            quality_score += math.sqrt(k - stock_start_index + 1) * stockDiffs[date]['price']           
            k += 1
        quality_score = 1 if quality_score > 0 else 0
        data_point.insert(0, quality_score)
        twitter_train.append(data_point)
        i += 1
    
    save_obj(twitter_train, filename, "")
    logging.info("Stored data set for " + company + " for " + timeframe)
    return test_train_split(twitter_train, timeframe)
    
def can_early_exit(company, timeframe):
    filename = "data_" + company + "_" + timeframe
    filename_path = "./training_data/" + filename + ".pkl"
    if os.path.isfile(filename_path):
        logging.info("Found data set for " + company + ". Can short-circuit data retrieval.")
        return True, filename
    return False, None
        
def get_training_data(company, timeframe):
    early_exit, filename = can_early_exit(company, timeframe)
    if early_exit:
        return test_train_split(load_obj(filename, ""), timeframe)
        
    fn_stocks, fn_tweets = pull_rds_to_csv(company)
    twitterDays = get_twitter_days(company, fn_tweets)
    stockDiffs, twitter_sorted_keys, stocks_sorted_keys = get_stock_diffs(company, fn_stocks, twitterDays)
    train_data, test_data = format_training_and_testing_data(company, timeframe, twitter_sorted_keys, stocks_sorted_keys, stockDiffs, twitterDays)
    return train_data, test_data