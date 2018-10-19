# searcher.py
# Functions for creating, indexing, and searching
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
                office=TEXT(stored=True),
                date=TEXT(stored=True), 
                path=ID(unique=True, stored=True),
                kind=TEXT(stored=True), 
                content=TEXT
            )
    if not os.path.exists("index"):
        os.mkdir("index")
    ix = create_in("index", schema)

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
            writer.add_document(
                    title = doc['overview'],
                    office = office,
                    date = doc['date'],
                    path = "/%ss/%s" % (name, str(el['_id'])),
                    kind = name,
                    content = content
            )
    writer.commit()

def indexer():
    store_documents(Requests(), "request")
    store_documents(Complains(), "complain")

def search(words):
    words = str(unicodedata.normalize('NFD', words).encode('ascii', 'ignore').lower())
    ix = open_dir("index")
    ret = []
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(words)
        results = searcher.search(query)
        for el in results:
            ret.append(dict(el)) 
    return ret
