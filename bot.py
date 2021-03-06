import time
from datetime import datetime
import csv
import os
import json
from concurrent import futures
import threading
import multiprocessing
import math

import pandas as pd
from discord import Webhook, RequestsWebhookAdapter

from coin import Coin

"""
To-Do:
    -between checks, which make sure that all the dfs got update correctly
    -email notification on error
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

        for result in results:
            self.coin_dict[result.result().symbol] = result.result()

        print(f"Setup Duration: {time.time()-start}")

    def __init__(self, config_path=None, logging=False):
        """
        Arguments:
            -config_path[string]:   path to the config file, if there is no path specified, it is assumed that the config file and this python file are in the same directory
        """    
        #config dictionary
        self.config = self._read_config(path=config_path)
        #list of all symbol strings
        self.symbol_list = self.config["binance"]["symbol_list"]

        #setup the coin_dict
        self.coin_dict = {}
        self._setup()

        """
        #create a list that can be shared between processes
        self.manager = multiprocessing.Manager()
        self.unsuccessfull_updates = self.manager.list()
        """
        self.unsuccessfull_updates = []

        """
        Setup Logging
        """
        self.logging = logging
        if logging:
            #create new folder for logging
            self.log_path = f"./logs/{datetime.now().strftime('%d-%m-%y=%H-%M-%S')}"
            os.makedirs(self.log_path)
            
            #create architecture in folder
            os.makedirs(f"{self.log_path}/coins")

        """
        Setup App.py
        """
        if not os.path.exists("./live_data"):
            os.makedirs("./live_data")

    def update(self):
        start = time.time()

        #setup discord webhooks
        webhook = Webhook.partial(self.config["discord"]["webhook_id"], self.config["discord"]["webhook_token"], adapter=RequestsWebhookAdapter())
        prec_webhook = Webhook.partial(self.config["discord"]["prec_webhook_id"], self.config["discord"]["prec_webhook_token"], adapter=RequestsWebhookAdapter())

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
                    webhook.send(message)
                
                elif action in "PrecLong" or action in "PrecShort":
                    #create the message
                    message = f"{symbol_string}: {action}"
                    #send message
                    prec_webhook.send(message)

            #check if timeout has been reached
            if time.time()-start > 60:
                #save the unsuccesfull coins
                self.unsuccessfull_updates += coin_list
                print("Unsuccesfull updates because of timeout:", coin_list)
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

    def _round5(self, number):
        return 5 * math.ceil((number+1)/5)

    def _timer(self):
        #incase the timer got called immediately after a 5 minute
        while datetime.now().minute % 5 == 0:
            pass
        while datetime.now().minute % 5 != 0:
            pass
    
    def _reinitializer(self, attempts=15):
        """
        Method for reinitializing coins that were unable to update
        """
        reinitialized_coins = {}
        for i in range(attempts):
            #reinitialize the coins
            with futures.ThreadPoolExecutor() as executor:
                results = [executor.submit(Coin.create, symbol, self.config) for symbol in self.unsuccessfull_updates]
            
            #check if they were initialized correctly
            for result in results:
                try:
                    coin = result.result()
                    #add to local_coin_dict
                    reinitialized_coins[coin.symbol] = coin
                
                except Exception:
                    time.sleep(1)

        return reinitialized_coins

    def _checker(self):
        """
        Method for checking on the coin objects
        """
        for symbol in self.coin_dict.keys():
            coin = self.coin_dict[symbol]
            
            """
            Check the 5m candles
            """
            if coin.klines_5m.iloc[-1,-2].minute != self._round5(datetime.now().minute):
                print("got a mistake")
                self.unsuccessfull_updates.append(coin.symbol)

            """
            Check the 1h candles
            """
            print(coin.klines_1h)

    def _between_worker(self):
        """
        Function for work that needs to be done between updates
        """
        ret_dict = {}

        ret_dict["reinitializer"] = self._reinitializer()

        return ret_dict

    def _logger(self):
        #create new folder
        minute = self._round5(datetime.now().minute)-5
        new_directory = f"{self.log_path}/coins/{datetime.now().strftime('%d-%m-%y=%H-')}{minute}"
        os.makedirs(new_directory)

        #log all the coins
        for symbol in self.coin_dict:
            self.coin_dict[symbol].klines_5m.to_csv(path_or_buf=f"{new_directory}/{symbol}_5m", index=False)
            self.coin_dict[symbol].klines_1h.to_csv(path_or_buf=f"{new_directory}/{symbol}_1h", index=False)

    def run(self):
        #log initial state
        if self.logging:
            self._logger()

        #main loop
        while True:
            #wait for time to get to 5 minutes
            self._timer()
            
            #update the coins
            self.update()

            #log all the data
            if self.logging:
                self._logger()


            #do tasks between
            print("Cleaning Garbage")
            
            successfull_cleanup = False
            with futures.ProcessPoolExecutor() as executor:
                future = executor.submit(self._between_worker)

                #calculate remaining time
                minutes = self._round5(datetime.now().minute) - 1 - datetime.now().minute
                seconds = datetime.now().second
                remaining_seconds = minutes*60 - seconds
                print(f"We have {remaining_seconds} seconds to clean up")

                try:
                    ret_dict = future.result(timeout=remaining_seconds)
                    successfull_cleanup = True
                except Exception as e:
                    print("Not able to do all the Work between because of timeout")
                    print(e)

            if successfull_cleanup:
                #get results from _reinitialiter and put them in coin_dict
                reinitialized_coins = ret_dict["reinitializer"]
                for symbol in reinitialized_coins.keys():
                    #add symbol to coindict
                    self.coin_dict[symbol] = reinitialized_coins[symbol]
                    #remove from unsuccessfull_updates
                    self.unsuccessfull_updates.remove(symbol)

            print("Done with cleaning")

if __name__ == "__main__":
    bot = Bot(logging=True)

    bot.run()