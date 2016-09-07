import pymongo
from bson.objectid import ObjectId

def dbconn():
    client = pymongo.MongoClient()
    db = client.alac
    return db
    
def emptyDict(keys):
    return {key: '' for key in keys}

# Clases para la consulta y actualización de la base de datos

class Cases:
    keys = ['title', 'overview', 'requester']
    def new(self, case):
        return dbconn().cases.insert_one(case).inserted_id
    def list(self):
        return dbconn().cases.find({}, {'title': 1}).sort('title')
    def get(self, _id):
        return dbconn().cases.find_one({'_id': ObjectId(_id)})
    def update(self, _id, case):
        dbconn().cases.update({'_id': ObjectId(_id)}, {'$set': case})

class Offices:
    keys = ['name', 'acronym', 'officer', 'email', 'phone']
    def new(self, office):
        return dbconn().offices.insert_one(office).inserted_id
    def list(self):
        return dbconn().offices.find({}, {'name': 1, 'acronym': 1}).sort('acronym')
    def get(self, _id):
        return dbconn().offices.find_one({'_id': ObjectId(_id)})
    def update(self, _id, office):
        dbconn().offices.update({'_id': ObjectId(_id)}, {'$set': office})

class Requests:
    keys = ['case_id', 'office_id', 'ref', 'date', 'overview', 'detail', 'status', 'result', 'comment']
    status = ['Borrador', 'En trámite', 'Cerrada']
    results = {
        'ND': 'No definido', 
        'RC': 'Respuesta completa', 
        'RP': 'Respuesta parcial', 
        'SI': 'Solicitud improcedente',
        'DI': 'Diferente información', 
        'RV': 'Reservada', 
        'CF': 'Confidencial', 
        'IN': 'Inexistente', 
        'NC': 'Oficina no competente', 
        'SR': 'Sin respuesta'
    }
    def new(self, req):
        return dbconn().requests.insert_one(req).inserted_id
    def list(self, case_id=None, office_id=None, status=None):
        fields = {'case_id': 1, 'office_id': 1, 'ref': 1, 'date': 1, 'overview': 1}
        if case_id != None:
            return dbconn().requests.find({'case_id': case_id}, fields).sort('date', -1)
        elif office_id != None:
            return dbconn().requests.find({'office_id': office_id}, fields).sort('date', -1)
        elif status != None:
            return dbconn().requests.find({'status': status}, fields).sort('date', -1)
        else:
            return dbconn().requests.find({}, fields).sort('ref')
    def get(self, _id):
        return dbconn().requests.find_one({'_id': ObjectId(_id)})
    def update(self, _id, req):
        dbconn().requests.update({'_id': ObjectId(_id)}, {'$set': req})

class Complains:
    keys = ['case_id', 'office_id', 'ref', 'date', 'overview', 'detail', 'status', 'result', 'comment']
    status = ['Borrador', 'En trámite', 'Cerrada']
    results = {
        'ND': 'No definido', 
        'RF': 'Favorable', 
        'RP': 'Parcial', 
        'RD': 'Desfavorable',
        'NC': 'Oficina no competente', 
        'SR': 'Sin respuesta'
    }
    def new(self, req):
        return dbconn().complains.insert_one(req).inserted_id
    def list(self, case_id=None, office_id=None):
        fields = {'case_id': 1, 'office_id': 1, 'ref': 1, 'date': 1, 'overview': 1}
        if case_id != None:
            return dbconn().complains.find({'case_id': case_id}, fields).sort('ref')
        elif office_id != None:
            return dbconn().complains.find({'office_id': office_id}, fields).sort('ref')
        else:
            return dbconn().complains.find({}, fields).sort('ref')
    def get(self, _id):
        return dbconn().complains.find_one({'_id': ObjectId(_id)})
    def update(self, _id, req):
        dbconn().complains.update({'_id': ObjectId(_id)}, {'$set': req})

class Updates:
    keys = ['source', 'source_id', 'date', 'detail']
    def new(self, update):
        if len(update['detail']) == 0:
                return 0
        return dbconn().updates.insert_one(update).inserted_id 
    def list(self, source, source_id):
        return dbconn().updates.find({'source': source, 'source_id': source_id}).sort('date')


