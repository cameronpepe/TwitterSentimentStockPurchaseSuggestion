# import got
# import sys
# import json
# def main():
#     tweetCriteria = got.manager.TweetCriteria().setQuerySearch('Nike').setSince("2013-11-20").setUntil("2013-11-21").setMaxTweets(100)
#     tweets = got.manager.TweetManager.getTweets(tweetCriteria)
#     for tweet in tweets:
#         # tweet = got.manager.TweetManager.getTweets(tweetCriteria)[i]
#         data = {
#             "text": tweet.text, 
#             "date": str(tweet.date)
#         }
#         print(json.dumps(data))
#         sys.stdout.flush()
    
# if __name__ == '__main__':
# 	main()

#!/usr/bin/python
import got
import sys
import json
import datetime
import time
from langdetect import detect_langs


date_format = "%Y-%m-%d"
bad_strings = ['http://', 'https://']

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True
       
       
def get_language(text):
    results = None
    try:
        results = detect_langs(text)
    except:
        return False
    print(results)
    result = results[0];
    result = str(results);
    # if(result[0:2] == 'en'):
    if ('en' in result):
        return True
    return False
 
def isGoodString(s):
    return isEnglish(s) and not any(bad in s for bad in bad_strings) and  s != "" and s != 'nan' and  get_language(s) 


def pullTweets(company, since, until):
    # tweetCriteria = got.manager.TweetCriteria().setQuerySearch('Nike').setSince("2018-11-18").setUntil("2018-11-19").setMaxTweets(100)
    tweetCriteria = got.manager.TweetCriteria().setQuerySearch(company).setSince(since).setUntil(until).setMaxTweets(300)
    tweets, numTweets = got.manager.TweetManager.getTweets(tweetCriteria)

    for tweet in tweets:
        text = tweet.text
        if isGoodString(text):
            data = {
                "text": text, 
                "timestamp": str(tweet.date)
            }
            
            print(json.dumps(data))
            sys.stdout.flush()

    
def main():
    ##company = sys.argv[1]
   ## days = int(sys.argv[2])
    print("I am Peter and this is a Test Case")
    get_language("I am Peter and this is a Test case")

    # today = datetime.date.today()
    
    # if days <= 0:
    #     pullTweets(company, today.isoformat(), today.isoformat())
    # else:
    #     since = today - datetime.timedelta(days=days)
    #     until = since + datetime.timedelta(days=1)
    
    #     while since < today:
    #         # time.sleep(10)
    #         pullTweets(company, since.isoformat(), until.isoformat())
    #         since = since + datetime.timedelta(days=1)
    #         until = until + datetime.timedelta(days=1)

    
if __name__ == '__main__': main()