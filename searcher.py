from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
import models

class Searcher:
    def get_schema(self):
        return Schema(
            title=TEXT(stored=True), 
            path=ID(stored=True), 
            kind=TEXT(stored=True),
            date=TEXT(stored=True), 
            content=TEXT
        )
    def update_requests(self):
        ix = create_in("indexdir", self.get_schema())
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
    def test(self):
        ix = create_in("indexdir", schema)
        writer = ix.writer()
        writer.add_document(title='First document', path='/a', date='2018-09-05', content='This is the first document')
        writer.add_document(title='Second document', path='/b', date='2018-09-05', content='This is the second document')
        writer.commit()
    def search(self, qry):
        ix = create_in("indexdir", self.get_schema())
        with ix.searcher() as searcher:
            query = QueryParser('content', ix.schema).parse(qry)
            res = searcher.search(query)
            if res:
                print(res[0])
            else:
                print('No results')


if __name__ == '__main__':
    Searcher().search('listado')
