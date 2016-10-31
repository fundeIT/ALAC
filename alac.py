from flask import Flask, request, render_template, redirect, session, send_file
from werkzeug.utils import secure_filename
from markdown import markdown
import os
from models import *
import trust

app = Flask(__name__)
app.secret_key = trust.secret_key
app.config['UPLOAD_FOLDER'] = trust.docs_path

ALLOWED_EXTENSIONS = set(['pdf', 'docx', 'xlsx'])

def uploadFile(docfile):
    docfile.filename = secure_filename(docfile.filename)
    d = Dates()
    path = app.config['UPLOAD_FOLDER'] + '/' + d.getYear()
    if not os.path.exists(path):
        os.makedirs(path)
    path += '/' + d.getMonth()
    if not os.path.exists(path):
        os.makedirs(path)
    path += '/' + secure_filename(docfile.filename)
    if not os.path.exists(path):
        docfile.save(path)
        return path 
    else:
        return None

def replaceOfficeinRequests(requests):
    """It appends a new field to each record with the name of the office
    to which was asked for information"""
    o = Offices()
    mod = []
    for req in requests:
        req['office'] = o.get(req['office_id'])['name']
        mod.append(req)
    return mod

def joinUserData(items):
    u = Users()
    mod = []
    for item in items:
        if 'user_id' in item:
            item['user_name'] = u.get(item['user_id'])['name']
        else:
            item['user_name'] = ''
        mod.append(item)
    return mod

def getRegistedUser():
    if 'user' in session:
        return session['user']
    else:
        return {}

def hasRight(source, source_id, categories):
    if 'user' in session:
        user = session['user']
        right = {
            'source': source,
            'source_id': str(source_id),
            'user_id': user['_id']
        }
        has_right = Rights().lookup(right) or user['kind'] in categories 
        return has_right
    else:
        return False

# Controllers

@app.route('/')
def index():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    return render_template('index.html', who=user) 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users().login(email, password)
        if user:
            user['_id'] = str(user['_id'])
            session['user'] = user
            return redirect('/')
        else:
            message = 'Usuario no registrado o contraseña incorrecta'
            return render_template('login.html', message=message, who={})
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    return render_template('login.html', message=None, who=user)

@app.route('/logout')
def logout():
    del session['user']
    return redirect('/')

@app.route('/cases')
def cases():
    if not 'user' in session:
        user = {}
    else:
        user = session['user']
    return render_template('caselist.html', cases = Cases().list(), who=user)

@app.route('/cases/new/', methods=['GET', 'POST'])
def caseNew():
    if not 'user' in session:
        return redirect('/cases')
    user = session['user']
    if request.method == 'POST':
        case = {key: request.form[key] for key in Cases().keys} 
        _id = Cases().new(case)
        if request.referrer != '/cases/new/':
            return redirect('/cases/%s' % str(_id))
        else:
            return redirect('/cases') 
    else:
        case = emptyDict(Cases().keys)
        _id = 'new/'
        return render_template('caseform.html', _id=_id, case = case, 
            who=user)

@app.route('/cases/<string:_id>', methods=['GET', 'POST'])
def caseDetail(_id):
    if request.method == 'POST':
        if 'user' in session:
            case = {key: request.form[key] for key in Cases().keys} 
            Cases().update(_id, case)
        return redirect('/cases/%s' % _id)
    else:
        case = Cases().get(_id)
        requests = replaceOfficeinRequests(Requests().list(case_id=_id))
        complains = replaceOfficeinRequests(Complains().list(case_id=_id))
        case['overview'] = markdown(case['overview'])
        advices = Updates().list('advise', _id)
        docrels = DocRels().list('case', _id)
        docs = Documents().list()
        return render_template('caseshow.html', 
                case=case,
                requests=requests, 
                complains=complains, 
                updates=joinUserData(Updates().list('case', _id)), 
                advices=advices, 
                docs=docs, 
                docrels=docrels, 
                date=Dates().getDate(),
                has_right = hasRight('case', _id, ['OPR', 'MNR', 'USR']),
                who=getRegistedUser())

@app.route('/cases/<string:_id>/edit')
def caseEdit(_id):
    if not 'user' in session:
        return redirect('/cases/%s' % _id)
    if request.method == 'GET':
        case = Cases().get(_id)
        return render_template('caseform.html', _id = _id, case = case, 
            who=session['user'])

@app.route('/offices')
def offices():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    return render_template('officelist.html', offices = Offices().list(), 
        who=user)
    
@app.route('/offices/new/', methods=['GET', 'POST'])
def officeNew():
    if not 'user' in session:
        return redirect('/offices')
    user = session['user']
    if request.method == 'POST':
        office = {key: request.form[key] for key in Offices().keys}
        office['0'] = 'Sin caso asociado'
        _id = Offices().new(office)
        return redirect('/offices')
    else:
        office = emptyDict(Offices().keys)
        _id = 'new/'
        return render_template('officeform.html', _id=_id, office=office, 
            who=user)

@app.route('/offices/<string:_id>', methods=['GET', 'POST'])
def officeDetail(_id):
    if request.method == 'POST':
        office = {key: request.form[key] for key in Offices().keys} 
        Offices().update(_id, office)
        return redirect('/offices/%s' % _id)
    else:
        office = Offices().get(_id)
        office['notes'] = markdown(office['notes'])
        requests = replaceOfficeinRequests(Requests().list(office_id=_id))
        complains = replaceOfficeinRequests(Complains().list(office_id=_id))
        updates = joinUserData(Updates().list('office', _id))
        return render_template('officeshow.html', 
                requests=requests,
                complains=complains, 
                office=office, 
                updates=updates, 
                date=Dates().getDate(),
                has_right = hasRight('case', _id, ['OPR', 'MNR', 'USR']),
                who=getRegistedUser())

@app.route('/offices/<string:_id>/edit')
def officeEdit(_id):
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    return render_template('officeform.html', _id = _id, office = Offices().get(_id), who=user)

@app.route('/requests')
def requests():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    r = Requests()
    drafts = replaceOfficeinRequests(r.list(status='0'))
    running = replaceOfficeinRequests(r.list(status='1'))
    done = replaceOfficeinRequests(r.list(status='2'))
    return render_template('requestlist.html', 
            drafts=drafts,
            running=running,
            done=done,
            who=user)

@app.route('/requests/new/', methods=['GET', 'POST'])
def requestNew():
    if not 'user' in session:
        return redirect('/requests')
    user = session['user']
    if request.method == 'POST':
        req = {key: request.form[key] for key in Requests().keys}
        _id = Requests().new(req)
        right = {
            'source': 'request',
            'source_id': str(_id),
            'user_id': user['_id']
        }
        Rights().new(right)
        d = Dates().getDate()
        msg = 'Petición creada'
        update = {
                'source': 'request',
                'source_id': str(_id),
                'date': d,
                'detail': msg,
                'user_id': str(user['_id'])
        }
        Updates().new(update)
        return redirect('/requests/%s' % str(_id))
    else:
        r = Requests()
        req = emptyDict(r.keys)
        req['date'] = Dates().getDate()
        req['result'] = 'ND'
        req['status'] = '0'
        case_id = request.args.get('case_id')
        if case_id != None:
            req['case_id'] = case_id
        _id = 'new/'
        return render_template('requestform.html', _id=_id, req = req, 
            status = r.status, results = r.results, cases = Cases().list(), 
            offices = Offices().list(), who=session['user'])

@app.route('/requests/<string:_id>', methods=['GET', 'POST'])
def requestDetail(_id):
    """
    This section show an specific request.
    It has options to append updates and documents.
    """
    # Checking privileges
    has_right = hasRight('request', _id, ['OPR', 'MNR', 'USR'])
    r = Requests() # Object used to access request methods
    if request.method == 'POST':
        if has_right:
            req = {key: request.form[key] for key in r.keys}
            r.update(_id, req)
        return redirect('/requests/%s' % _id)
    else: # It's GET
        req = r.get(_id)
        req['detail'] = markdown(req['detail'])
        req['status'] = r.status[int(req['status'])]
        req['result'] = r.results[req['result']]
        req['comment'] = markdown(req['comment'])
        if req['case_id']:
            case = Cases().get(req['case_id'])
        else:
            case = {}
        office = Offices().get(req['office_id'])
        updates = Updates().list('request', _id)
        updates_mod = []
        for element in updates:
            element['detail'] = markdown(element['detail'])
            if 'user_id' in element:
                u = Users().get(element['user_id'])
                if u:
                    element['user_name'] = u['name']
            updates_mod.append(element)
        docrels = DocRels().list('request', _id)
        docs = Documents().list()
        return render_template('requestshow.html', 
                _id=_id, 
                req=req, 
                office=office, 
                case=case, 
                updates=updates_mod,
                docrels=docrels, 
                docs=docs, 
                has_right=has_right, 
                date=Dates().getDate(),
                who=getRegistedUser())

@app.route('/requests/<string:_id>/edit')
def requestEdit(_id):
    if not 'user' in session:
        return redirect('/requests/%s' % _id)
    user = session['user']
    if not user['kind'] in ['OPR', 'USR']:
        return redirect('/requests/%s' % _id)
    r = Requests()
    req = r.get(_id)
    # if int(req['status']) == 2:
    #    return redirect('/requests/%s' % _id)
    users_right = Rights().listBySource('request', _id)
    users_list = Users().list()
    return render_template('requestform.html', _id=_id, req=req, status=r.status, results=r.results, cases = Cases().list(), offices = Offices().list(), users_right=users_right, users_list=users_list, who=user)

@app.route('/requests/<string:_id>/forward', methods=['GET'])
def forwardRequest(_id):
    r = Requests()
    req = r.get(_id)
    if int(req['status']) != 0:
        return redirect('/requests/%s' % _id)
    if not 'user' in session:
        return redirect('/requests/%s' % _id)
    user = session['user']
    right = {
            'source': 'request',
            'source_id': str(_id),
            'user_id': user['_id']
    }
    has_right = Rights().lookup(right) or user['kind'] in ['OPR', 'MNR']
    if has_right:
        d = Dates().getDate()
        req['status'] = '1'
        req['start'] = d
        r.update(_id, req)
        msg = 'Petición pasa de borrador a en trámite'
        update = {
                'source': 'request',
                'source_id': _id,
                'date': d,
                'detail': msg,
                'user_id': str(user['_id'])
        }
        Updates().new(update)
    return redirect('/requests/%s' % _id)

@app.route('/requests/<string:_id>/close', methods=['GET', 'POST'])
def closeRequest(_id):
    r = Requests()
    req = r.get(_id)
    if int(req['status']) != 1:
        return redirect('/requests/%s' % _id)
    if not 'user' in session:
        return redirect('/requests/%s' % _id)
    user = session['user']
    right = {
            'source': 'request',
            'source_id': str(_id),
            'user_id': user['_id']
    }
    has_right = Rights().lookup(right) or user['kind'] in ['OPR', 'USR', 'MNR']
    if not has_right:
        return redirect('/requests/%s' % _id)
    if request.method == 'GET':
        req['result'] = r.results[req['result']]
        return render_template('requestclose.html', _id=_id, req=req, results=r.results,
                referrer=request.referrer, who=user)
    else:
        d = Dates().getDate()
        req['status'] = '2'
        req['result'] = request.form['result']
        req['comment'] = request.form['comment']
        req['finish'] = d 
        r.update(_id, req)
        msg = 'Petición pasa a cerrada'
        update = {
                'source': 'request',
                'source_id': _id,
                'date': d,
                'detail': msg,
                'user_id': str(user['_id'])
        }
        Updates().new(update)
        referrer = request.form['referrer']
        return redirect('/requests/%s' % _id)

@app.route('/updates/new/', methods=['POST'])
def updateNew():
    if 'user' in session:
        user = session['user']
        u = Updates()
        update = {key: request.form[key] for key in u.keys}
        update['user_id'] = request.form['user_id'] 
        _id = u.new(update)
    return redirect(request.referrer)

@app.route('/updates/<string:_id>/delete', methods=['POST'])
def deleteUpdate(_id):
    if not 'user' in session:
        return redirect(request.referrer)
    user = session['user']
    if user['kind'] != 'OPR':
        return redirect(request.referrer)
    Updates().remove(_id)
    return redirect(request.referrer)

@app.route('/complains')
def complains():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    complains = Complains()
    drafts = replaceOfficeinRequests(complains.list(status='0'))
    running = replaceOfficeinRequests(complains.list(status='1'))
    done = replaceOfficeinRequests(complains.list(status='2'))
    return render_template('complainlist.html', drafts=drafts, running=running,
        done=done, who=user)

@app.route('/complains/new/', methods=['GET', 'POST'])
def complainNew():
    if not 'user' in session:
        return redirect('/complains')
    user = session['user']
    if request.method == 'POST':
        complain = {key: request.form[key] for key in Complains().keys}
        _id = Complains().new(complain)
        right = {
            'source': 'complain',
            'source_id': str(_id),
            'user_id': user['_id']
        }
        Rights().new(right)
        return redirect('/complains')
    else:
        r = Complains()
        complain = emptyDict(r.keys)
        complain['result'] ='ND'
        case_id = request.args.get('case_id')
        if case_id != None:
            complain['case_id'] = case_id
        _id = 'new/'
        o = Offices()
        offices = o.list()
        reviewers = o.list()
        return render_template('complainform.html', _id=_id, complain=complain,
            status = r.status, results = r.results, cases = Cases().list(),
            offices = offices, reviewers = reviewers, who=session['user'])

@app.route('/complains/<string:_id>', methods=['GET', 'POST'])
def complainDetail(_id):
    if 'user' in session:
        user = session['user']
        right = {
            'source': 'complain',
            'source_id': _id,
            'user_id': user['_id']
        }
        has_right = Rights().lookup(right) or user['kind'] in ['OPR', 'MNR', 'USR']
    else:
        user = {}
        has_right = False
    has_right = hasRight('complain', _id, ['OPR', 'MNR', 'USR'])
    r = Complains()
    if request.method == 'POST':
        if has_right:
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
        reviewer = Offices().get(complain['reviewer_id'])
        updates = joinUserData(Updates().list('complain', _id))
        updates_mod = []
        for u in updates:
           u['detail'] = markdown(u['detail'])
           updates_mod.append(u)
        docrels = DocRels().list('complain', _id)
        docs = Documents().list()
        return render_template('complainshow.html', 
                _id=_id, 
                complain=complain,
                office=office,
                case=case, 
                updates=updates_mod,
                reviewer=reviewer, 
                docrels=docrels, 
                docs=docs, 
                date=Dates().getDate(),
                who=getRegistedUser(),
            has_right=has_right)

@app.route('/complains/<string:_id>/edit')
def complainEdit(_id):
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    r = Complains()
    complain = r.get(_id)
    o = Offices()
    offices = o.list()
    reviewers = o.list()
    users_right = Rights().listBySource('complain', _id)
    users_list = Users().list()
    return render_template('complainform.html', _id=_id, complain=complain, status=r.status, results = r.results, cases=Cases().list(), offices=offices, reviewers=reviewers, users_right=users_right, users_list=users_list, who=user)

@app.route('/users')
def users():
    if not 'user' in session:
        return redirect('/')
    else:
        return render_template('userlist.html', users=Users().list(), who=session['user'])

@app.route('/users/new/', methods=['GET', 'POST'])
def userNew():
    if not 'user' in session:
        return redirect('/')
    _id = 'new/'
    u = Users()
    if request.method == 'POST':
        user = {key: request.form[key] for key in u.keys}
        password1 = request.form['password1']
        if password1 == user['password']:
            u.new(user)
            return redirect('/users')
        else:
            user['password'] = ''
            message = 'Las contraseñas deben ser iguales. Verifique.'
            return render_template('userform.html', 
                _id = _id, 
                user = user, 
                message = message, 
                password1 = '', 
                kinds = u.kinds, 
                who = session['user']
            )
    else:
        user = emptyDict(u.keys)
        return render_template('userform.html', _id=_id, user=user, message='', password1='', kinds=u.kinds, who=session['user'])

@app.route('/users/<string:_id>', methods=['GET', 'POST'])
def userDetail(_id):
    if not 'user' in session:
        return redirect('/')
    u = Users()
    if request.method == 'POST':
        user = {key: request.form[key] for key in u.keys}
        if user['password'] != '':
            password1 = request.form['password1']
            if password1 == user['password']:
                u.update(_id, user)
                return redirect('/users/%s' % _id)
            else:
                user['password'] = ''
                message = 'Las contraseñas deben ser iguales. Verifique.'
                return render_template('userform.html', _id=_id, user=user,
                        message=message, password1='', kinds=u.kinds, who=session['user'])
        else:
            del user['password']
            u.update(_id, user)
            return redirect('/users/%s' % _id)
    else:
        user = u.get(_id)
        user['password'] = ''
        return render_template('userform.html', _id=_id, user=user, 
            message='', password1='', kinds=u.kinds, who=session['user'])

@app.route('/docs')
def documents():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    docs = Documents().list()
    return render_template('doclist.html', docs=docs, who=user) 

@app.route('/docs/new/', methods=['GET', 'POST'])
def newDoc():
    if not 'user' in session:
        redirect('/docs')
    _id = 'new/'
    message = ''
    if request.method == 'POST':
        d = Dates()
        doc = {}
        doc['title'] = request.form['title']
        doc['overview'] = request.form['overview']
        doc['tags'] = request.form['tags']
        doc['date'] = request.form['date']
        docfile = request.files['file']
        docfile.filename = secure_filename(docfile.filename)
        path = app.config['UPLOAD_FOLDER'] + '/' + d.getYear()
        if not os.path.exists(path):
            os.makedirs(path)
        path += '/' + d.getMonth()
        if not os.path.exists(path):
            os.makedirs(path)
        path += '/' + docfile.filename
        if not os.path.exists(path):
            docfile.save(path)
            doc['path'] = d.getDatePath() + docfile.filename 
            Documents().new(doc)
            return redirect('/docs')
        else:
            message = 'File %s exists' % docfile.filename
            return render_template('docform.html', _id=_id, doc=doc,
                who=session['user'], message=message)
    else:
        doc = emptyDict(Documents().keys)
        return render_template('docform.html', _id=_id, doc=doc,
            who=session['user'], message=message)

@app.route('/docs/<string:_id>/edit', methods=['GET', 'POST'])
def docDetail(_id):
    if not 'user' in session:
        return redirect('/docs')
    d = Documents()
    if request.method == 'POST':
        doc = {key: request.form[key] for key in d.keys}
        del doc['path']
        d.update(_id, doc)
        return redirect(request.form['referrer'])
    else:
        doc = d.get(_id)
        return render_template('docform.html', _id=_id, doc=doc,
            referrer=request.referrer, who=session['user'], message='')

@app.route('/docs/<string:_id>')
def docDownload(_id):
    d = Documents()
    doc = d.get(_id)
    path = app.config['UPLOAD_FOLDER'] + '/' + doc['path']
    filename = path.split('/')[-1]
    return send_file(path, as_attachment=True, attachment_filename=filename)

@app.route('/docrels/new/', methods=['POST'])
def docrelNew():
    if not 'user' in session:
        return redirect(request.referrer)
    else:
        dr = DocRels()
        docrel = {key: request.form[key] for key in dr.keys}
        l = len(docrel['doc_id'])
        p = docrel['doc_id'].rfind('/')
        if p > 0:
            p += 1
            docrel['doc_id'] = docrel['doc_id'][p:l]
        doc = Documents().get(docrel['doc_id'])
        if doc['path']:
            _id = dr.new(docrel)
        return redirect(request.referrer)

@app.route('/docrels/newdoc/', methods=['POST'])
def docrelNewWithDoc():
    if not 'user' in session:
        return redirect(request.referrer)
    else:
        doc = {}
        doc['title'] = request.form['prefix'] + ' - ' + request.form['title']
        doc['overview'] = ''
        doc['tags'] = ''
        doc['date'] = request.form['date'] 
        docfile = request.files['file']
        path = uploadFile(docfile)
        if path:
            doc['path'] = Dates().getDatePath() + docfile.filename 
            doc_id = Documents().new(doc)
            docrel = {}
            docrel['source'] = request.form['source']
            docrel['source_id'] = request.form['source_id']
            docrel['doc_id'] = doc_id
            DocRels().new(docrel)
        return redirect("%s#documents" % request.referrer)

@app.route('/rights/new/', methods=['POST'])
def newRight():
    if not 'user' in session:
        return redirect(request.referrer)
    right = {}
    right['source'] = request.form['source'] 
    right['source_id'] = request.form['source_id']
    right['user_id'] = request.form['user_id']
    Rights().new(right)
    return redirect(request.referrer)

@app.route('/mine')
def mine():
    if not 'user' in session:
        return redirect('/')
    user = session['user']
    r = Rights()
    requests = replaceOfficeinRequests(r.listByUser(user['_id'], 'request'))
    complains = replaceOfficeinRequests(r.listByUser(user['_id'], 'complain'))
    notes = r.listByUser(user['_id'], 'note')
    return render_template('minelist.html', 
            requests=requests,
            complains=complains, notes=notes, who=session['user'])

@app.route('/notes')
def notes():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    notes = Notes().list()
    return render_template('notelist.html', notes=notes, who=user)

@app.route('/notes/new/', methods=['GET', 'POST'])
def newNote():
    if not 'user' in session:
        return redirect('/notes')
    user = session['user']
    n = Notes()
    if request.method == 'POST':
        note = {key: request.form[key] for key in Notes().keys}
        _id = n.new(note)
        right = {
                'source': 'note',
                'source_id': str(_id),
                'user_id': user['_id']
                }
        Rights().new(right)
        return redirect('/notes')
    else:
        note = emptyDict(n.keys)
        note['date'] = Dates().getDate()
        _id = 'new/'
        return render_template('noteform.html', _id=_id, note=note, who=user)

@app.route('/notes/<string:_id>', methods=['GET', 'POST'])
def detailNote(_id):
    if not 'user' in session:
        user = {} 
        has_right = False
    else:
        user = session['user']
        user_id = user['_id']
        right = {
                'source': 'note',
                'source_id': _id,
                'user_id': user_id
        }
        has_right = Rights().lookup(right) or user['kind'] in ['OPR', 'MNR', 'USR']
    n = Notes()
    if request.method == 'POST':
        if has_right:
            note = {key: request.form[key] for key in n.keys}
            n.update(_id, note)
        return redirect('/notes/%s' % _id)
    else:
        note = n.get(_id)
        note['content'] = markdown(note['content'])
        return render_template('noteshow.html', _id=_id, note=note, who=user)

@app.route('/notes/<string:_id>/edit')
def editNote(_id):
    if not 'user' in session:
        return redirect('/notes')
    n = Notes()
    note = n.get(_id)
    users_right = Rights().listBySource('note', _id)
    print(users_right)
    users_list = Users().list()
    return render_template('noteform.html', _id=_id, note=note, users_right=users_right, users_list=users_list, who=session['user'])

if __name__ == '__main__':
    app.run(host='0.0.0.0')
