import time
from datetime import datetime
import csv
import os
import json
from concurrent import futures
import threading

import pandas as pd
from discord import Webhook, RequestsWebhookAdapter

from coin import Coin

"""
To-Do:
    -between checks, which make sure that all the dfs got update correctly / logging
    -email notification on error
    -pre set the leverage and margin mode
"""


"""
Backend Setup
"""
#create objects
def setup(config):
    start = time.time()

    with futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(Coin.create, symbol, config) for symbol in config["binance"]["symbol_list"]]

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
    disc_not = {}
    disc_not_prec = {}

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

#read in config
def read_config():
    #load in config
    try:
        with open("config.json", "r") as json_file:
            config = json.load(json_file)
    except Exception:
        raise Exception("Your config file is corrupt (wrong syntax, missing values, ...)")

    #check for completeness
    if len(config["binance"]) != 4:
        raise Exception("Make sure your config file is complete, under section binance something seems to be wrong")
    
    if len(config["discord"]) != 4:
        raise Exception("Make sure your config file is complete, under section discord something seems to be wrong")

    return config

"""
Discord Setup
"""
def send(message_dict, prec_message_dict, config):
    #check if dictionary is empty
    if message_dict:
        #create the webhhok
        webhook = Webhook.partial(config["discord"]["webhook_id"], config["discord"]["webhook_token"], adapter=RequestsWebhookAdapter())
        
        #send all messages to trade-notifications
        for key in message_dict:
            #create the message
            message = f"{key}: {message_dict[key][0]}"
            for i in range(1, len(message_dict[key])):
                message += f"\n {message_dict[key][i]}"
            
            webhook.send(message)

    if prec_message_dict:
        #create the webhhook
        prec_webhook = Webhook.partial(config["discord"]["prec_webhook_id"], config["discord"]["prec_webhook_token"], adapter=RequestsWebhookAdapter())

        #send all messages to precon-notifications
        for key in prec_message_dict:
            #create the message
            message = f"{key}: {prec_message_dict[key][0]}"
            for i in range(1, len(prec_message_dict[key])):
                message += f"\n {prec_message_dict[key][i]}"
            
            prec_webhook.send(message)


"""
Main Function
"""
def main():
    #read in the config
    config = read_config()

    #create all coin objects
    coin_dict = setup(config=config)

    while True:
        #wait for time to get to 5 minutes
        update_var = timer()

        #update the coins
        disc_not, disc_not_prec = update(coin_dict=coin_dict, update_variable=update_var)

        #notify discord
        send(message_dict=disc_not, prec_message_dict=disc_not_prec, config=config)

        print(f"Finished update at: {datetime.now()}")

if __name__ == "__main__":
    main()