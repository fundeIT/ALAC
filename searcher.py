#!/usr/bin/python
# searcher.py
# Functions for creating, indexing, and searching
# 
# These functions are been implemented on Whoosh library, a Python search engine framework.
# Searches are for requests and complains resources.
#
# (2018-2021) Jaime Lopez <jailop AT protonmail DOT com>

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
                office=TEXT(stored=True),
                date=TEXT(stored=True), 
                path=ID(unique=True, stored=True),
                kind=TEXT(stored=True), 
                content=TEXT
            )
    if not os.path.exists("index"):
        os.mkdir("index")
    ix = create_in("index", schema)

def store_notes():
    resource = Notes()
    ix = open_dir("index")
    writer = ix.writer()
    list = resource.list()
    for el in list:
        doc = resource.get(el['_id'])
        content = "%s %s" % (doc['title'], doc['content'])
        content = str(unicodedata.normalize('NFD', content).encode('ascii', 'ignore').lower())
        writer.update_document(
                title = doc['title'],
                office = "",
                date = doc['date'],
                path = "/notes/%s" % str(el['_id']),
                kind = "note",
                content = content
        )
    writer.commit()

def store_documents(resource, name):
    ix = open_dir("index")
    writer = ix.writer()
    list = resource.list()
    for el in list:
        doc = resource.get(el['_id'])
        if doc['status'] in ['1', '2']:
            office = Offices().get(doc['office_id'])['name']
            content = "%s %s %s" % (doc['overview'], office, doc['detail'])
            content = str(unicodedata.normalize('NFD', content).encode('ascii', 'ignore').lower())
            writer.update_document(
                    title = doc['overview'],
                    office = office,
                    date = doc['date'],
                    path = "/%ss/%s" % (name, str(el['_id'])),
                    kind = name,
                    content = content
            )
    writer.commit()

def indexer():
    try:
        ix = open_dir("index")
    except:
        create()
    store_documents(Requests(), "request")
    store_documents(Complains(), "complain")
    store_notes()

def search(words):
    w = str(unicodedata.normalize('NFD', words).encode('ascii', 'ignore').lower())
    ix = open_dir("index")
    ret = []
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(w)
        results = searcher.search(query)
        for el in results:
            ret.append(dict(el)) 
    f = open('log-search.txt', 'a')
    f.write("%s - %s [%d]\n" % (Dates().getDate(), words, len(ret)))
    f.close()
    return ret

if __name__ == '__main__':
    # If you run this script, the indexer function is launched.
    # So, a storage must exist, otherwise you'll get an error.
    indexer()
