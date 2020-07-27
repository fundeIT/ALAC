# Monitoring module

import os
import datetime as dt
import subprocess as sp

DATE_START = '2017-04-01'

def suggested_dates():
    now = dt.datetime.now()
    last_month = now - dt.timedelta(days=now.day)
    return DATE_START, last_month.strftime('%Y-%m-%d')
    
def prepare_datasets(starting_date, ending_date):
    print(os.getcwd())
    ret = sp.run(['python', 'makereports.py', starting_date, ending_date], capture_output=True, cwd='monitoring')
    print(ret)
    ret = sp.run(['zip', '-r', 'monitoring.zip', 'data/', 'images/'], capture_output=True, cwd='monitoring')
    print(ret)
    
    
