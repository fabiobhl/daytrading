from coin import Coin
from utils import timer
import pandas as pd
import time
import csv
import os
import json

"""
Backend Setup
"""

symbol_list = ["ETHUSDT", "BTCUSDT", "LTCUSDT"]

#create objects
setup_start = time.time()
coin_dict = {}
for symbol in symbol_list:
    coin_dict[symbol] = Coin(symbol=symbol)
print(f"Setup Duration: {time.time()-setup_start}")

#main loop
while True:
    #wait for minutes to be a multiple of 5
    update = timer()

    complete_start = time.time()

    #delete the csv file
    try:
        os.remove("actions.csv")
        os.remove("metadata.json")
    except Exception:
        print(Exception)

    #update the coins
    if update == "betweenUpdate":
        update_start = time.time()
        for key in coin_dict:
            coin_dict[key].update_data_between()
        update_duration = time.time() - update_start

    elif update == "fullUpdate":
        update_start = time.time()
        for key in coin_dict:
            coin_dict[key].update_data_full()
        update_duration = time.time() - update_start
    
    #save the actions to csv
    for key in coin_dict:
        action = coin_dict[key].buy_signal_detection()
        trend_state = coin_dict[key].trend_state
        symbol = key
        with open('actions.csv', 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([symbol, trend_state, action])
    
    complete_duration = time.time()-complete_start

    #write metadata to json file
    metadata = {
        "complete_duration": complete_duration,
        "update_duration": update_duration
    }
    with open("metadata.json", "w") as jsonfile:
        json.dump(metadata, jsonfile)
