from tornado import web, template
import iaipres
from db import DB
from bson.objectid import ObjectId

def search(s):
    n = 25
    i = 0
    r = iaipres.rank(s)
    l = sorted(r, reverse=True)
    res = []
    for key in l:
        if i > n:
            break
        res += r[key]
        i += len(r[key])
    return res

class IAIP(web.RequestHandler):
    def get(self):
        query = self.get_argument('query', '')
        loader = template.Loader("templates/iaip")
        if query != '':
            results = search(query)
        else:
            results = []
        self.write(loader.load("main.html").generate(
            query=query, 
            results=results))

class Res(web.RequestHandler):
    def get(self, ID):
        db = DB('iaipres') 
        loader = template.Loader("templates/iaip")
        rec = db.get({'_id': ObjectId(ID)})
        if not 'similar' in rec:
            results = search(rec['title'] + ' ' + rec['content'])
            similar = [str(item['_id']) for item in results]
            db.update({'_id': ObjectId(ID)}, {'similar': similar})
        else:
            similar = rec['similar']
        length = 6 if len(similar) >= 6 else len(similar)
        results = []
        for i in range(1, length):
            res = db.collection.find_one({'_id': ObjectId(similar[i])})
            if res:
                results.append({'_id': res['_id'], 'title': res['title']})
        print(results)
        self.write(loader.load("res.html").generate(rec=rec, results=results, query=None)) 
