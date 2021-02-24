import discord
import asyncio
import time
from datetime import datetime
import csv
import os
import json
import pandas as pd
from coin import Coin
from concurrent import futures
import threading
import discord_cred
import discord_utilities

"""
To-Do:
    -between checks, which make sure that all the dfs got update correctly / logging
    -email notification on error
    -create configuration file
"""


"""
Backend Setup
"""
symbol_list = ["ETHUSDT", "BTCUSDT", "LTCUSDT", "UNIUSDT", "DOTUSDT", "ADAUSDT", "BNBUSDT", "LINKUSDT", "AAVEUSDT", "YFIUSDT",
                "BCHUSDT", "EOSUSDT", "SOLUSDT", "XLMUSDT", "SXPUSDT", "SUSHIUSDT", "TRXUSDT", "IOSTUSDT", "SRMUSDT", "FTMUSDT",
                "ATOMUSDT", "ETCUSDT", "DOGEUSDT", "GRTUSDT", "XTZUSDT", "KSMUSDT", "1INCHUSDT", "AVAXUSDT", "VETUSDT", "FILUSDT"]

#create objects
def setup(symbols):
    start = time.time()
    
    with futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(Coin.create, symbol) for symbol in symbols]

    coin_dict = {}
    for result in results:
        coin_dict[result.result().symbol] = result.result()

    print(f"Setup Duration: {time.time()-start}")

    return coin_dict

#update the coins
def update(coin_dict, update_variable):
    start = time.time()

    #update the coins
    if update_variable == "betweenUpdate":
        update_start = time.time()

        #create threads
        threads = []
        for symbol in coin_dict:
            thread = threading.Thread(target=coin_dict[symbol].update_data_between)
            thread.start()
            threads.append(thread)

        #wait for threads to finish
        for thread in threads:
            thread.join()

        update_duration = time.time() - update_start

    elif update_variable == "fullUpdate":
        update_start = time.time()

        #create threads
        threads = []
        for symbol in coin_dict:
            thread = threading.Thread(target=coin_dict[symbol].update_data_full)
            thread.start()
            threads.append(thread)

        #wait for threads to finish
        for thread in threads:
            thread.join()
        
        update_duration = time.time() - update_start
    
    #discord notfifications dict
    disc_not_prec = {}
    disc_not = {}

    #save the actions to csv
    csv_frame = []
    for key in coin_dict:
        #get values
        action = coin_dict[key].buy_signal_detection()
        trend_state = coin_dict[key].trend_state
        symbol = key
        url = coin_dict[key].url

        #append to frame
        csv_frame.append([symbol, trend_state, action, url])
        
        #fill notification dict
        if action in "Long" or action in "Short":
            disc_not[symbol] = [action, url]
        elif action in "PrecLong" or action in "PrecShort":
            disc_not_prec[symbol] = [action]
    
    #write to csv
    df = pd.DataFrame(csv_frame)
    df.to_csv(path_or_buf="./live_data/actions.csv", header=False, index=False)
    
    duration = time.time()-start

    #write metadata to json file
    metadata = {
        "complete_duration": duration,
        "update_duration": update_duration
    }
    with open("./live_data/metadata.json", "w") as jsonfile:
        json.dump(metadata, jsonfile)
    
    return disc_not, disc_not_prec

#timer
def timer():
    #incase the timer got called immediately after a 5 minute
    while datetime.now().minute % 5 == 0:
        pass
    while datetime.now().minute % 5 != 0:
        pass

    if datetime.now().minute == 0:
        return "fullUpdate"
    else:
        return "betweenUpdate"

"""
Main Function
"""
def main(symbol_list):
    #create all coin objects
    coin_dict = setup(symbols=symbol_list)

    while True:
        #wait for time to get to 5 minutes
        update_var = timer()

        #update the coins
        disc_not, disc_not_prec = update(coin_dict=coin_dict, update_variable=update_var)

        #notify discord
        discord_utilities.send(message_dict=disc_not, token=discord_cred.token, channel_id=discord_cred.channel_id)
        discord_utilities.send(message_dict=disc_not_prec, token=discord_cred.token, channel_id=discord_cred.prec_channel_id)

        print(f"Finished update at: {datetime.now()}")

if __name__ == "__main__":
    main(symbol_list)