import json
from flask import make_response, request, jsonify
from flask_restful import Resource

import trust
from models import DB, Users

def dbToList(qry):
    ret = []
    for el in qry:
        el['_id'] = str(el['_id'])
        ret.append(el)
    return ret

class PoS(Resource):
    def __init__(self):
        self.db = DB('pos')
    def get(self):
        ret = dbToList(self.db.list())
        return jsonify(ret)
    def post(self):
        rec = request.json
        if rec['_id'] == '':
            del rec['_id']
            rec['_id'] = self.db.new(rec)
            return jsonify(rec['_id'])
        else:
            _id = rec['_id']
            del rec['_id']
            self.db.update(_id, rec) 
            return jsonify(_id)

class User(Resource):
    def __init__(self):
        self.db = Users() 
    def get(self):
        ret = []
        for el in dbToList(self.db.list()):
            if 'deleted' in el.keys() and el['deleted']:
                continue
            if 'password' in el.keys():
                el['password'] = ''
            if not 'pos' in el.keys():
                el['pos'] = ''
            if not 'active' in el.keys():
                el['active'] = True
            ret.append(el)
        return jsonify(ret)
    def post(self):
        rec = request.json
        if rec['_id'] == '':
            del rec['_id']
            rec['_id'] = self.db.new(rec)
            return jsonify(rec['_id'])
        else:
            _id = rec['_id']
            del rec['_id']
            if rec['password'] == '':
                del rec['password']
            self.db.update(_id, rec) 
            return jsonify(_id)
    def delete(self):
        rec = request.json
        self.db.update(rec['_id'], {'deleted': True})
        return jsonify(rec['_id'])


