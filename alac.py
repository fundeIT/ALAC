from flask import Flask, request, render_template, redirect
import pymongo
from bson.objectid import ObjectId
from markdown import markdown

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


app = Flask(__name__)

# Definición de los controladores

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/cases')
def cases():
    return render_template('caselist.html', cases = Cases().list())

@app.route('/cases/new/', methods=['GET', 'POST'])
def caseNew():
    if request.method == 'POST':
        case = {key: request.form[key] for key in Cases().keys} 
        _id = Cases().new(case)
        if request.referrer != '/cases/new/':
            return redirect(request.referrer)
        else:
            return redirect('/cases') 
    else:
        case = emptyDict(Cases().keys)
        _id = 'new/'
        return render_template('caseform.html', _id=_id, case = case)

@app.route('/cases/<string:_id>', methods=['GET', 'POST'])
def caseDetail(_id):
    if request.method == 'POST':
        case = {key: request.form[key] for key in Cases().keys} 
        Cases().update(_id, case)
        return redirect('/cases/%s' % _id)
    else:
        case = Cases().get(_id)
        requests = Requests().list(case_id=_id)  
        complains = Complains().list(case_id=_id)
        case['overview'] = markdown(case['overview'])
        updates = Updates().list('case', _id)
        advices = Updates().list('advise', _id)
        # for u in updates:
        #    u['detail'] = markdown(u['detail'])
        return render_template('caseshow.html', case = case, requests = requests, complains=complains, updates=updates, advices=advices)

@app.route('/cases/<string:_id>/edit')
def caseEdit(_id):
    if request.method == 'GET':
        case = Cases().get(_id)
        return render_template('caseform.html', _id = _id, case = case)

@app.route('/offices')
def offices():
    return render_template('officelist.html', offices = Offices().list())
    
@app.route('/offices/new/', methods=['GET', 'POST'])
def officeNew():
    if request.method == 'POST':
        office = {key: request.form[key] for key in Offices().keys}
        office['0'] = 'Sin caso asociado'
        _id = Offices().new(office)
        return redirect('/offices')
    else:
        office = emptyDict(Offices().keys)
        _id = 'new/'
        return render_template('officeform.html', _id=_id, office=office)

@app.route('/offices/<string:_id>', methods=['GET', 'POST'])
def officeDetail(_id):
    if request.method == 'POST':
        office = {key: request.form[key] for key in Offices().keys} 
        Offices().update(_id, office)
        return redirect('/offices/%s' % _id)
    else:
        return render_template('officeshow.html', office = Offices().get(_id))

@app.route('/offices/<string:_id>/edit')
def officeEdit(_id):
        return render_template('officeform.html', _id = _id, office = Offices().get(_id))

@app.route('/requests')
def requests():
    r = Requests()
    drafts = r.list(status='0')
    running = r.list(status='1')
    done = r.list(status='2')
    return render_template('requestlist.html', drafts=drafts, running=running, done=done)

@app.route('/requests/new/', methods=['GET', 'POST'])
def requestNew():
    if request.method == 'POST':
        req = {key: request.form[key] for key in Requests().keys}
        _id = Requests().new(req)
        if request.referrer != '/requests/new/':
            return redirect(request.referrer)
        else:
            return redirect('/requests')
    else:
        r = Requests()
        req = emptyDict(r.keys)
        req['result'] = 'ND'
        case_id = request.args.get('case_id')
        if case_id != None:
            req['case_id'] = case_id
        _id = 'new/'
        return render_template('requestform.html', _id=_id, req = req, status = r.status, results = r.results, cases = Cases().list(), offices = Offices().list())

@app.route('/requests/<string:_id>', methods=['GET', 'POST'])
def requestDetail(_id):
    r = Requests()
    if request.method == 'POST':
        req = {key: request.form[key] for key in r.keys}
        r.update(_id, req)
        return redirect('/requests/%s' % _id)
    else:
        req = r.get(_id)
        req['detail'] = markdown(req['detail'])
        req['status'] = r.status[int(req['status'])]
        req['result'] = r.results[req['result']]
        case = Cases().get(req['case_id'])
        office = Offices().get(req['office_id'])
        updates = Updates().list('request', _id)
        return render_template('requestshow.html', _id=_id, req = req, office = office, case = case, updates=updates)

@app.route('/requests/<string:_id>/edit')
def requestEdit(_id):
    r = Requests()
    req = r.get(_id)
    return render_template('requestform.html', _id=_id, req = req, status = r.status, results = r.results, cases = Cases().list(), offices = Offices().list())

@app.route('/updates/new/', methods=['POST'])
def updateNew():
    u = Updates()
    update = {key: request.form[key] for key in u.keys}
    _id = u.new(update)
    return redirect(request.referrer)

@app.route('/complains')
def complains():
    return render_template('complainlist.html', complains = Complains().list())

@app.route('/complains/new/', methods=['GET', 'POST'])
def complainNew():
    if request.method == 'POST':
        complain = {key: request.form[key] for key in Complains().keys}
        _id = Complains().new(complain)
        if request.referrer != '/complainuests/new/':
            return redirect(request.referrer)
        else:
            return redirect('/complains')
    else:
        r = Complains()
        complain = emptyDict(r.keys)
        complain['result'] ='ND'
        case_id = request.args.get('case_id')
        if case_id != None:
            complain['case_id'] = case_id
        _id = 'new/'
        return render_template('complainform.html', _id=_id, complain = complain, status = r.status, results = r.results, cases = Cases().list(), offices = Offices().list())

@app.route('/complains/<string:_id>', methods=['GET', 'POST'])
def complainDetail(_id):
    r = Complains()
    if request.method == 'POST':
        req = {key: request.form[key] for key in r.keys}
        r.update(_id, req)
        return redirect('/complains/%s' % _id)
    else:
        complain = r.get(_id)
        complain['detail'] = markdown(complain['detail'])
        complain['status'] = r.status[int(complain['status'])]
        complain['result'] = r.results[complain['result']]
        case = Cases().get(complain['case_id'])
        office = Offices().get(complain['office_id'])
        updates = Updates().list('complain', _id)
        return render_template('complainshow.html', _id=_id, complain = complain, office = office, case = case, updates=updates)

@app.route('/complains/<string:_id>/edit')
def complainEdit(_id):
    r = Complains()
    complain = r.get(_id)
    return render_template('complainform.html', _id=_id, complain = complain, status = r.status, results = r.results, cases = Cases().list(), offices = Offices().list())

