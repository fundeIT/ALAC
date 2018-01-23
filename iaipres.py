from db import DB
from lxml import html
import requests
import datetime
import numpy as np

base = 'https://transparencia.iaip.gob.sv/transparencia-activa/gestion-operativa/'
collection = DB('iaipres')

def savePage(link):
    try:
        page = requests.get(link)
        if collection.get({'link': link}):
            collection.update({'link': link}, {'content': page.content})
        else:
            collection.new({'link': link, 'content': page.content})
        print('%s: %d' % (link, len(page.content)))
    except:
        print("Link connection failed: %s" % link)

def crawlPage(content):
    elements = html.fromstring(content)
    links = elements.xpath('//a/@href')
    for link in links:
        if link.find('NUE') >= 0 and link.find('.txt') >= 0:
            savePage(link)

def getPages():
    try:
        page = requests.get(base)
        crawlPage(page.content)
    except:
        print('Comm failure')

