#!/usr/bin/env python
#
# Get updates from requests and complains
# made during the indicated month
#
# (2018) Jaime Lopez <jailop AT gmail DOT com>

# Python libraries
import sys
from bson.objectid import ObjectId

# Own libraries
from models import DB 

def updated(month):
    fout = open('reqcompupdated.txt', 'w')
    db = DB('updates')
    res = db.collection.find({'date': {'$regex': month}})
    for item in res:
        fout.write("https://alac.funde.org/%ss/%s\n" % (item['source'], item['source_id']))
    fout.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: missing parameter")
        print("Usage: %s YYYY-MM" % sys.argv[0])
        exit()
    updated(sys.argv[1])
