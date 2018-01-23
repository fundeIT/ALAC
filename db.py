import pymongo
from bson.objectid import ObjectId
import trust

class DB:
    def __init__(self, collection):
        client = pymongo.MongoClient()
        db = client[trust.db_name]
        self.collection = db[collection]
    def new(self, doc):
        _id = str(self.collection.insert_one(doc).inserted_id)
        return _id
    def count(self, sel={}):
        return self.collection.count(sel)
    def list(self, skip=0, limit=10, filt=None, order=1):
        return self.collection.find(filt).sort([('_id', order)]).skip(skip).limit(limit)
    def raw(self):
        return self.collection.find().sort([('_id', 1)])
    def get(self, sel={}):
        return self.collection.find_one(sel)
    def update(self, sel, doc):
        self.collection.update(sel, {'$set': doc})


