import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
from keras.models import model_from_json
import pandas as pd
import numpy as np
import csv, logging, sys
import os.path


import predict
import data_handler

logging.basicConfig(level=logging.INFO)
SESSION = None


def create_model(num_nodes):
    logging.info("Building neural net with 2 hidden layers and " + str(num_nodes) + " perceptrons per layer...")
    model = Sequential()
    model.add(Dense(num_nodes, activation='relu'))
    model.add(Dense(num_nodes, activation='relu'))
    model.add(Dense(num_nodes, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer='sgd', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def xy_split(data):
    X = data.values[:, 1:] 
    y = data.values[:, 0]
    return X, y

def build(company, timeframe):
    logging.info("Getting testing and training data for " + company + " for " + timeframe + " term.")
    train_data, test_data = data_handler.get_training_data(company, timeframe)
    
    model_filename = "./models/model_" + company + "_" + timeframe + ".json"
    weight_filename = "./models/model_" + company + "_" + timeframe + ".h5"
    
    X, y = xy_split(train_data)
    model = create_model(X.shape[1])
    logging.info("Training model...")
    model.fit(X, y, epochs=100, verbose=0)
    
    logging.info("Serializing model for " + company + " for " + timeframe + "...")
    model_json = model.to_json()
    # model_filename = "./models/model_" + company + "_" + timeframe + ".json"
    # with open("./models/model.json", "w") as json_file:
    with open(model_filename, "w") as json_file:
        json_file.write(model_json)
    # weight_filename = "./models/model_" + company + "_" + timeframe + ".h5"
    # model.save_weights("./models/model.h5")
    model.save_weights(weight_filename)
    logging.info("Saved model for " + company + " for " + timeframe + " to disk.")
    return test_data
    
    
    
def test(test_data, company, timeframe):
    X_test, y_test = xy_split(test_data)
    logging.info("Predicting for " + company + " for " + timeframe + "...")
    y_pred = predict.predict(X_test, company, timeframe)[0]
    accuracy = np.mean((y_pred == y_test)) * 100
    print("Accuracy: ", accuracy)
    
def validate_params():
    if (len(sys.argv) != 3) or (sys.argv[2] not in ["long", "mid", "short"]):
        logging.error("Must call training script by: python train.py <company> <timeframe>")
        logging.error("<timeframe> must be long, mid, or short")
        exit(1)

def main():
    validate_params()
    company = sys.argv[1]
    timeframe = sys.argv[2]
    
    test_data = build(company, timeframe)
    test(test_data, company, timeframe)
    
if __name__ == '__main__':
    main()

