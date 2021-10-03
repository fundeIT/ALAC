#apiclasses.py
# Classes for API responses
# (2020) Fundación Nacional para el Desarrollo

# Importing libraries
from datetime import datetime
from flask import jsonify,json
from flask_restful import request, Resource, reqparse
import models
from bson.json_util import dumps, RELAXED_JSON_OPTIONS, CANONICAL_JSON_OPTIONS
import json

# Setting API global variables
parser = reqparse.RequestParser()
parser.add_argument('startdate', type=str, help='Starting date')
parser.add_argument('enddate', type=str, help='Ending date')
parser.add_argument('page', type=int, default=0, help='Page number, for pagination')
parser.add_argument('limit', type=int, default=10, help='Records by page')

class apiOffices(Resource):
    def get(self):
        db = models.DB('offices')
        ret = db.collection.find()
        res = []
        for el in ret:
            el['_id'] = str(el['_id'])
            if '0' in el.keys():
                del el['0']
            res.append(el)
        return jsonify(res)

class apiTickets(Resource):
    def post(self):
        # Recovering data arguments
        if 'page' in request.form.keys():
            page = int(request.form['page'])
        else:
            page = 0
        if 'limit' in request.form.keys():
            limit = int(request.form['limit'])
        else:
            limit = 25
        # Querying the database
        tickets = models.DB('tickets')
        threads = models.DB('threads')
        ret = tickets.collection.find().skip(page * limit).limit(limit)
        res = []
        for el in ret:
            el['_id'] = str(el['_id'])
            aux = threads.collection.find({'ticket_id' : el['_id']})
            el['threads'] = []
            for item in aux:
                item['_id'] = str(item['_id'])
                el['threads'].append(item)
            res.append(el)
        # Returning the response
        return jsonify(res)

class apiRequests(Resource):
    def get(self):
        args = parser.parse_args()
        if args['enddate'] == None:
            args['enddate'] = datetime.date.today()
        if args['startdate'] == None:
            args['startdate'] = datetime.date.today() + datetime.timedelta(6*365/12)
        db = models.DB('requests')
        ret = db.collection.find({'$query':{
            'date': {
                '$lte': args['enddate'],
                '$gte': args['startdate']
                },
            'status': {
                '$gte': '1',
                '$lte': '2'
                },
        },'$orderby':{'date':-1}},{
        'detail':0,
        'ref':0,
        'comment':0,
        'finish':0,
        'start':0,
        'touched':0,
        'case_id':0,
        'result':0,
        'status':0,
        }).skip(args['page'] * args['limit']).limit(args['limit'])
        res = []
        for el in ret:
            el['_id'] = str(el['_id'])
            el['office'] = models.Offices().get(el['office_id'])['name']
            res.append(el)
        return jsonify(res)

class apiRequestsFull(Resource):
    def get(self):
        args = parser.parse_args()
        if args['enddate'] == None:
            args['enddate'] = datetime.date.today()
        if args['startdate'] == None:
            args['startdate'] = datetime.date.today() + datetime.timedelta(6*365/12)
        db = models.DB('requests')
        ret = db.collection.find({
            'date': {
                '$lte': args['enddate'],
                '$gte': args['startdate']
                },
            'status': {
                '$gte': '1',
                '$lte': '2'
                }
        }).skip(args['page'] * args['limit']).limit(args['limit'])
        res = []
        for el in ret:
            el['_id'] = str(el['_id'])
            el['url'] = 'https://alac.funde.org/requests/' + el['_id']
            if 'touched' in el.keys():
                del el['touched']
            if el['status'] == '1':
                el['status'] = 'En trámite'
            else:
                el['status'] = 'Cerrada'
            el['result'] = models.Requests().results[el['result']]
            el['office'] = models.Offices().get(el['office_id'])['name']
            updates = models.Updates().list('request', el['_id'])
            el['updates'] = []
            for upd in updates:
                del upd['_id']
                del upd['source']
                del upd['source_id']
                if 'user_id' in upd.keys():
                    del upd['user_id']
                el['updates'].append(upd)
            docrels = models.DocRels().list('request', el['_id'])
            el['documents'] = []
            for doc in docrels:
                doc['_id'] = str(doc['_id'])
                doc['path'] = 'https://alac.funde.org/docs/' + doc['_id']
                el['documents'].append(doc)
            res.append(el)
        return jsonify(res)

class apiComplainsFull(Resource):
    def get(self):
        args = parser.parse_args()
        if args['enddate'] == None:
            args['enddate'] = datetime.date.today()
        if args['startdate'] == None:
            args['startdate'] = datetime.date.today() + datetime.timedelta(6*365/12)
        db = models.DB('complains')
        ret = db.collection.find({
            'date': {
                '$lte': args['enddate'],
                '$gte': args['startdate']
                },
            'status': {
                '$gte': '1',
                '$lte': '2'
                }
        }).skip(args['page'] * args['limit']).limit(args['limit'])
        res = []
        off = models.Offices()
        for el in ret:
            el['_id'] = str(el['_id'])
            el['url'] = 'https://alac.funde.org/complains/' + el['_id']
            if 'touched' in el.keys():
                del el['touched']
            if el['status'] == '1':
                el['status'] = 'En trámite'
            else:
                el['status'] = 'Cerrada'
            el['result'] = models.Complains().results[el['result']]
            el['office'] = off.get(el['office_id'])['name']
            el['reviewer'] = off.get(el['reviewer_id'])['name']
            updates = models.Updates().list('complain', el['_id'])
            el['updates'] = []
            for upd in updates:
                del upd['_id']
                del upd['source']
                del upd['source_id']
                if 'user_id' in upd.keys():
                    del upd['user_id']
                el['updates'].append(upd)
            docrels = models.DocRels().list('complain', el['_id'])
            el['documents'] = []
            for doc in docrels:
                doc['_id'] = str(doc['_id'])
                doc['path'] = 'https://alac.funde.org/docs/' + doc['_id']
                el['documents'].append(doc)
            res.append(el)
        return jsonify(res)

class apiRequestStatistics(Resource):
    def get(self,option):
        """
        Option 1 is for grouped by institution results
        Option 2 is for grouped by status results
        """
        if (option == '1'):
            db = models.DB('requests')
            res = db.collection.aggregate([
            {
                "$group" :{'_id':'$office_id', 'frequency':{'$sum':1}}
            },
            	{'$sort':{"frequency":-1}}
            ])
            data = json.loads(dumps(res))
            for row in range(0,5):
                data[row]['institution'] = models.Offices().get(data[row]['_id'])['acronym']
            return data[0:5]
        else:
            db = models.DB('requests')
            res = db.collection.aggregate([{
                '$group': {
                    '_id': {'$substr':['$start',0,4]},
                    'frequency': { "$sum": 1 },
                },
            }])
            data = json.loads(dumps(res))
            return data

class apiComplainStatistics(Resource):
    def get(self,option):
        """
        Option 1 is for grouped by institution results
        Option 2 is for grouped by status results
        """
        if (option == '1'):
            db = models.DB('complains')
            res = db.collection.aggregate([
            {
                "$group" :{'_id':'$office_id', 'frequency':{'$sum':1}}
            },
            	{'$sort':{"frequency":-1}}
            ])
            data = json.loads(dumps(res))
            for row in range(0,5):
                data[row]['institution'] = models.Offices().get(data[row]['_id'])['acronym']
            return data[0:5]
        else:
            db = models.DB('complains')
            res = db.collection.aggregate([{
                '$group': {
                    '_id': {'$substr':['$start',0,4]},
                    'frequency': { "$sum": 1 },
                },
            }])
            data = json.loads(dumps(res))
            return data

class apiRequest(Resource):
    def get(self,request_id):
        request = models.Requests().get(request_id)
        data = json.loads(dumps(request))
        data['office'] = models.Offices().get(data['office_id'])['name']
        data['result'] = models.Requests().results[data['result']]
        if data['status'] == '1':
            data['status'] = 'En trámite'
        else:
            data['status'] = 'Cerrada'
        updates = models.Updates().list('request', request_id)
        data['updates'] = []
        for upd in updates:
            del upd['_id']
            del upd['source']
            del upd['source_id']
            if 'user_id' in upd.keys():
                del upd['user_id']
            data['updates'].append(upd)
        docrels = models.DocRels().list('request', request_id)
        data['documents'] = []
        for doc in docrels:
            doc['_id'] = str(doc['_id'])
            doc['path'] = 'https://alac.funde.org/docs/' + doc['_id']
            data['documents'].append(doc)
        #return dumps([request],json_options=RELAXED_JSON_OPTIONS)
        return data

class apiComplains(Resource):
    def get(self):
        args = parser.parse_args()
        if args['enddate'] == None:
            args['enddate'] = datetime.date.today()
        if args['startdate'] == None:
            args['startdate'] = datetime.date.today() + datetime.timedelta(6*365/12)
        db = models.DB('complains')
        ret = db.collection.find({'$query':{
            'date': {
                '$lte': args['enddate'],
                '$gte': args['startdate']
                },
            'status': {
                '$gte': '1',
                '$lte': '2'
                },
        },'$orderby':{'date':-1}},{
        'detail':0,
        'ref':0,
        'comment':0,
        'finish':0,
        'start':0,
        'touched':0,
        'case_id':0,
        'result':0,
        'status':0,
        'reviewer_id':0,
        }).skip(args['page'] * args['limit']).limit(args['limit'])
        res = []
        off = models.Offices()
        for el in ret:
            el['_id'] = str(el['_id'])
            el['office'] = off.get(el['office_id'])['name']
            res.append(el)
        return jsonify(res)

class apiComplain(Resource):
    def get(self,request_id):
        request = models.Complains().get(request_id)
        data = json.loads(dumps(request))
        data['office'] = models.Offices().get(data['office_id'])['name']
        data['result'] = models.Complains().results[data['result']]
        if data['status'] == '1':
            data['status'] = 'En trámite'
        else:
            data['status'] = 'Cerrada'
        updates = models.Updates().list('complain', request_id)
        data['updates'] = []
        for upd in updates:
            del upd['_id']
            del upd['source']
            del upd['source_id']
            if 'user_id' in upd.keys():
                del upd['user_id']
            data['updates'].append(upd)
        docrels = models.DocRels().list('complain', request_id)
        data['documents'] = []
        for doc in docrels:
            doc['_id'] = str(doc['_id'])
            doc['path'] = 'https://alac.funde.org/docs/' + doc['_id']
            data['documents'].append(doc)
        #return dumps([request],json_options=RELAXED_JSON_OPTIONS)
        return data
