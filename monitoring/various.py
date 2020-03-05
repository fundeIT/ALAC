import os                         # To access operative system functions
import requests                   # To get webpages from Internet
import pandas as pd               # To manage datasets
import json                       # To manage JSON files
# from fbprophet import Prophet     # To make predictions based on time series
import matplotlib.pyplot as plt   # Plotting library
from lxml import html
# from mpl_toolkits.basemap import Basemap, cm
# import pygeoip
import subprocess


STARTING_DATE = '2017-04-01'
ENDING_DATE = '2019-12-31'

URL = 'http://alac.funde.org'
API_KEY = 'kljaaoTI*%89f92nklf@#fadi3'

LOG_FILES_PATH = 'hits'
DATA_PATH = 'data'
IMAGES_PATH = 'images'

GEOIP4_PATH = '/usr/share/GeoIP/GeoIPCity.dat'
GEOIP6_PATH = '/usr/share/GeoIP/GeoIPCityv6.dat'

###############################################################################
# Advisory actions
###############################################################################

def get_tickets(date_start, date_end):
    url = URL + '/api/v1/tickets'
    data = {
        'api_key': 'API_KEY',
        'startdate': date_start,
        'enddate': date_end,
        'limit': 10000,
        'page': 0
    }
    result = requests.post(url, data=data)   # Getting the data from Internet
    content = json.loads(result.content)     # Converting from JSON
    data = pd.DataFrame(content)             # Converting to a dataframe
    data.rename(columns={'_id': 'ticket_id', 'msg': 'title'}, inplace=True)
    return data

def get_ticket_threads(data):
    """
    It is needed to remove ENDING_DATE
    """
    aux = [item for index, row in data.iterrows() for item in row['threads']]
    threads = pd.DataFrame(aux)
    threads = threads[threads.date <= ENDING_DATE]
    threads = threads.merge(
        data[['ticket_id', 'ticket', 'year', 'title', 'status']],
        on='ticket_id',
        how='left'
    )
    threads['month'] = threads.date.apply(lambda x: str(x)[:7])
    return threads

def save_ticket_threads(threads):
    output = threads.copy()
    output['msg'] = threads['msg'].apply(
        lambda x: str(x)[0:63].replace('\n', ' ').replace('\r', '').strip()
    )
    output['title'] = threads['title'].apply(
        lambda x: str(x).replace('\n', ' ').replace('\r', '').strip()
    )
    output = output[['year', 'ticket', 'date', 'title', 'msg', 'status']]
    output.sort_values('date').to_csv('data/tickets.csv', index=False)

# Grouping by month

def threads_by_month(threads):
    aux = threads \
        .groupby(['month', 'status']) \
        .count()['_id'] \
        .fillna(0) \
        .reset_index()
    by_month = pd.crosstab(aux.month, aux.status, aux._id, aggfunc=sum) \
        .fillna(0)
    by_month['total'] = by_month['closed'] + by_month['openned']
    by_month.to_csv('data/tickets-by-month.csv')
    fig = by_month[['closed', 'openned']] \
        .plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Tickets by month')
    plt.savefig('images/tickets_by_month.png')
    plt.close()
    return by_month

# Predictions

"""
def threads_forecast(threads):
    by_day = threads.groupby('date').count()['_id'].reset_index()
    by_day.rename(columns={'date': 'ds', '_id': 'y'}, inplace=True)
    m = Prophet(yearly_seasonality=True, daily_seasonality=True)
    m.fit(by_day)
    future = m.make_future_dataframe(periods=180)
    forecast = m.predict(future)
    forecast.to_csv('data/tickets_forecast.csv', index=False)
    return forecast
"""

"""
f = m.plot(forecast)
plt.title('Tickets - Forecast by day')
plt.ylabel('Entries')
plt.savefig('images/tickets_forecast.png')
"""

###############################################################################
# Information Requests
###############################################################################

#%%

def get_requests(date_start, date_end):
    # Setting the URL to access the Request API
    url = URL + '/api/v1/requests?startdate={}&enddate={}&page=0&limit=10000'.format(date_start, date_end)
    # Obtaining the data
    data = pd.read_json(url)
    # Creating new attributes
    data['month'] = data.date.apply(lambda x: str(x)[:7])
    data['reqs'] = data.detail.apply(lambda x: str(x).strip().split('\n'))
    data['num'] = data.reqs.apply(lambda x: len(x))
    data['actions'] = data['updates'].apply(lambda x: len(x))
    # Storing the dataset
    data.to_csv('data/requests.csv', index=False)
    return data

#%% Requests by result

def requests_by_result(data):
    by_result = pd.DataFrame(data[data.status == 'Cerrada'] \
        .groupby('result') \
        .sum()['num'] \
        .sort_values(ascending=False))
    by_result.to_csv('data/requests-by-result.csv')
    fig = by_result.plot(kind='bar', figsize=(16,9), alpha=0.5)
    plt.title('Requests by outcomes')
    plt.xlabel('Outcome')
    plt.ylabel('Frequency')
    plt.savefig('images/requests-by-result.png')
    plt.close()
    return by_result

#%% Requests by offices

def requests_by_office(data):
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
    plt.close()
    return by_office

#%% Requests by programs

def requests_by_program(by_office):
    sp = pd.read_csv('sector_programs.csv')
    by_office = sp.merge(by_office, on='office')
    by_program = by_office.groupby('program').sum().sort_values('Total', ascending=False)
    by_program.to_csv('data/requests-by-program.csv')
    fig = by_program[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Requests by program')
    plt.xlabel('Programs')
    plt.ylabel('Frequency')
    plt.savefig('images/requests-by-program.png')
    plt.close()
    return by_program

def requests_by_sector(by_office):
    by_sector = by_office.groupby('sector').sum().sort_values('Total', ascending=False)
    by_sector.to_csv('data/requests-by-sector.csv')
    by_sector[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Requests by sector')
    plt.xlabel('Sectors')
    plt.ylabel('Frequency')
    plt.savefig('images/requests-by-sector.png')
    return by_sector

def requests_by_function(by_office):
    by_function = by_office.groupby('function').sum().sort_values('Total', ascending=False)
    by_function.to_csv('data/requests-by-function.csv')
    by_function[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Requests by function')
    plt.xlabel('Functions')
    plt.ylabel('Frequency')
    plt.savefig('images/requests-by-sector.png')
    return by_function

#%% Actions for requests

def requests_actions(data):
    aux = [{**item, 'office': row['office'], 'url': row['url']} 
        for index, row in data.iterrows() 
        for item in row['updates']
    ] 
    updates = pd.DataFrame(aux)
    updates['month'] = updates.date.apply(lambda x: str(x)[:7])
    updates = updates[updates.month <= ENDING_DATE]
    return updates

#%% Requests by month

def requests_by_month(data):
    aux = data.groupby(['month', 'status']).sum()['num'].reset_index()
    by_month = pd.crosstab(aux.month, aux.status, aux.num, aggfunc=sum).fillna(0)
    # by_month.to_csv('data/requests-by-month.csv')
    # fig = by_month.plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    # plt.title('Requests by month')
    # plt.savefig('images/requests-by-month.png')
    # plt.close()
    return by_month

def requests_actions_by_month(data, updates):
    upd_by_month = updates.groupby('month').count()['detail']
    upd_by_month.plot(kind='bar', figsize=(16,9), alpha=0.5)
    plt.title('Request Actions')
    plt.xlabel('Actions')
    plt.ylabel('Frequency')
    plt.savefig('images/requests-actions.png')
    plt.close()
    by_month = requests_by_month(data)
    by_month['Total'] = by_month['Cerrada'] + by_month['En trámite']
    by_month_summ = by_month.merge(upd_by_month, on='month').rename(columns={'detail': 'Acciones'})
    by_month_summ.to_csv('data/requests-by-month.csv')
    return by_month_summ

#%% Predictions

"""
def requests_forecast(updates):
    by_day = updates.groupby('date').count()['detail'].reset_index()
    by_day.rename(columns={'date': 'ds', 'detail': 'y'}, inplace=True)
    m = Prophet(yearly_seasonality=True, daily_seasonality=True)
    m.fit(by_day)
    future = m.make_future_dataframe(periods=180)
    forecast = m.predict(future)
    forecast.to_csv('data/requests-forecasts.csv', index=False)
    return forecast
"""


"""
f = m.plot(forecast)
f.savefig('images/forecast_requests.png')
"""

#%% Saving results

def save_requests_actions(data, updates):
    data[['date', 'overview', 'office', 'status', 'result', 'num', 'actions', 'url']].to_csv('data/requests.csv', index=False)
    updates['detail'] = updates['detail'].apply(lambda x: str(x).replace('\n', ' ').replace('\r', ''))
    updates[['date', 'office', 'title', 'detail', 'url']].sort_values('date').to_csv('data/requests-actions.csv', index=False)

###############################################################################
# Legal Resources
###############################################################################

def get_complains(date_start, date_end):
    # Setting the URL to access the Request API
    url = URL + '/api/v1/complains?startdate={}&enddate={}&page=0&limit=10000'.format(date_start, date_end)
    # Obtaining the data
    data = pd.read_json(url)
    ## Creating a new attribute: month
    data['month'] = data.date.apply(lambda x: str(x)[:7])
    data['actions'] = data['updates'].apply(lambda x: len(x))
    return data

#%% Complains by month

def complains_by_month(data):
    aux = data.groupby(['month', 'status']).count()['_id'].reset_index()
    by_month = pd.crosstab(aux.month, aux.status, aux._id, aggfunc=sum).fillna(0)

    ax = by_month.plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Complains by month')
    plt.xlabel('Complains')
    plt.ylabel('Frequency')
    plt.savefig('images/complains-by-month.png')

    by_month['Total'] = by_month['Cerrada'] + by_month['En trámite']
    by_month.to_csv('data/complains-by-month.csv')

    print('Complains:')
    print(by_month.sum())
    return by_month

#%% Complains by result

def complains_by_result(data):
    by_result = data[data.status == 'Cerrada'] \
        .groupby('result') \
        .count()['_id'] \
        .sort_values(ascending=False) 
    by_result.to_csv('data/complains-by-result.csv', header=True)
    fig = by_result.plot(kind='bar', figsize=(16,9), alpha=0.5)
    plt.title('Complains by result')
    plt.xlabel('Complains')
    plt.ylabel('Frequency')
    plt.savefig('images/complains-by-result.png')
    plt.close()
    return by_result

#%% Complains by offices

def complains_by_office(data):
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
    plt.close()
    return by_office

#%% Complains by program

def complains_by_program(by_office):
    sp = pd.read_csv('sector_programs.csv')
    by_office = sp.merge(by_office, on='office')
    by_program = by_office.groupby('program').sum().sort_values('Total', ascending=False)
    by_program.to_csv('data/complains-by-program.csv')
    by_program[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Complains by program')
    plt.xlabel('Program')
    plt.ylabel('Frequency')
    plt.savefig('images/complains-by-program.png')
    plt.close()
    return by_program

def complains_by_sector(by_office):
    sp = pd.read_csv('sector_programs.csv')
    by_office = sp.merge(by_office, on='office')
    by_sector = by_office.groupby('sector').sum().sort_values('Total', ascending=False)
    by_sector.to_csv('data/complains-by-sector.csv')
    by_sector[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Complains by sector')
    plt.xlabel('Sector')
    plt.ylabel('Frequency')
    plt.savefig('images/complains-by-sector.png')
    plt.close()
    return by_sector

def complains_by_function(by_office):
    sp = pd.read_csv('sector_programs.csv')
    by_office = sp.merge(by_office, on='office')
    by_function = by_office.groupby('function').sum().sort_values('Total', ascending=False)
    by_function.to_csv('data/complains-by-function.csv')
    by_function[['Cerrada', 'En trámite']].plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    plt.title('Complains by function')
    plt.xlabel('Function')
    plt.ylabel('Frequency')
    plt.savefig('images/complains-by-sector.png')
    plt.close()
    return by_function

def complains_by_reviewer(data):
    aux = data.groupby(['reviewer', 'status']).count()['_id'].reset_index()
    by_reviewer = pd.crosstab(aux.reviewer, aux.status, aux._id, aggfunc=sum).fillna(0)
    by_reviewer['Total'] = by_reviewer['Cerrada'] + by_reviewer['En trámite']
    by_reviewer = by_reviewer.groupby('reviewer').sum().sort_values('Total', ascending=False)
    by_reviewer.to_csv('data/complains-by-reviewer.csv')
    return by_reviewer

#%% Complain Actions

def complains_by_month(data):
    aux = data.groupby(['month', 'status']).count()['_id'].reset_index()
    by_month = pd.crosstab(aux.month, aux.status, aux._id, aggfunc=sum).fillna(0)

    # ax = by_month.plot(kind='bar', stacked=True, figsize=(16,9), alpha=0.5)
    # plt.title('Complains by month')
    # plt.xlabel('Complains')
    # plt.ylabel('Frequency')
    # plt.savefig('images/complains-by-month.png')
    by_month['Total'] = by_month['Cerrada'] + by_month['En trámite']
    by_month.to_csv('data/complains-by-month.csv')
    # print('Complains:')
    # print(by_month.sum())
    return by_month

def complains_actions(data):
    aux = [{**item, 'title': row['overview'], 'office': row['office'], 'url': row['url']} 
        for index, row in data.iterrows() 
        for item in row['updates']
    ] 
    updates = pd.DataFrame(aux)
    updates['month'] = updates.date.apply(lambda x: str(x)[:7])
    updates = updates[updates.month <= ENDING_DATE]
    return updates

def complains_actions_by_month(data, updates):
    upd_by_month = updates.groupby('month').count()['detail']
    upd_by_month.plot(kind='bar', figsize=(16,9), alpha=0.5)
    plt.title('Complain actions by month')
    plt.xlabel('Complain Actions')
    plt.ylabel('Frequency')
    plt.savefig('images/complains-actions-by-month.png')
    plt.close()

    by_month_summ = complains_by_month(data) \
        .merge(upd_by_month, on='month') \
        .rename(columns={'detail': 'Acciones'})
    by_month_summ.to_csv('data/complains-actions-by-month.csv')
    # print('Complains:')
    # print(by_month_summ.sum())
    return by_month_summ

#%% Predictions

"""
def complains_forecast(updates):
    by_day = updates.groupby('date').count()['detail'].reset_index()
    by_day.rename(columns={'date': 'ds', 'detail': 'y'}, inplace=True)

    m = Prophet()
    m.fit(by_day)
    future = m.make_future_dataframe(periods=180)
    forecast = m.predict(future)
    forecast.to_csv('data/complains-forecasts.csv', index=False)
    return forecast
"""

"""
f = m.plot(forecast)
plt.title('Complain forecasts by day')
f.savefig('images/complains-forecasts.png')
"""

#%% Saving results

def complains_save(data, updates):
    data = data[['date', 'overview', 'office', 'reviewer', 'status', 'result', 'actions', 'url']]
    data.to_csv('data/complains.csv', index=False)
    updates['detail'] = updates['detail'] \
        .apply(lambda x: str(x).replace('\n', ' ').replace('\r', ''))
    updates[['date', 'office', 'title', 'detail', 'url']] \
        .sort_values('date').to_csv('data/complains-actions.csv', index=False)

###############################################################################
# Website
###############################################################################

#%% Processing data

def download_hit_files():
    subprocess.call(
        ['rsync', '-av', '--delete', 'root@alac.funde.org:ALAC/log/hits', '.']
    )

def get_hits(date_start, date_end):
    base_path = LOG_FILES_PATH
    download_hit_files()
    month_begin = date_start.replace('-', '')[0:6]
    month_end = date_end.replace('-', '')[0:6]
    lines = []
    for month in os.listdir(base_path):
        if month >= month_begin and month <= month_end:
            with open(base_path + '/' + month, 'r') as fd:
                lines += fd.readlines()
    data = []
    for item in lines:
        fields = item.strip().split(' ')
        if len(fields) >= 3:
            data.append({
                "Date": fields[0], 
                "Time": fields[1], 
                "IP": fields[2], 
                "Resource": fields[3]
            })
    df = pd.DataFrame(data)
    plt.figure(figsize=(16,9))
    gb = df.groupby(['Date']).count()
    plt.xticks(rotation=90)
    gb['IP'].plot(kind='area', alpha=0.5)
    plt.savefig('images/website-hits-by-day.png')
    print("Average Daily Hits: %f" % gb.Resource.mean())
    df.to_csv('data/website-hits.csv', index=False)
    return df

#%% Hits by month

def hits_by_month(df):
    df['month'] = df.Date.apply(lambda x: x[0:7])
    tbl = df.groupby(['month'])['month'].count()
    tbl.to_csv('data/website-hits-by-month.csv')
    plt.figure(figsize=(16,9))
    ax = tbl.plot(kind='bar', alpha=0.5)
    ax.set_ylabel("Hits x 1000")
    ax.set_xlabel('Meses')
    f = ax.get_figure()
    f.savefig('images/website-hists-by-month.png', header=True)
    return tbl

#%% Predictions

"""
def hits_forecast(df):
    by_day = df.groupby('Date').count()['IP'].reset_index()
    by_day.rename(columns={'Date': 'ds', 'IP': 'y'}, inplace=True)

    m = Prophet(yearly_seasonality=True, daily_seasonality=True)
    m.fit(by_day)
    future = m.make_future_dataframe(periods=180)
    forecast = m.predict(future)
    forecast.to_csv('data/website-hits-forecast.csv', index=False)
    return forecast
"""

"""
f = m.plot(forecast)
f.savefig('images/website-hits-forecasts.png')
"""

#%% Last month

def getReferences(path):
    url = os.getenv('URL') + path
    page = requests.get(url).content
    content = html.fromstring(page)
    title = content.xpath('//h3/text()')[0]
    office = content.xpath('//div[@id="office"]/a/text()')[0]
    date = content.xpath('//div[@id="reference"]/text()')[1].strip().split(':')[1].strip()
    rec = {'title': title, 'office': office, 'date': date, 'url': url}
    return rec

def getResources(month, resource, limit=25):
    mm = month[0:4] + '-' + month[4:]
    data = df[df.month == mm].groupby(by=['Resource']).count()['month'].reset_index()
    data = data[data.Resource.str.contains('/%s/' % resource)].sort_values('month', ascending=False)[0:limit]
    ret = []
    for idx in range(len(data)):
        row = data.iloc[idx]
        rec = getReferences(row.Resource)
        rec['hits'] = row.month
        ret.append(rec)
    return pd.DataFrame(ret)

def get_requests_last_month():
    import requests
    requests = getResources(month_end, 'requests')
    requests.to_csv('data/website-requests-most-view-%s.csv' % month_end, index=False)
    return requests

def get_complains_last_month():
    import requests
    complains = getResources(month_end, 'complains')
    complains.to_csv('output_data/complains_most_%s.csv' % month_end, index=False)
    return complains

def hits_make_maps():
    mm = os.getenv('ENDING_DATE')[0:7]
    ip = df[df.month == mm].groupby(by='IP').count().sort_values(by=['month'], ascending=False).index

    gi4 = pygeoip.GeoIP('/usr/share/GeoIP/GeoIPCity.dat')
    gi6 = pygeoip.GeoIP('/usr/share/GeoIP/GeoIPCityv6.dat')

    geo = []
    counter = 0
    for el in ip:
        counter += 1
        a = gi6.record_by_addr(el) if el.find(':') > 0 else gi4.record_by_addr(el)
        geo.append(a)

    latitude = []
    longitude = []
    city = []
    country = []
    for el in geo:
        if el:
            latitude.append(el['latitude'])
            longitude.append(el['longitude'])
            city.append(el['city'])
            country.append(el['country_code'])

    latlong = pd.DataFrame({'latitude': latitude, 'longitude': longitude, 'item': range(len(longitude)), 'city': city,
                           'country': country})

    ll = latlong.groupby(by=['latitude', 'longitude']).count()

    ll.item = ll.item / max(ll.item)
    ll.reset_index(level=0, inplace=True)
    ll.reset_index(level=0, inplace=True)

    plt.figure(figsize=(16,9))
    m = Basemap(llcrnrlon=-180.,llcrnrlat=-60.,urcrnrlon=180.,urcrnrlat=90.)
    m.drawcoastlines()
    m.drawmapboundary(fill_color=(0.3, 0.9, 0.9))
    m.drawcountries()
    m.fillcontinents(color='#cc9966', lake_color='#99ffff', alpha=0.5)
    m.scatter(ll.longitude, ll.latitude, ll.item*500, marker = 'o', color='r', alpha=0.5, zorder=5)
    plt.savefig('images/website-geosources-int-%s.png' % month_end)

    plt.figure(figsize=(16,9))
    m = Basemap(llcrnrlon=-90.2,llcrnrlat=13.1,urcrnrlon=-87.6,urcrnrlat=14.5, resolution='i')
    m.drawmapboundary(fill_color='aqua')
    m.fillcontinents(color='#cc9966', lake_color='#99ffff', alpha=0.35)
    # m.drawcoastlines()
    m.readshapefile('third/SLV_adm1', 'depto')
    m.scatter(ll.longitude, ll.latitude, ll.item*5000, marker = 'o', color='r', alpha=0.5, zorder=5)
    plt.savefig('images/website-geosources-esa-%s.png' % month_end)

def fetch_tickets(date_start, date_end):
    res = {}
    res['tickets'] = get_tickets(date_start, date_end)
    res['actions'] = get_ticket_threads(res['tickets'])  
    save_ticket_threads(res['actions'])
    res['by_month'] = threads_by_month(res['actions'])
    return res

def fetch_requests(date_start, date_end):
    res = {}
    res['requests'] = get_requests(date_start, date_end)
    res['by_result'] = requests_by_result(res['requests'])
    res['by_office'] = requests_by_office(res['requests'])
    res['by_program'] = requests_by_program(res['by_office']) 
    res['by_sector'] = requests_by_sector(res['by_office'])
    res['by_function'] = requests_by_function(res['by_office'])
    res['actions'] = requests_actions(res['requests']) 
    res['by_month'] = requests_actions_by_month(res['requests'], res['actions'])
    save_requests_actions(res['requests'], res['actions'])
    return res

def fetch_complains(date_start, date_end):
    res = {}
    res['complains'] = get_complains(date_start, date_end)
    res['by_result'] = complains_by_result(res['complains'])
    res['by_office'] = complains_by_office(res['complains']) 
    res['by_program'] = complains_by_program(res['by_office'])
    res['by_sector'] = complains_by_sector(res['by_office'])
    res['by_function'] = complains_by_function(res['by_office'])
    res['by_reviewer'] = complains_by_reviewer(res['complains'])
    res['actions'] = complains_actions(res['complains'])
    res['by_month'] = complains_actions_by_month(res['complains'], res['actions'])
    complains_save(res['complains'], res['actions'])
    return res
    
def fetch_hits(date_start, date_end):
    res = {}
    res['hits'] = get_hits(date_start, date_end)
    res['by_month'] = hits_by_month(res['hits'])
    return res

if __name__ == '__main__':
    date_start = '2017-04-01'
    date_end   = '2019-12-31'
    tickets = fetch_tickets(date_start, date_end)
    requests = fetch_requests(date_start, date_end)
    complains = fetch_complains(date_start, date_end)
    hits = fetch_hits(date_start, date_end)
    

