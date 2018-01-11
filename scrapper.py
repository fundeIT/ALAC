import pymongo
from lxml import html
import requests
import datetime
import numpy as np

baseURL = "http://www.transparencia.gob.sv"
max_level = 30

def connectDB():
    client = pymongo.MongoClient('localhost', 27017)
    db = client['aipdocs']
    return db

def isDocument(href):
    ends = ['download', 'pdf', 'csv', 'doc', 'docx', 'xls', 'xlsx']
    for end in ends:
        if href[-len(end):] == end:
            return True
    return False

def scrapPage(url):
    if url.find('http') == 0 or url.find('mailto') == 0:
        return ({}, ())
    try:
        page = requests.get(baseURL + url)
    except:
        return ({}, ())
    if page.status_code != 200:
        print('%s request failed' % url)
        return ({}, ())
    if page.headers['content-type'].find('text/html') < 0:
        print('%s content type' % page.headers['content-type'])
        return ({}, ())
    data = html.fromstring(page.content)
    title = ''
    titles = data.xpath('//h1/text()')
    if titles:
        title = titles[0].strip()
    docs = []
    fwds = []
    anchors = data.xpath('//a')
    for a in anchors:
        hrefs = a.xpath('@href')
        if not hrefs:
            continue
        href = hrefs[0]
        if href.find(baseURL) == 0:
            href = href[len(baseURL):]
        pos = href.rfind('?')
        if pos != -1:
            href = href[0:pos]
        descs = a.xpath('text()')
        desc = ''
        if len(descs) > 0:
            desc = descs[0].strip()
        if isDocument(href):
            s = title + ' ' + desc
            t = tokenize(s)
            docs.append({'title': title, 'url': href, 'desc': desc, 'tokens': t})
        else:
            fwds.append(href)
    return (docs, set(fwds))

def markAsVisited(url):
    db = connectDB()
    ret = db.pages.find_one({'url': url})
    if ret:
        db.pages.update({'_id': ret['_id']}, {'$set': {'visited': True}})
    else:
        db.pages.insert_one({'url': url, 'visited': True})

def isVisited(url):
    db = connectDB()
    ret = db.pages.find_one({'url': url})
    if ret:
        return ret['visited']
    else:
        return False

def addPage(url):
    db = connectDB()
    ret = db.pages.find_one({'url': url})
    if not ret:
        db.pages.insert_one({'url': url, 'visited': False})

def addDoc(doc):
    db = connectDB()
    ret = db.docs.find_one({'url': doc['url']})
    if ret:
        db.docs.update({'_id': ret['_id']}, {'$set': doc})
    else:
        db.docs.insert_one(doc)

def crawlSite(url, level):
    if level > max_level:
        return
    docs, fwds = scrapPage(url)
    print("[%d] %s: %d docs and %d forwards" % (level, url, len(docs), len(fwds)))
    for doc in docs:
        addDoc(doc)
    for fwd in fwds:
        if fwd == url:
            continue
        if not isVisited(fwd):
            crawlSite(fwd, level + 1)
    markAsVisited(url)

def toCSV(filename):
    db = connectDB()
    ret = db.docs.find()
    if not ret:
        return
    print("entity\ttitle\tlink")
    for el in ret:
        print("%s\t%s\t%s" % (el['title'], el['desc'], baseURL + el['url']))

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
        if el in tokens.keys():
            tokens[el] += 1
        else:
            tokens[el] = 1
    return tokens

def updateTokens():
    db = connectDB()
    ret = db.docs.find()
    for el in ret:
        s = el['title'] + ' ' + el['desc']
        t = tokenize(s)
        db.docs.update({'_id': el['_id']}, {'$set': {'tokens': t}})

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
    db = connectDB()
    ret = db.docs.find()
    for el in ret:
        sim = calcSim(st, el['tokens']) 
        if not sim or sim == 0:
            continue
        rnk = str(np.round(sim, 8))
        rcd = {'title': el['title'], 'desc': el['desc'], 'url': baseURL + el['url']}
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
            print("%s: %s" % (el['title'], el['desc']))
            print("%s (%s)" % (el['url'], key))

def count():
    db = connectDB()
    return db.docs.count()

if __name__ == '__main__':
    search("rendición de cuentas mined 2016")
