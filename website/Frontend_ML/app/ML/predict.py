import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
from keras.models import model_from_json
import pandas as pd
import numpy as np
import csv
import logging
from keras import backend as K


logging.basicConfig(level=logging.INFO)

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

def load_model(company, timeframe):
    logging.info("Loading the stored model for " + company + " for " + timeframe + "...")
    model_filename = "app/ML/models/model_" + company + "_" + timeframe + ".json"
    # json_file = open("./models/model.json")
    json_file = open(model_filename)
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    weight_filename = "app/ML/models/model_" + company + "_" + timeframe + ".h5"
    print "***** WEIGHT NAME"
    print weight_filename
    # loaded_model.load_weights("./models/model.h5")
    loaded_model.load_weights(weight_filename)
    logging.info("Loaded model from disk for " + company + " for " + timeframe + ".")
    logging.info("Compiling " + company + " " + timeframe + " model...")
    
    loaded_model.compile(optimizer='SGD', loss='binary_crossentropy', metrics=['accuracy'])
    return loaded_model

def predict_class(X, company, timeframe):
    model = load_model(company, timeframe)
    y_pred = model.predict_classes(X)
    return y_pred

def predict_probabilities(X, company, timeframe):
    model = load_model(company, timeframe)
    y_pred_proba = model.predict_proba(X)
    return y_pred_proba
    
def predict(X, company, timeframe):
    K.clear_session()
    model = load_model(company, timeframe)
    # print ('in predict')
    # print(X.shape)
    # print(X)
    # X = np.reshape(X, (1,))
    X = np.reshape(X, (1, timeframe_days[timeframe]['tweet_days'] * 3))
    y_pred = model.predict_classes(X)
    y_pred_proba = model.predict_proba(X)
    logging.info("Returning tuple of [0] classification and [1] confidence in predictions.")
    return (y_pred, y_pred_proba)
    