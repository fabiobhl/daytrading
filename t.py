from utils import read_config
from binance.client import Client

import pandas as pd

config = read_config()

def get_positions(config):
    #create the client
    client = Client(api_key=config["binance"]["key"], api_secret=config["binance"]["secret"])
    
    #download the data
    while True:
        try:
            raw_data = client.futures_position_information()
            break
        except Exception:
            print("not working")
            time.sleep(0.5)
            pass
    
    #prepare the data
    data = pd.DataFrame(raw_data)
    data["positionAmt"] = pd.to_numeric(data["positionAmt"], downcast="float")
    indeces = data.index[data["positionAmt"] != 0].to_list()
    data = data.iloc[indeces, :]

    data.drop(inplace=True, columns=["positionAmt", "entryPrice", "markPrice", "liquidationPrice", "maxNotionalValue", "marginType", "isAutoAddMargin", "positionSide", "notional", "isolatedWallet"])
    
    



get_positions(config)