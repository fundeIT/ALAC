from flask import make_response, jsonify
from flask_restful import Resource, reqparse

from models import *

parser = reqparse.RequestParser()
parser.add_argument('startdate', type=str, help='Starting date')
parser.add_argument('enddate', type=str, help='Ending date')
parser.add_argument('page', type=int, default=0, help='Page number, for pagination')
parser.add_argument('limit', type=int, default=10, help='Records by page')

class apiOffices(Resource):
    def get(self):
        db = DB('offices')
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
        if 'api_key' in request.form.keys():
            api_key = request.form['api_key']
        else:
            return jsonify({'msg': 'Invalid access'})
        if 'enddate' in request.form.keys():
            enddate = request.form['enddate']
        else:
            enddate = datetime.date.today()
        if 'startdate' in request.form.keys():
            startdate = request.form['startdate']
        else:
            startdate = datetime.date.today() - datetime.timedelta(6*365/12)
        if 'page' in request.form.keys():
            page = int(request.form['page'])
        else:
            page = 0
        if 'limit' in request.form.keys():
            limit = int(request.form['limit'])
        else:
            limit = 25
        tickets = DB('tickets')
        threads = DB('threads')
        ret = tickets.collection.find().skip(page * limit).limit(limit)
        res = []
        for el in ret:
            el['_id'] = str(el['_id'])
            aux = threads.collection.find({ 'ticket_id' : el['_id']})
            el['threads'] = []
            for item in aux:
                item['_id'] = str(item['_id'])
                el['threads'].append(item)
            res.append(el)
        return jsonify(res)

class apiRequests(Resource):
    def get(self):
        args = parser.parse_args()
        if args['enddate'] == None:
            args['enddate'] = datetime.date.today()
        if args['startdate'] == None:
            args['startdate'] = datetime.date.today() + datetime.timedelta(6*365/12)
        db = DB('requests')
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
            el['result'] = Requests().results[el['result']]
            el['office'] = Offices().get(el['office_id'])['name']
            updates = Updates().list('request', el['_id'])
            el['updates'] = []
            for upd in updates:
                del upd['_id']
                del upd['source']
                del upd['source_id']
                if 'user_id' in upd.keys():
                    del upd['user_id']
                el['updates'].append(upd)
            docrels = DocRels().list('request', el['_id'])
            el['documents'] = []
            for doc in docrels:
                doc['_id'] = str(doc['_id'])
                doc['path'] = 'https://alac.funde.org/docs/' + doc['_id']
                el['documents'].append(doc)
            res.append(el)
        return jsonify(res)

class apiComplains(Resource):
    def get(self):
        args = parser.parse_args()
        if args['enddate'] == None:
            args['enddate'] = datetime.date.today()
        if args['startdate'] == None:
            args['startdate'] = datetime.date.today() + datetime.timedelta(6*365/12)
        db = DB('complains')
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
        off = Offices()
        for el in ret:
            el['_id'] = str(el['_id'])
            el['url'] = 'https://alac.funde.org/complains/' + el['_id']
            if 'touched' in el.keys():
                del el['touched']
            if el['status'] == '1':
                el['status'] = 'En trámite'
            else:
                el['status'] = 'Cerrada'
            el['result'] = Complains().results[el['result']]
            el['office'] = off.get(el['office_id'])['name']
            el['reviewer'] = off.get(el['reviewer_id'])['name']
            updates = Updates().list('complain', el['_id'])
            el['updates'] = []
            for upd in updates:
                del upd['_id']
                del upd['source']
                del upd['source_id']
                if 'user_id' in upd.keys():
                    del upd['user_id']
                el['updates'].append(upd)
            docrels = DocRels().list('complain', el['_id'])
            el['documents'] = []
            for doc in docrels:
                doc['_id'] = str(doc['_id'])
                doc['path'] = 'https://alac.funde.org/docs/' + doc['_id']
                el['documents'].append(doc)
            res.append(el)
        return jsonify(res)
