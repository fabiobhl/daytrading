import multiprocessing
import time
from datetime import datetime
import threading
from concurrent import futures
from binance.client import Client
from ctypes import c_wchar_p
import json
from coin import Coin


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

    def __init__(self, config_path=None):
        #config dictionary
        self.config = self._read_config(path=config_path)
        #list of all symbol strings
        self.symbol_list = self.config["binance"]["symbol_list"]

        #create shared memory manager
        self.manager = multiprocessing.Manager()

        #create the coin_dict, containing all the coin objects
        self.coin_dict = self.manager.dict()

        #populate the dictionary
        self._setup()
        

    def add_item(self):
        self.coin_dict["test"] = "testing"

    def worker(self):

        p = multiprocessing.Process(target=self.add_item)

        p.start()
        p.join()


        print(bot.coin_dict)

    


if __name__ == "__main__":

    bot = Bot()

    bot.worker()