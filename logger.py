import csv
from datetime import datetime
import time
import os
import pandas as pd

"""
To-Do:
"""

def timer():
    #incase the timer got called immediately after a 5 minute
    while (datetime.now().minute-3) % 5 == 0:
        pass

    while (datetime.now().minute-3) % 5 != 0:
        pass
    
    print("now")

def log_line(directory):
    #read the csv
    data = pd.read_csv("actions.csv", names=["symbol", "trend_state", "action"])

    #convert to list
    print(data.shape)
    csv_row = []
    for index in range(data.shape[0]):
        csv_row += data.iloc[index,:].to_list()
    
    #add timestamp
    csv_row.append(datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))

    #log to file
    with open(f'{directory}/actions_log.csv', 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_row)

#create new logfolder
directory = f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
os.makedirs(directory)

while True:
    timer()

    log_line(directory=directory)