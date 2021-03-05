import time
from datetime import datetime
import csv
import os
import json
from concurrent import futures
import threading
import multiprocessing

import pandas as pd
from discord import Webhook, RequestsWebhookAdapter

from coin import Coin

"""
To-Do:
    -implement time cycle for work between the updates
    -between checks, which make sure that all the dfs got update correctly / logging
    -email notification on error
    -pre set the leverage and margin mode
"""

class Bot():

    @staticmethod
    def _read_config(path=None):
        """
        Function for reading in the config.json file
        """
        #create the filepath
        if path:
            if "config.json" in path:
                file_path = path
            else:
                file_path = f"{path}/config.json"
        else:
            file_path = "config.json"
        
        #load in config
        try:
            with open(file_path, "r") as json_file:
                config = json.load(json_file)
        except Exception:
            raise Exception("Your config file is corrupt (wrong syntax, missing values, ...)")

        #check for completeness
        if len(config["binance"]) != 4:
            raise Exception("Make sure your config file is complete, under section binance something seems to be wrong")
        
        if len(config["discord"]) != 4:
            raise Exception("Make sure your config file is complete, under section discord something seems to be wrong")

        return config

    def _setup(self):
        """
        Method for instantiating all the coin objects
        """
        start = time.time()

        with futures.ThreadPoolExecutor() as executor:
            results = [executor.submit(Coin.create, symbol, self.config) for symbol in self.config["binance"]["symbol_list"]]

        coin_dict = {}
        for result in results:
            coin_dict[result.result().symbol] = result.result()

        print(f"Setup Duration: {time.time()-start}")

        return coin_dict

    def __init__(self, config_path=None):
        """
        Arguments:
            -config_path[string]:   path to the config file, if there is no path specified, it is assumed that the config file and this python file are in the same directory
        """    
        #config dictionary
        self.config = self._read_config(path=config_path)
        #list of all symbol strings
        self.symbol_list = self.config["binance"]["symbol_list"]

        #setup of discord webhooks
        self.webhook = Webhook.partial(self.config["discord"]["webhook_id"], self.config["discord"]["webhook_token"], adapter=RequestsWebhookAdapter())
        self.prec_webhook = Webhook.partial(self.config["discord"]["prec_webhook_id"], self.config["discord"]["prec_webhook_token"], adapter=RequestsWebhookAdapter())

        #create the coin_dict, containing all the coin objects
        self.coin_dict = self._setup()

        #create a list that can be shared between processes
        self.unsuccessfull_updates = multiprocessing.Manager().list()

    def update(self):
        start = time.time()

        #csv file 
        csv_frame = []

        coin_list = [symbol for symbol in self.coin_dict.keys() if symbol not in self.unsuccessfull_updates]
        while coin_list:
            #list of successfully updated coins
            succesfull_coins = []

            #update the coins
            with futures.ThreadPoolExecutor() as executor:
                results = [executor.submit(self.coin_dict[symbol].update_data) for symbol in coin_list]
            
            #check for errors in updates
            for result in results:
                try:
                    #check if exception occured, while updating data
                    symbol = result.result()

                    #add to succesfull coins
                    succesfull_coins.append(symbol)

                    #delete coin from coinlist
                    coin_list.remove(symbol)
                except Exception as e:
                    pass

            #collect data on good coins and send discord notifications
            for symbol in succesfull_coins:
                #get values
                action = self.coin_dict[symbol].buy_signal_detection()
                trend_state = self.coin_dict[symbol].trend_state
                symbol_string = symbol
                url = self.coin_dict[symbol].url

                #append to frame
                csv_frame.append([symbol, trend_state, action, url])
                
                #send notification to discord
                if action in "Long" or action in "Short":
                    #create the message
                    message = f"{symbol_string}: {action} \n {url}"
                    #send message
                    self.webhook.send(message)
                elif action in "PrecLong" or action in "PrecShort":
                    #create the message
                    message = f"{symbol_string}: {action}"
                    #send message
                    self.prec_webhook.send(message)

            #check if timeout has been reached
            if time.time()-start > 60:
                #save the unsuccesfull coins
                self.unsuccessfull_updates += coin_list
                print("Unsuccesfull updates:", coin_list)
                break
        
        #write to csv
        df = pd.DataFrame(csv_frame)
        df.to_csv(path_or_buf="./live_data/actions.csv", header=False, index=False)
        
        #calculate update duration
        duration = time.time()-start

        print(f"Update took {duration} seconds")

        #write metadata to json file
        metadata = {
            "duration": duration
        }
        with open("./live_data/metadata.json", "w") as jsonfile:
            json.dump(metadata, jsonfile)

    def _timer(self):
        #incase the timer got called immediately after a 5 minute
        while datetime.now().minute % 5 == 0:
            pass
        while datetime.now().minute % 5 != 0:
            pass
    
    def _reinitalizer(self, unsuccessfull_updates):
        """
        Method for reinitializing coins that were unable to update
        """
        local_coin_dict = {}
        while self.unsuccessfull_updates:
            #reinitialize the coins
            with futures.ThreadPoolExecutor() as executor:
                results = [executor.submit(Coin.create, symbol, self.config) for symbol in self.unsuccessfull_updates]
            
            #check if they were initialized correctly
            for result in results:
                try:
                    coin = result.result()
                    #add to local_coin_dict
                    local_coin_dict[coin.symbol] = coin
                    #remove from unsuccessfull_updates
                    self.unsuccessfull_updates.remove(coin.symbol)
                
                except Exception:
                    time.sleep(1)
        
        return local_coin_dict

    def _bewtween_worker(self):
        """
        Function for work that needs to be done between updates
        """

    def run(self):
        while True:
            #wait for time to get to 5 minutes
            self._timer()
            #update the coins
            self.update()

            print(self.unsuccessfull_updates)



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
    bot = Bot()

    bot.run()