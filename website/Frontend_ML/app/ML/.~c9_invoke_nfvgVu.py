import pandas as pd
import numpy as np
import csv, logging, sys
import os.path
import mysql.connector
import csv, math
from datetime import datetime, timedelta
from pytz import timezone
import predict
import pickle
import json
timeframe_days = {
    "long": {
        "tweet_days": 180
    },
    "mid": {
        "tweet_days": 30
    },
    "short": {
        "tweet_days": 7
    }
}

eastern = timezone('US/Eastern')

logging.basicConfig(level=logging.INFO)


def save_obj(obj, fn):
    # type = "stocks" or "tweets"
    # https://stackoverflow.com/a/19201448
    with open(fn, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(fn):
    with open(fn, 'rb') as f:
        return pickle.load(f)


def pull_rds_to_csv(company):
    today = datetime.now(eastern).date() - timedelta(days=1);
    today_str = today.isoformat();
    filename_tweets = "app/ML/predicting/raw/" + today_str[0:10] + "_"+ company + ".csv"
    
    if os.path.isfile(filename_tweets):
    #     # https://stackoverflow.com/a/82852
        logging.info("Found raw stocks and tweets data for " + company + " for " + today_str[0:10])
        return filename_tweets
    
    rds = mysql.connector.connect(
        host="twittersentiment.c8olx6nhxh4p.us-east-1.rds.amazonaws.com",
        user="cameronpepe",
        passwd="password",
        database="twitterSentiment",
        port="3306"
    )
    # Find the new date
    sixMonthsAgo = datetime.today() - timedelta(days=181);
    today_Date = datetime.today().isoformat();
    target_Date = sixMonthsAgo.isoformat();
    print(target_Date[0:10])
    print(today_Date[0:10])
    
    cur = rds.cursor()
    #tweets
    select_stmt = "SELECT date, positive, negative, neutral FROM tweetSentimentNew WHERE company=%(comp)s AND date >= '"+ target_Date[0:10] +"' AND date < '"+ today_Date[0:10] +"' ORDER BY date ASC" 
    cur.execute(select_stmt, {'comp': company})
    rows = cur.fetchall()
    fp = open(filename_tweets, "w")
    file = csv.writer(fp)
    headers = ["date", "positive", "negative", "neutral"]
    file.writerow(headers)
    file.writerows(rows)
    fp.close()
    logging.info("Stored raw stocks and tweets data for " + company)
    return filename_tweets

def get_twitter_days(company, fn_tweets):
    today = datetime.now(eastern).date() - timedelta(days=1);
    today_str = today.isoformat();
    print(today_str)
    dict_filename = "twitterDays_" + today_str[0:10] + company
    dict_filename_path = "app/ML/predicting/twitterDays/" + dict_filename + ".pkl"
    if os.path.isfile(dict_filename_path):
        logging.info("Found twitterDays for "+ company +" on "+ today_str[0:10])
        return load_obj(dict_filename_path)
    
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
    
    save_obj(twitterDays, dict_filename_path)
    logging.info("Stored raw twitterDays for " + company)
    # print(len(twitterDays.keys()))
    # keys = twitterDays.keys()
    # print(len(twitterDays[keys[0]]))
    return twitterDays
    

def format_training_and_testing_data(company, timeframe, twitterDays):
    today = datetime.now(eastern).date();
    today_str = today.isoformat();
    today_date = today_str[0:10]
    
    twitter_sorted_keys = sorted(twitterDays, key = lambda x:datetime.strptime(x, '%Y-%m-%d'))
    filename = "data_" + company + "_" + today_date
    filename_path = "app/ML/predicting/datapoints/" + filename + ".pkl"
    if os.path.isfile(filename_path):
        logging.info("Found data set for " + company + " for " + timeframe)
        return load_obj(filename_path),
    
    day = twitter_sorted_keys[0]
    # print(len(twitter_sorted_keys))
    data_point = []
    j = 0
    for j in range(180 - timeframe_days[timeframe]['tweet_days'], 180):
        data_point.append(twitterDays[twitter_sorted_keys[j]]['positive'])
        data_point.append(twitterDays[twitter_sorted_keys[j]]['negative'])
        data_point.append(twitterDays[twitter_sorted_keys[j]]['neutral'])
        
    # print(len(data_point))    

    save_obj(data_point, filename)
    logging.info("Stored data point for " + company + " for " + timeframe)
    return data_point

    
def get_suggestion(company):
    fn_tweets = pull_rds_to_csv(company)
    twitterDays = get_twitter_days(company, fn_tweets)
    long_datapoint = format_training_and_testing_data(company, "long", twitterDays)
    mid_datapoint = format_training_and_testing_data(company, "mid", twitterDays)
    short_datapoint = format_training_and_testing_data(company, "short", twitterDays)
    
    short_datapoint_arr = np.array( short_datapoint )
    print ('in suggestion')
    print(short_datapoint_arr.shape)
    
    
    long_response = predict.predict(long_datapoint, "Nike", "long")
    mid_response = predict.predict(mid_datapoint, "Nike", "mid")
    short_response = predict.predict(short_datapoint_arr, "Nike", "short")
    
    print (long_response[1][0][0])
    #print(mid_response)
    #print(short_response)
    
    test_response = {
        "long": {
            "prediction": str(long_response[0][0][0]),
            "confidence": str(long_response[1][0][0])
        },
        "mid": {
            "prediction": str(mid_response[0][0][0]),
            "confidence": str(mid_response[1][0][0])
        },
        "short": {
            "prediction": str(short_response[0][0][0]),
            "confidence": str(short_response[1][0][0])
        }
    }
    return json.dumps(test_response)
    
def main():    
    company = sys.argv[1]
    get_suggestion(company)
    
    
if __name__ == '__main__':
    main()
