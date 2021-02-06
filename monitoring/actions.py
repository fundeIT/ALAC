import os
import pandas as pd
from flask import make_response
from flask_restful import Resource

import trust

def count_requests(date_start, date_end):


# Setting the URL to access the Request API
url = os.getenv('URL') + '/api/v1/requests?startdate={}&enddate={}&page=0&limit=10000'.format(os.getenv('STARTING_DATE'), os.getenv('ENDING_DATE'))
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

print('Requests:')
print(by_month.sum())

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
updates = updates[updates.month <= os.getenv('ENDING_DATE')]

#%% Requests by month

upd_by_month = updates.groupby('month').count()['detail']
upd_by_month.plot(kind='bar', figsize=(16,9), alpha=0.5)
plt.title('Request Actions')
plt.xlabel('Actions')
plt.ylabel('Frequency')
plt.savefig('images/requests-actions.png')

by_month_summ = by_month.merge(upd_by_month, on='month').rename(columns={'detail': 'Acciones'})
by_month_summ.to_csv('data/requests-by-month.csv')

print('Requests:')
print(by_month_summ.sum())

#%% Predictions

"""
by_day = updates.groupby('date').count()['detail'].reset_index()
by_day.rename(columns={'date': 'ds', 'detail': 'y'}, inplace=True)
m = Prophet(yearly_seasonality=True, daily_seasonality=True)
m.fit(by_day)
future = m.make_future_dataframe(periods=180)
forecast = m.predict(future)
forecast.to_csv('data/requests-forecasts.csv', index=False)
"""

"""
f = m.plot(forecast)
f.savefig('images/forecast_requests.png')
"""

#%% Saving results

data[['date', 'overview', 'office', 'status', 'result', 'num', 'actions', 'url']].to_csv('data/requests.csv', index=False)
updates['detail'] = updates['detail'].apply(lambda x: str(x).replace('\n', ' ').replace('\r', ''))
updates[['date', 'office', 'title', 'detail', 'url']].sort_values('date').to_csv('data/requests-actions.csv', index=False)


