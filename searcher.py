from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID 
from whoosh.qparser import QueryParser
import models

DIR = 'indexdir'

def get_schema():
    return Schema(
        title=TEXT(stored=True), 
        path=ID(stored=True), 
        kind=TEXT(stored=True),
        date=TEXT(stored=True), 
        content=TEXT
    )

def update_requests():
    ix = create_in(DIR, get_schema())
    writer = ix.writer()
    req = models.Requests()
    for item in req.list():
        item = req.get(item['_id'])
        writer.add_document(
                title = item['overview'],
                path = str(item['_id']),
                kind = 'request',
                date = item['date'],
                content = item['detail']
        )
    writer.commit()

def update_complains():
    ix = create_in(DIR, get_schema())
    writer = ix.writer()
    print(writer)
    req = models.Complains()
    for item in req.list():
        item = req.get(item['_id'])
        print(item)
        writer.add_document(
                title = item['overview'],
                path = str(item['_id']),
                kind = 'complain',
                date = item['date'],
                content = item['detail']
        )
    writer.commit()

def search(qry):
    ix = open_dir(DIR)
    print(ix.schema)
    with ix.searcher() as searcher:
        query = QueryParser('content', ix.schema).parse(qry)
        print(query)
        res = searcher.search(query)
        if res:
            print(res[0])
        else:
            print('No results')


if __name__ == '__main__':
    search('This')
