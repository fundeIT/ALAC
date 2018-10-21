#!/usr/bin/python
# ticket-searcher.py
# Functions for creating, indexing, and searching on tickets
# 
# These functions are been implemented on Whoosh library, a Python search engine framework.
# Searches are for requests and complains resources.
#
# (2018) Jaime Lopez <jailop AT gmail DOT com>

import unicodedata
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.fields import *
import os.path

# Own libraries
from models import *

def create():
    """
    This function defines an scheme to index the website resouces and creates a storage
    to keep the generated indexes. The storage is a directory called "index". This function
    only have to be run one time, at the beginning.
    """
    schema = Schema(
                title=TEXT(stored=True), 
                path=ID(unique=True, stored=True),
                content=TEXT
            )
    if not os.path.exists("index-ticket"):
        os.mkdir("index-ticket")
    ix = create_in("index-ticket", schema)

def indexer():
    tickets = DB('tickets')
    threads = DB('threads')
    ix = open_dir("index-ticket")
    writer = ix.writer()
    for el in tickets.list():
        ticket_id = str(el['_id'])
        content = el['msg']
        thrs = threads.list(filt={'ticket_id': ticket_id})
        for thr in thrs:
            content += ' ' + thr['msg'] 
        content = str(unicodedata.normalize('NFD', content).encode('ascii', 'ignore').lower())
        print(content)
        writer.update_document(
                title = el['msg'],
                path = "/ticket/%s/%s" % (el['year'], str(el['ticket'])),
                content = content
        )
    writer.commit()

def search(words):
    w = str(unicodedata.normalize('NFD', words).encode('ascii', 'ignore').lower())
    ix = open_dir("index-ticket")
    ret = []
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(w)
        results = searcher.search(query)
        for el in results:
            ret.append(dict(el)) 
    f = open('log-ticket-search.txt', 'a')
    f.write("%s - %s [%d]\n" % (Dates().getDate(), words, len(ret)))
    f.close()
    return ret

if __name__ == '__main__':
    indexer()
