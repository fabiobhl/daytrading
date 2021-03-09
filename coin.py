#external libraries import
import numpy as np
import pandas as pd
from binance.client import Client
import ta
import time
from datetime import datetime


"""
SSL Channel method
"""
def ssl_channel(data, len=10):
    #get the moving averages
    data["smaHigh"] = ta.trend.sma_indicator(data["high"], window=len)
    data["smaLow"] = ta.trend.sma_indicator(data["low"], window=len)

    #reset index
    data.reset_index(inplace=True, drop=True)

    #get the Hlv column:
    data["Hlv"] = np.nan
    data["sslUp"] = np.nan
    data["sslDown"] = np.nan
    for index in range(data.shape[0]):
        if data.loc[index, "close"] > data.loc[index, "smaHigh"]:
            data.loc[index, "Hlv"] = 1
        elif data.loc[index, "close"] < data.loc[index, "smaLow"]:
            data.loc[index, "Hlv"] = -1
        else:
            data.loc[index, "Hlv"] = data["Hlv"].iloc[index-1]
    
        if data.loc[index, "Hlv"] < 0:
            data.loc[index, "sslDown"] = data.loc[index, "smaHigh"]
            data.loc[index, "sslUp"] = data.loc[index, "smaLow"]

        elif data.loc[index, "Hlv"] > 0:
            data.loc[index, "sslDown"] = data.loc[index, "smaLow"]
            data.loc[index, "sslUp"] = data.loc[index, "smaHigh"]

"""
EMA Method
"""
def ema(data, length=50):
    #create the ema
    data["ema"] = ta.trend.ema_indicator(close=data["close"], window=50, fillna=True)

    #reset index
    data.reset_index(inplace=True, drop=True)

"""
Coin Class
"""
class Coin():

    def _download(self, interval, limit):
        #download raw data
        if self.market_endpoint == "futures":
            raw_data = self.client.futures_klines(symbol=self.symbol, interval=interval, limit=limit)
        elif self.market_endpoint == "spot":
            raw_data = self.client.get_klines(symbol=self.symbol, interval=interval, limit=limit)
        else:
            raise Exception("Please choose a valid market_endpoint: [futures, spot]")
        
        #create df
        data = pd.DataFrame(raw_data)

        #clean the dataframe
        data = data.astype(float)
        data.drop(data.columns[[7,8,9,10,11]], axis=1, inplace=True)
        data.rename(columns = {0:'open_time', 1:'open', 2:'high', 3:'low', 4:'close', 5:'volume', 6:'close_time'}, inplace=True)

        #set the correct times
        data['close_time'] += 1
        data['close_time'] = pd.to_datetime(data['close_time'], unit='ms')
        data['open_time'] = pd.to_datetime(data['open_time'], unit='ms')

        #check for nan values
        if data.isna().values.any():
            raise Exception("Nan values in data, please discard this object and try again")

        return data

    def __init__(self, symbol, config):
        self.symbol = symbol
        self.client = Client(api_key=config["binance"]["key"], api_secret=config["binance"]["secret"])
        self.market_endpoint = config["binance"]["market_endpoint"]

        """
        Set the url
        """
        if self.market_endpoint == "futures":
            self.url = f"https://www.binance.com/en/futures/{self.symbol[0:-4]}_USDT"
        elif self.market_endpoint == "spot":
            self.url = f"https://www.binance.com/en/trade/{self.symbol[0:-4]}_USDT?layout=pro"
        else:
            raise Exception("Please choose a valid market_endpoint: [futures, spot]")

        """
        Download the initial 1h klines
        """
        #download the data
        data = self._download(interval="1h", limit=100)        

        #add the ssl channel
        ssl_channel(data)

        #safety reset index
        data.reset_index(inplace=True, drop=True)

        #save dataframe
        self.klines_1h = data

        """
        Download the initial 5m klines
        """
        #download the data
        data = self._download(interval="5m", limit=240)
        
        #add the 50-ema
        ema(data=data)

        #safety reset the index
        data.reset_index(inplace=True, drop=True)

        #save the dataframe
        self.klines_5m = data

        #get trend_state
        self.get_trend_state()

    def get_trend_state(self):
        if self.klines_1h["Hlv"].iloc[-1] < 0:
            self.trend_state = "down"
        else:
            self.trend_state = "up"

        return self.trend_state

    def _update_5m_data(self):
        #download new data
        new_klines = self._download(interval="5m", limit=2)

        #add new column
        new_klines["ema"] = np.nan

        #check if data is full
        if new_klines.shape != (2,8):
            raise Exception("Downloaded data not complete")
            
        #add them to the dataframe
        if new_klines.iloc[0,0] >= self.klines_5m.iloc[-1,0]:
            #replace last item
            self.klines_5m.iloc[-1,:] = new_klines.iloc[0,:]
            #add new item
            self.klines_5m = self.klines_5m.append(other=new_klines.iloc[1,:], ignore_index=True)
            #remove first item
            self.klines_5m.drop(index=0,axis=0,inplace=True)
            #reset index
            self.klines_5m.reset_index(inplace=True, drop=True)

            #add the ema
            ema(data=self.klines_5m)

            #reset the index again
            self.klines_5m.reset_index(inplace=True, drop=True)
        else:
            raise Exception("Download was too early")

    def update_data(self):
        #update the 5m klines
        self._update_5m_data()

        if datetime.now().minute == 0:
            #download data
            new_klines = self._download(interval="1h", limit=2)

            #add new columns
            new_klines["smaHigh"] = np.nan
            new_klines["smaLow"] = np.nan
            new_klines["Hlv"] = np.nan
            new_klines["sslUp"] = np.nan
            new_klines["sslDown"] = np.nan

            #check if data is full
            if new_klines.shape != (2,12):
                raise Exception("Downloaded data not complete")
                
            #add them to the dataframe
            if new_klines.iloc[0,0] >= self.klines_1h.iloc[-1,0]:
                #replace last item
                self.klines_1h.iloc[-1,:] = new_klines.iloc[0,:]
                #add new item
                self.klines_1h = self.klines_1h.append(other=new_klines.iloc[1,:], ignore_index=True)
                #remove first item
                self.klines_1h.drop(index=0,axis=0,inplace=True)
                #reset index
                self.klines_1h.reset_index(inplace=True, drop=True)

                #add the ssl channel
                ssl_channel(self.klines_1h)
                #reset the index again
                self.klines_1h.reset_index(inplace=True, drop=True)
            else:
                raise Exception("Download was too early")
                
        return self.symbol

    def buy_signal_detection(self):
        
        #update the trend state
        self.get_trend_state()

        #set the return variable
        ret_variable = "noA"

        if self.trend_state == "up":
            #preConditions
            precondition1 = self.klines_5m["open"].iloc[-2] >= self.klines_5m["ema"].iloc[-2]
            precondition2 = self.klines_5m["close"].iloc[-2] <= self.klines_5m["ema"].iloc[-2]

            #FullConditions
            condition1 = self.klines_5m["open"].iloc[-3] >= self.klines_5m["ema"].iloc[-3]
            condition2 = self.klines_5m["close"].iloc[-3] <= self.klines_5m["ema"].iloc[-3]
            condition3 = self.klines_5m["close"].iloc[-2] >= self.klines_5m["ema"].iloc[-2]
            condition4 = self.klines_5m["close"].iloc[-2] >= self.klines_5m["open"].iloc[-3]

            if precondition1 and precondition2:
                ret_variable = "PrecLong"
            elif condition1 and condition2 and condition3 and condition4:
                ret_variable = "Long"

        elif self.trend_state == "down":
            
            #preConditions
            precondition1 = self.klines_5m["open"].iloc[-2] <= self.klines_5m["ema"].iloc[-2]
            precondition2 = self.klines_5m["close"].iloc[-2] >= self.klines_5m["ema"].iloc[-2]

            #FullConditions
            condition1 = self.klines_5m["open"].iloc[-3] <= self.klines_5m["ema"].iloc[-3]
            condition2 = self.klines_5m["close"].iloc[-3] >= self.klines_5m["ema"].iloc[-3]
            condition3 = self.klines_5m["close"].iloc[-2] <= self.klines_5m["ema"].iloc[-2]
            condition4 = self.klines_5m["close"].iloc[-2] <= self.klines_5m["open"].iloc[-3]

            if precondition1 and precondition2:
                ret_variable = "PrecShort"
            elif condition1 and condition2 and condition3 and condition4:
                ret_variable = "Short"

        else:
            raise Exception("Bug alert: trend_state was not up or down!")
        
        return ret_variable

    @classmethod
    def create(cls, symbol, config):
        instance = cls(symbol=symbol, config=config)
        return instance

    def __str__(self):
        return_str = f"\n------------\nCoin Object of Symbol: {self.symbol},\nInitializationtime: {self.init_call_time}\n------------\n"
        return return_str
"""
Figure
"""
"""
import plotly.express as px
import plotly.graph_objs as go

eth = Coin("ETHUSDT")

candlestick_data_5m = go.Candlestick(x=eth.klines_5m["open_time"], open=eth.klines_5m["open"], high=eth.klines_5m["high"], low=eth.klines_5m["low"], close=eth.klines_5m["close"])
ema_data = go.Scatter(x=eth.klines_5m["open_time"], y=eth.klines_5m["ema"], line=dict(color='purple', width=1))
fig_5m = go.Figure(data=[candlestick_data_5m, ema_data])
fig_5m.show()
"""