#!/usr/bin/python
# ticket-searcher.py
# Functions for creating, indexing, and searching on tickets
# 
# These functions are been implemented on Whoosh library, a Python search engine framework.
# Searches are for requests and complains resources.
#
# (2018-2021) Jaime Lopez <jailop AT protonmail DOT com>

import os.path
import unicodedata

# This script uses the Whoosh search engine library
# Documentation: https://whoosh.readthedocs.io/en/latest/

from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.fields import *

# Own libraries
from models import *  # It is used to access the database

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
    counter = 0
    tickets = DB('tickets')
    threads = DB('threads')
    try:
        ix = open_dir("index-ticket")
    except:
        # In case of error, that means the index
        # has not been created
        create()
        ix = open_dir("index-ticket")
    writer = ix.writer()
    for el in tickets.list(limit=-1):
        counter += 1
        ticket_id = str(el['_id'])
        content = el['msg']
        thrs = threads.list(filt={'ticket_id': ticket_id})
        for thr in thrs:
            content += ' ' + thr['msg'] 
        content = str(unicodedata.normalize('NFD', content).encode('ascii', 'ignore').lower())
        writer.update_document(
                title = el['msg'],
                path = "/ticket/%s/%s" % (el['year'], str(el['ticket'])),
                content = content
        )
    writer.commit()
    print("%d documentos actualizados" % counter)

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
