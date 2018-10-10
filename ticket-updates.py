#!/usr/bin/env python
# Get tickets updated during the indicated month
# (2018) Jaime Lopez <jailop AT gmail DOT com>

import sys
from bson.objectid import ObjectId

from models import DB 

def updated(month):
    # month: YYYY-MM
    fout = open('updated.txt', 'w')
    db = DB('threads')
    res = db.collection.find({'date': {'$regex': month}})
    tickets = [item['ticket_id'] for item in res]
    db = DB('tickets')
    for ID in tickets:
        item = db.collection.find_one({'_id': ObjectId(ID)})
        fout.write("%s-%03d\n" % (item['year'], int(item['ticket'])))
    fout.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: missing parameter")
        print("Usage: %s YYYY-MM" % sys.argv[0])
        exit()
    updated(sys.argv[1])
