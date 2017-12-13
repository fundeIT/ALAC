import pymongo
import hashlib
import datetime
import trust
from bson.objectid import ObjectId

def dbconn():
    client = pymongo.MongoClient(trust.db_server, trust.db_port)
    db = client[trust.db_name]
    return db
    
def emptyDict(keys):
    return {key: '' for key in keys}

class Dates:
    def __init__(self):
        self.now = datetime.datetime.now()
    def getDate(self):
        return self.now.strftime("%Y-%m-%d")
    def getDatePath(self):
        return self.now.strftime("%Y/%m/")
    def getYear(self):
        return self.now.strftime("%Y")
    def getMonth(self):
        return self.now.strftime("%m")

class DB:
    """It is the basic data connection class. All data models classes will be
    derivated from this base class."""
    def __init__(self, collection):
        client = pymongo.MongoClient()
        db = client[trust.db_name]
        self.collection = db[collection]
    def new(self, doc):
        _id = str(self.collection.insert_one(doc).inserted_id)
        return _id
    def count(self):
        return self.collection.count()
    def list(self, skip=0, limit=25, filt=None):
        return self.collection.find(filt).sort([('_id', 1)]).skip(skip).limit(limit)
    def raw(self):
        return self.collection.find().sort([('_id', 1)])
    def get(self, _id):
        print(_id)
        return self.collection.find_one({'_id': ObjectId(_id)})
    def update(self, _id, doc):
        print(doc)
        self.collection.update({'_id': ObjectId(_id)}, {'$set': doc})

# Clases para la consulta y actualización de la base de datos

def touch(entity, _id):
    if entity == 'case':
        collection = 'cases'
    elif entity == 'office':
        collection = 'offices'
    elif entity == 'request':
        collection = 'requests'
    elif entity == 'complain':
        collection = 'complains'
    elif entity == 'client':
        collection = 'clients'
    else:
        return
    client = pymongo.MongoClient()
    db = client[trust.db_name]
    collection = db[collection]
    res = collection.update({'_id': ObjectId(_id)}, 
            {'$currentDate': {'touched': True}})
    s = collection.find_one({'_id': _id})
    return

class Cases:
    keys = ['title', 'overview', 'requester']
    def new(self, case):
        return dbconn().cases.insert_one(case).inserted_id
    def list(self):
        return dbconn().cases.find({}, 
                {'title': 1, 'touched': 1}).sort('touched', -1)
    def get(self, _id):
        return dbconn().cases.find_one({'_id': ObjectId(_id)})
    def update(self, _id, case):
        touch('case', _id)
        dbconn().cases.update({'_id': ObjectId(_id)}, {'$set': case})

class Offices:
    keys = ['name', 'acronym', 'officer', 'email', 'phone', 'notes']
    def new(self, office):
        return dbconn().offices.insert_one(office).inserted_id
    def list(self):
        return dbconn().offices.find({}, {'name': 1, 
	    'acronym': 1}).sort('acronym')
    def get(self, _id):
        if _id == '':
            return emptyDict(self.keys)
        office = dbconn().offices.find_one({'_id': ObjectId(_id)})
        if not 'notes' in office:
            office['notes'] = ''
        return office
    def update(self, _id, office):
        dbconn().offices.update({'_id': ObjectId(_id)}, {'$set': office})

class Requests:
    keys = ['case_id', 'office_id', 'ref', 'date', 'overview', 'detail', 
            'start', 'finish', 'status', 'result', 'comment']
    status = ['Borrador', 'En trámite', 'Cerrada', 'No tramitada']
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
        fields = {
            'case_id': 1, 
            'office_id': 1, 
            'ref': 1, 
            'date': 1,
            'overview': 1,
            'touched': 1
        }
        if case_id != None:
            return dbconn().requests.find({'case_id': case_id}, 
                fields).sort('touched', -1)
        elif office_id != None:
            return dbconn().requests.find({'office_id': office_id}, fields).sort('touched', -1)
        elif status != None:
            return dbconn().requests.find({'status': status}, fields).sort('touched', -1)
        else:
            return dbconn().requests.find({}, fields).sort('touched', -1)
    def get(self, _id):
        request = dbconn().requests.find_one({'_id': ObjectId(_id)})
        if not 'start' in request:
            request['start'] = ''
            request['start'] = ''
        if not 'finish' in request:
            request['finish'] = ''
        return request
    def update(self, _id, req):
        touch('request', _id)
        dbconn().requests.update({'_id': ObjectId(_id)}, {'$set': req})

class Clients:
    keys = ['name', 'alias', 'age', 'sex', 'kind', 'org', 
            'vulnerable', 'rol', 'city', 'tel', 'email', 'notes']
    kinds = ['Otro', 'Empleado público', 'Empresario', 'Organización social',
            'Periodista', 'Ciudadano/a', 'Academia']
    vulnerables = ['Ninguno', 'Mujeres', 'Jóvenes', 'Tercera edad', 
            'Personas con discapacidad', 'Pueblos originarios', 'Migrante',
            'LGBTI']
    ages = ['Menos de 30 años', 'De 30 años o más y menor de 45',
            'De 45 años o más y menor de 60', 'De 60 años o más']
    def new(self, doc):
        return dbconn().clients.insert_one(doc).inserted_id
    def list(self, case_id=None, office_id=None, status=None):
        fields = {
            'name': 1, 
            'city': 1 
        }
        return dbconn().clients.find().sort('touched', -1)
    def get(self, _id):
        return dbconn().clients.find_one({'_id': ObjectId(_id)})
    def update(self, _id, doc):
        touch('client', _id)
        dbconn().clients.update({'_id': ObjectId(_id)}, {'$set': doc})

class Complains:
    keys = [
        'case_id', 
        'office_id',    # Office that is been complained
        'reviewer_id',  # Office that is reviewing the case
        'ref',          
        'date', 
        'overview', 
        'detail', 
        'start',        # Starting date when formal procedure begin
        'finish',       # Ending date when formal procedere become closed
        'status', 
        'result', 
        'comment'
    ]
    status = ['Borrador', 'En trámite', 'Cerrada']
    results = {
        'ND': 'No definido', 
        'RF': 'Favorable', 
        'RP': 'Parcial', 
        'RD': 'Desfavorable',
        'NC': 'Oficina no competente', 
        'SR': 'Sin respuesta',
        'DS': 'Desistimiento'
    }
    def new(self, req):
        return dbconn().complains.insert_one(req).inserted_id
    def list(self, case_id=None, office_id=None, status=None):
        fields = {'case_id': 1, 'office_id': 1, 'ref': 1, 'date': 1, 'overview': 1, 'touched': 1}
        if case_id != None:
            return dbconn().complains.find({'case_id': case_id}, fields).sort('touched', -1)
        elif office_id != None:
            return dbconn().complains.find({'office_id': office_id}, fields).sort('touched', -1)
        elif status != None:
            return dbconn().complains.find({'status': status}, fields).sort('touched', -1)
        else:
            return dbconn().complains.find({}, fields).sort('touched', -1)
    def get(self, _id):
        complain = dbconn().complains.find_one({'_id': ObjectId(_id)})
        for key in ['reviewer_id', 'start', 'finish']:
            if not key in complain:
                complain[key] = ''
        return complain
    def update(self, _id, req):
        touch('complain', _id)
        dbconn().complains.update({'_id': ObjectId(_id)}, {'$set': req})

class Updates:
    keys = ['source', 'source_id', 'date', 'detail']
    def new(self, update):
        if len(update['detail']) == 0:
                return 0
        _id = dbconn().updates.insert_one(update).inserted_id 
        touch(update['source'], update['source_id'])
        return _id
    def list(self, source, source_id):
        return dbconn().updates.find({'source': source, 
            'source_id': source_id}).sort('date')
    def remove(self, _id):
        return dbconn().updates.remove({'_id': ObjectId(_id)})

class Users:
    keys = ['name', 'email', 'kind', 'password']
    kinds = {
        'GSS': 'Invitado', 
        'USR': 'Editor', 
        'MNG': 'Revisor', 
        'OPR': 'Operador'
    }
    def encrypt(self, password):
        m = hashlib.md5()
        m.update(password.encode('utf-8'))
        return m.digest()
    def new(self, user):
        user['password'] = self.encrypt(user['password']) 
        return dbconn().users.insert_one(user).inserted_id
    def get(self, _id):
        return dbconn().users.find_one({'_id': ObjectId(_id)})
    def getByName(self, name):
        return dbconn().users.find_one({'name': name})
    def list(self):
        fields = {'name': 1, 'email': 1, 'kind': 1}
        return dbconn().users.find({}, fields).sort('name')
    def update(self, _id, user):
        if 'password' in user:
            user['password'] = self.encrypt(user['password'])
        dbconn().users.update({'_id': ObjectId(_id)}, {'$set': user})
    def checkPassword(self, _id, password):
        user = self.get(_id)
        if user['password'] == self.encrypt(password):
            return True
        else:
            return False
    def changePassword(self, _id, oldPassword, newPassword):
        if self.checkPassword(_id, oldPassword):
            dbconn().users.update({'_id': ObjectId(_id)}, {'$set': userPass})
            return True
        else:
            return False
    def login(self, email, password):
        user = dbconn().users.find_one({'email': email})
        if user != None:
            if self.checkPassword(user['_id'], password):
                return user
            else:
                return None
        return None

class Documents:
    keys = ['title', 'overview', 'tags', 'date', 'path', 'public']
    def new(self, doc):
        return dbconn().docs.insert_one(doc).inserted_id
    def list(self, public=False):
        if public:
            return dbconn().docs.find({'public': 'on'}).sort('date', -1)
        else:
            return dbconn().docs.find().sort('date', -1)
    def get(self, _id):
        return dbconn().docs.find_one({'_id': ObjectId(_id)})
    def update(self, _id, doc):
        dbconn().docs.update({'_id': ObjectId(_id)}, {'$set': doc})

class DocRels:
    keys = ['source', 'source_id', 'doc_id']
    def new(self, docrel):
        touch(docrel['source'], docrel['source_id'])
        return dbconn().docrels.insert_one(docrel).inserted_id 
    def list(self, source, source_id):
        # Getting document IDs related with the source
        temp = dbconn().docrels.find({'source': source, 
            'source_id': source_id}).sort('doc_id')
        # Based on their IDs, getting documents related with the source
        docs = [Documents().get(dr['doc_id']) for dr in temp]
        return docs

class Rights:
    keys = ['source', 'source_id', 'user_id']
    def new(self, right):
        return dbconn().rights.insert_one(right).inserted_id
    def lookup(self, right):
        # right['source_id'] = ObjectId(right['source_id'])
        return dbconn().rights.find_one(right)
    def listByUser(self, user_id, source):
        cursor = dbconn().rights.find({'source': source, 'user_id': user_id})
        source_list = None
        if source == 'request':
            source_list = [Requests().get(element['source_id']) 
                    for element in cursor]
        elif source == 'complain':
            source_list = [Complains().get(element['source_id']) 
                    for element in cursor]
        elif source == 'note':
            source_list = [Notes().get(element['source_id']) 
                    for element in cursor]
        return source_list
    def listBySource(self, source, source_id):
        cursor = dbconn().rights.find({'source': source, 'source_id':
            source_id})
        users_list = [Users().get(element['user_id']) for element in cursor]
        return users_list

class Notes:
    keys = ['title', 'date', 'content', 'tags']
    def new(self, note):
        return dbconn().notes.insert_one(note).inserted_id
    def list(self):
        return dbconn().notes.find().sort('date', -1)
    def get(self, _id):
        return dbconn().notes.find_one({'_id': ObjectId(_id)})
    def update(self, _id, note):
        dbconn().notes.update({'_id': ObjectId(_id)}, {'$set': note})
        
def newCounter(kind, year):
    counter = 1
    client = pymongo.MongoClient()
    db = client[trust.db_name]
    rec = db.counters.find_one({'year': year, 'kind': kind})
    if (not rec):
        db.counters.insert_one({'year': year, 'kind': kind, 'value': counter})
    else:
        _id = rec['_id']
        counter = rec['value'] + 1
        db.counters.update({'_id': _id}, {'$set': {'year': year, 'kind': kind, 'value': counter}})
    return counter


