from binance.client import Client
import json
import requests
import pandas as pd

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

config = read_config()

client = Client(api_key=config["binance"]["key"], api_secret=config["binance"]["secret"])

raw_data = client.futures_position_information()

#raw_data = client.futures_klines(symbol="ETHUSDT", interval="5m", limit=2)

"""
response = requests.get("https://fapi.binance.com")
"""

data = pd.DataFrame(raw_data)

data["positionAmt"] = pd.to_numeric(data["positionAmt"], downcast="float")

indeces = data.index[data["positionAmt"] != 0].tolist()

print(data.iloc[indeces,:])