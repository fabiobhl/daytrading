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

"""
To-Do:
    -email notification on error
    -solve updating too early
    -binance link to long/short trading pair
    -between checks, which make sure that all the dfs got update correctly / logging
"""


"""
Backend Setup
"""
symbol_list = ["ETHUSDT", "BTCUSDT", "LTCUSDT", "UNIUSDT", "DOTUSDT", "ADAUSDT", "BNBUSDT", "LINKUSDT", "AAVEUSDT", "YFIUSDT"]
symbol_list2 = ["ETHUSDT", "BTCUSDT", "LTCUSDT", "UNIUSDT", "DOTUSDT", "ADAUSDT", "BNBUSDT", "LINKUSDT", "AAVEUSDT", "YFIUSDT",
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

async def update(coin_dict, update_variable):
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

    #save the actions to csv
    csv_frame = []
    for key in coin_dict:
        #get values
        action = coin_dict[key].buy_signal_detection()
        trend_state = coin_dict[key].trend_state
        symbol = key

        #append to frame
        csv_frame.append([symbol, trend_state, action])
        
        #fill notification dict
        if action in "PrecLong" or action in "PrecShort":
            disc_not[symbol] = action
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
    
    return disc_not

"""
Discord Setup
"""
token = "ODEyOTk1NzE2Njk5NjUyMTA2.YDI3Qw.s6Z-N-FyhEwUBLrL3amFDb5p4FY"
channel_id = 813126932707147806

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

async def asynctimer():
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
async def main():
    #wait for discord client to be ready
    await client.wait_until_ready()
    channel = client.get_channel(channel_id)
    await asyncio.sleep(0.01)

    #download all coins
    coin_dict = setup(symbols=symbol_list2)
    
    #main loop
    while not client.is_closed():
        #wait for 5 minutes to pass
        waiting_task = asyncio.create_task(asynctimer())
        await waiting_task

        #update the coins
        updating_task = asyncio.create_task(update(coin_dict=coin_dict, update_variable=waiting_task.result()))
        await updating_task

        #send results to discord channel
        for key in updating_task.result():
            await channel.send(f"{key}: {updating_task.result()[key]}")
        
        print("joee we did it")


"""
Bot
"""
client.loop.create_task(main())
client.run(token)