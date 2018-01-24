from db import DB
from lxml import html
import requests
import datetime
import numpy as np

base = 'https://transparencia.iaip.gob.sv/transparencia-activa/gestion-operativa/'
collection = DB('iaipres')

def savePage(link):
    if not collection.get({'link': link}):
        try:
            page = requests.get(link)
            content = page.content.decode('Windows-1252')
            collection.new({'link': link, 'content': content})
            print('%s: %d' % (link, len(content)))
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

def asciify(s):
    s = s.replace('á', 'a')
    s = s.replace('é', 'e')
    s = s.replace('í', 'i')
    s = s.replace('ó', 'o')
    s = s.replace('ú', 'u')
    s = s.replace('ñ', 'n')
    l = list(s)
    s = ''
    for i in range(len(l)):
        p = ord(l[i])
        if not ((p>=97 and p<=122) or (p>=48 and p<57)):
            l[i] = ' '
        s += l[i]
    return s

def tokenize(s):
    tokens = {}
    s = s.lower()
    s = asciify(s)
    d = s.split()
    for el in d:
        if len(el) <= 2:
            continue
        if el[-1] in ('s', 'n'):
            el = el[0:-1]
        if el[-1] in ('a', 'e', 'o'):
            el = el[0:-1]
        if el in tokens.keys():
            tokens[el] += 1
        else:
            tokens[el] = 1
    return tokens

def updateTokens():
    ret = collection.collection.find()
    for el in ret:
        start = el['link'].rfind('/') + 1
        end = el['link'].rfind('.txt')
        title = el['link'][start:end].replace('-', ' ')
        s = str(el['content'])
        t = tokenize(s)
        collection.update({'_id': el['_id']}, {'title': title, 'tokens': t})

def calcSim(t1, t2):
    corpora = list(set(list(t1.keys()) + list(t2.keys())))
    n = len(corpora)
    a = np.zeros(n)
    b = np.zeros(n)
    for el in corpora:
        for k in t1.keys():
            if k == el:
                a[corpora.index(el)] = t1[k]
        for k in t2.keys():
            if k == el:
                b[corpora.index(el)] = t2[k]
    ma = (a * a).sum()
    mb = (b * b).sum()
    if (ma == 0 or mb == 0):
        return 0
    sim = (a * b).sum() / (np.sqrt(ma) * np.sqrt(mb))
    if not sim:
        return 0
    return sim

def rank(s):
    ranks = {}
    st = tokenize(s)
    ret = collection.collection.find()
    for el in ret:
        sim = calcSim(st, el['tokens']) 
        if not sim or sim == 0:
            continue
        rnk = str(np.round(sim, 8))
        rcd = {'title': el['title'], 'url': el['link']}
        if rnk in ranks.keys():
            ranks[rnk].append(rcd)
        else:
            ranks[rnk] = [rcd]
    return ranks

def search(s):
    r = rank(s)
    l = sorted(r, reverse=True)
    for key in l:
        for el in r[key]:
            print("%s" % el['title'])
            print("%s (%s)" % (el['url'], key))


