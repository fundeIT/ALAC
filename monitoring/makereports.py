import sys
import os                           # To access operative system functions
import requests                     # To get webpages from Internet
import pandas as pd                 # To manage datasets
import json                         # To manage JSON files
# from fbprophet import Prophet     # To make predictions based on time series
from dotenv import load_dotenv      # To access environment variables
import matplotlib.pyplot as plt     # Plotting library
from lxml import html
# from mpl_toolkits.basemap import Basemap, cm
# import pygeoip

load_dotenv()

STARTING_DATE = sys.argv[1]
ENDING_DATE = sys.argv[2]

url = os.getenv('URL') + '/api/v1/tickets'
data = {
    'api_key': os.getenv('API_KEY'),
    'startdate': STARTING_DATE,
    'enddate': ENDING_DATE,
    'limit': 100000,
    'page': 0
}

result = requests.post(url, data=data)   # Getting the data from Internet
content = json.loads(result.content)     # Converting from JSON
data = pd.DataFrame(content)             # Converting to a dataframe
data.rename(columns={'_id': 'ticket_id', 'msg': 'title'}, inplace=True)

aux = []
for idx in range(len(data)):
    row = data.iloc[idx]
    aux += row.threads
threads = pd.DataFrame(aux)
threads = threads[threads.date <= ENDING_DATE]
threads = threads.merge(data[['ticket_id', 'ticket', 'year', 'title', 'status']], on='ticket_id', how='left')
threads['month'] = threads.date.apply(lambda x: str(x)[:7])

output = threads.copy()
output['msg'] = threads['msg'].apply(lambda x: str(x)[0:63].replace('\n', ' ').replace('\r', '').strip())
output['title'] = threads['title'].apply(lambda x: str(x).replace('\n', ' ').replace('\r', '').strip())
output[['year', 'ticket', 'date', 'title', 'msg', 'status']].sort_values('date').to_csv('data/tickets.csv', index=False)

aux = threads.groupby(['month', 'status']).count()['_id'].fillna(0).reset_index()
by_month = pd.crosstab(aux.month, aux.status, aux._id, aggfunc=sum).fillna(0)
by_month['total'] = by_month['closed'] + by_month['openned']
by_month.to_csv('data/tickets-by-month.csv')

by_month[['closed', 'openned']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Tickets by month')
plt.savefig('images/tickets_by_month.png')

# Information Requests

# Setting the URL to access the Request API
url = os.getenv('URL') + '/api/v1/requests?startdate={}&enddate={}&page=0&limit=10000'.format(STARTING_DATE, ENDING_DATE)
# Obtaining the data
data = pd.read_json(url)
# Creating new attributes
data['month'] = data.date.apply(lambda x: str(x)[:7])
data['reqs'] = data.detail.apply(lambda x: str(x).strip().split('\n'))
data['num'] = data.reqs.apply(lambda x: len(x))
# Storing the dataset
data.to_csv('data/requests.csv', index=False)

aux = data.groupby(['month', 'status']).sum()['num'].reset_index()
by_month = pd.crosstab(aux.month, aux.status, aux.num, aggfunc=sum).fillna(0)
by_month.to_csv('data/requests-by-month.csv')

by_month.plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Requests by month')
plt.savefig('images/requests-by-month.png')

#%% Requests by result

by_result = pd.DataFrame(data[data.status == 'Cerrada'].groupby('result').sum()['num'].sort_values(ascending=False))
by_result.to_csv('data/requests-by-result.csv')

by_result.plot(kind='bar', figsize=(16,9), alpha=0.5)
plt.title('Requests by outcomes')
plt.xlabel('Outcome')
plt.ylabel('Frequency')
plt.savefig('images/requests-by-result.png')

#%% Requests by offices

aux = data.groupby(['office', 'status']).sum()['num'].reset_index()
by_office = pd.crosstab(aux.office, aux.status, aux.num, aggfunc=sum).fillna(0)
by_office['Total'] = by_office['Cerrada'] + by_office['En trámite']
by_office = by_office.sort_values('Total', ascending=False)
by_office.reset_index().to_csv('data/requests-by-offices.csv', index=False)

by_office[0:25][['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Requests by offices')
plt.xlabel('Offices')
plt.ylabel('Frequency')
plt.savefig('images/requests-by-offices.png')

#%% Requests by programs

sp = pd.read_csv('sector_programs.csv')
by_office = sp.merge(by_office, on='office')

by_program = by_office.groupby('program').sum().sort_values('Total', ascending=False)
by_program.to_csv('data/requests-by-program.csv')
by_program[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Requests by program')
plt.xlabel('Programs')
plt.ylabel('Frequency')
plt.savefig('images/requests-by-program.png')

by_sector = by_office.groupby('sector').sum().sort_values('Total', ascending=False)
by_sector.to_csv('data/requests-by-sector.csv')
by_sector[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Requests by sector')
plt.xlabel('Sectors')
plt.ylabel('Frequency')
plt.savefig('images/requests-by-sector.png')

by_function = by_office.groupby('function').sum().sort_values('Total', ascending=False)
by_function.to_csv('data/requests-by-function.csv')
by_function[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Requests by function')
plt.xlabel('Functions')
plt.ylabel('Frequency')
plt.savefig('images/requests-by-sector.png')

#%% Actions for requests

aux = []
for idx in range(len(data)):
    row = data.iloc[idx]
    # upd = ast.literal_eval(row.updates)
    for el in row.updates:
        el['url'] = row.url
        el['title'] = row.overview
        el['office'] = row.office
        aux.append(el)

data['actions'] = data['updates'].apply(lambda x: len(x))

updates = pd.DataFrame(aux)
updates['month'] = updates.date.apply(lambda x: str(x)[:7])
updates = updates[updates.month <= ENDING_DATE]

#%% Requests by month

upd_by_month = updates.groupby('month').count()['detail']
upd_by_month.plot(kind='bar', figsize=(16,9), alpha=0.5)
plt.title('Request Actions')
plt.xlabel('Actions')
plt.ylabel('Frequency')
plt.savefig('images/requests-actions.png')

by_month_summ = by_month.merge(upd_by_month, on='month').rename(columns={'detail': 'Acciones'})
by_month_summ.to_csv('data/requests-by-month.csv')


data[['date', 'overview', 'office', 'status', 'result', 'num', 'actions', 'url']].to_csv('data/requests.csv', index=False)
updates['detail'] = updates['detail'].apply(lambda x: str(x).replace('\n', ' ').replace('\r', ''))
updates[['date', 'office', 'title', 'detail', 'url']].sort_values('date').to_csv('data/requests-actions.csv', index=False)

###############################################################################
# Legal Resources
###############################################################################

# Setting the URL to access the Request API
url = os.getenv('URL') + '/api/v1/complains?startdate={}&enddate={}&page=0&limit=10000'.format(STARTING_DATE, ENDING_DATE)
# Obtaining the data
data = pd.read_json(url)
## Creating a new attribute: month
data['month'] = data.date.apply(lambda x: str(x)[:7])

#%% Complains by month

aux = data.groupby(['month', 'status']).count()['_id'].reset_index()
by_month = pd.crosstab(aux.month, aux.status, aux._id, aggfunc=sum).fillna(0)

ax = by_month.plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Complains by month')
plt.xlabel('Complains')
plt.ylabel('Frequency')
plt.savefig('images/complains-by-month.png')

by_month['Total'] = by_month['Cerrada'] + by_month['En trámite']
by_month.to_csv('data/complains-by-month.csv')

#%% Complains by result

by_result = data[data.status == 'Cerrada'].groupby('result').count()['_id'].sort_values(ascending=False)
by_result.to_csv('data/complains-by-result.csv', header=True)

by_result.plot(kind='bar', figsize=(16,9), alpha=0.5)
plt.title('Complains by result')
plt.xlabel('Complains')
plt.ylabel('Frequency')
plt.savefig('images/complains-by-result.png')

#%% Complains by offices

aux = data.groupby(['office', 'status']).count()['_id'].reset_index()
by_office = pd.crosstab(aux.office, aux.status, aux._id, aggfunc=sum).fillna(0)
by_office['Total'] = by_office['Cerrada'] + by_office['En trámite']
by_office = by_office.sort_values('Total', ascending=False)
by_office.to_csv('data/complains-by-offices.csv')

by_office[0:25][['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Complains by office')
plt.xlabel('Complains')
plt.ylabel('Frequency')
plt.savefig('images/complains-by-office.png')

#%% Complains by program

by_office = sp.merge(by_office, on='office')

by_program = by_office.groupby('program').sum().sort_values('Total', ascending=False)
by_program.to_csv('data/complains-by-program.csv')
by_program[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Complains by program')
plt.xlabel('Program')
plt.ylabel('Frequency')
plt.savefig('images/complains-by-program.png')

by_sector = by_office.groupby('sector').sum().sort_values('Total', ascending=False)
by_sector.to_csv('data/complains-by-sector.csv')
by_sector[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Complains by sector')
plt.xlabel('Sector')
plt.ylabel('Frequency')
plt.savefig('images/complains-by-sector.png')

by_function = by_office.groupby('function').sum().sort_values('Total', ascending=False)
by_function.to_csv('data/complains-by-function.csv')
by_function[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
plt.title('Complains by function')
plt.xlabel('Function')
plt.ylabel('Frequency')
plt.savefig('images/complains-by-sector.png')

aux = data.groupby(['reviewer', 'status']).count()['_id'].reset_index()
by_reviewer = pd.crosstab(aux.reviewer, aux.status, aux._id, aggfunc=sum).fillna(0)
by_reviewer['Total'] = by_reviewer['Cerrada'] + by_reviewer['En trámite']
by_reviewer = by_reviewer.groupby('reviewer').sum().sort_values('Total', ascending=False)
by_reviewer.to_csv('data/complains-by-reviewer.csv')

#%% Complain Actions

aux = []
for idx in range(len(data)):
    row = data.iloc[idx]
    # upd = ast.literal_eval(row.updates)
    for el in row.updates:
        el['url'] = row.url
        el['title'] = row.overview
        el['office'] = row.office
        aux.append(el)

data['actions'] = data['updates'].apply(lambda x: len(x))

updates = pd.DataFrame(aux)
updates['month'] = updates.date.apply(lambda x: str(x)[:7])
updates = updates[updates.month <= ENDING_DATE]

upd_by_month = updates.groupby('month').count()['detail']

upd_by_month.plot(kind='bar', figsize=(16,9), alpha=0.5)
plt.title('Complain actions by month')
plt.xlabel('Complain Actions')
plt.ylabel('Frequency')
plt.savefig('images/complains-actions-by-month.png')

by_month_summ = by_month.merge(upd_by_month, on='month').rename(columns={'detail': 'Acciones'})
by_month_summ.to_csv('data/complains-actions-by-month.csv')

#%% Saving results

data[['date', 'overview', 'office', 'reviewer', 'status', 'result', 'actions', 'url']].to_csv('data/complains.csv', index=False)
updates['detail'] = updates['detail'].apply(lambda x: str(x).replace('\n', ' ').replace('\r', ''))
updates[['date', 'office', 'title', 'detail', 'url']].sort_values('date').to_csv('data/complains-actions.csv', index=False)

###############################################################################
# Website
###############################################################################

#%% Processing data

base_path = os.getenv('LOG_FILES_PATH')
month_begin = STARTING_DATE.replace('-', '')[0:6]
month_end = ENDING_DATE.replace('-', '')[0:6]

lines = []
for month in os.listdir(base_path):
    if month >= month_begin and month <= month_end:
        with open(base_path + '/' + month, 'r') as fd:
            lines += fd.readlines()

data = []
for item in lines:
    fields = item.strip().split(' ')
    if len(fields) >= 3:
        data.append({"Date": fields[0], "Time": fields[1], "IP": fields[2], "Resource": fields[3]})

df = pd.DataFrame(data)

#%% Hits by day

plt.figure(figsize=(16,9))
gb = df.groupby(['Date']).count()
plt.xticks(rotation=90)
gb['IP'].plot(kind='area', alpha=0.5)
plt.savefig('images/website-hits-by-day.png')

#%% Hits by month

df['month'] = df.Date.apply(lambda x: x[0:7])
tbl = df.groupby(['month'])['month'].count()
tbl.to_csv('data/website-hits-by-month.csv', header=True)

plt.figure(figsize=(16,9))
ax = tbl.plot(kind='bar', alpha=0.5)
ax.set_ylabel("Hits x 1000")
ax.set_xlabel('Meses')
f = ax.get_figure()
f.savefig('images/website-hists-by-month.png')


