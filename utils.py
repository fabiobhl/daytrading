import time
from datetime import datetime

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