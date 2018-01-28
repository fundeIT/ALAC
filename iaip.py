from tornado import web, template
import iaipres

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
