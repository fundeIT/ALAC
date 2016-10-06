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
    d = Dates()
    path = app.config['UPLOAD_FOLDER'] + '/' + d.getYear()
    if not os.path.exists(path):
        os.makedirs(path)
    path += '/' + d.getMonth()
    if not os.path.exists(path):
        os.makedirs(path)
    path += '/' + secure_filename(docfile.filename)
    print(path)
    if not os.path.exists(path):
        docfile.save(path)
        return path 
    else:
        return None

# Controllers

@app.route('/')
def index():
    if not 'user' in session:
        session['user'] = {}
        return redirect('/login')
    return render_template('index.html', who=session['user']) 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not 'user' in session:
        session['user'] = {}
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
            return render_template('login.html', message=message, who=session['user'])
    return render_template('login.html', 
        message=None, who=session['user'])

@app.route('/cases')
def cases():
    if not 'user' in session:
        session['user'] = {}
    return render_template('caselist.html', cases = Cases().list(), who=session['user'])

@app.route('/cases/new/', methods=['GET', 'POST'])
def caseNew():
    if not 'user' in session:
        session['user'] = {}
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
        return render_template('caseform.html', _id=_id, case = case, 
            who=session['user'])

@app.route('/cases/<string:_id>', methods=['GET', 'POST'])
def caseDetail(_id):
    if not 'user' in session:
        session['user'] = {}
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
        docrels = DocRels().list('case', _id)
        docs = Documents().list()
        # for u in updates:
        #    u['detail'] = markdown(u['detail'])
        return render_template('caseshow.html', case = case,
            requests = requests, complains=complains, updates=updates,
            advices=advices, docs=docs, docrels=docrels, who=session['user'])

@app.route('/cases/<string:_id>/edit')
def caseEdit(_id):
    if not 'user' in session:
        session['user'] = {}
    if request.method == 'GET':
        case = Cases().get(_id)
        return render_template('caseform.html', _id = _id, case = case, 
            who=session['user'])

@app.route('/offices')
def offices():
    if not 'user' in session:
        session['user'] = {}
    return render_template('officelist.html', offices = Offices().list(), 
        who=session['user'])
    
@app.route('/offices/new/', methods=['GET', 'POST'])
def officeNew():
    if not 'user' in session:
        session['user'] = {}
    if request.method == 'POST':
        office = {key: request.form[key] for key in Offices().keys}
        office['0'] = 'Sin caso asociado'
        _id = Offices().new(office)
        return redirect('/offices')
    else:
        office = emptyDict(Offices().keys)
        _id = 'new/'
        return render_template('officeform.html', _id=_id, office=office, 
            who=session['user'])

@app.route('/offices/<string:_id>', methods=['GET', 'POST'])
def officeDetail(_id):
    if not 'user' in session:
        session['user'] = {}
    if request.method == 'POST':
        office = {key: request.form[key] for key in Offices().keys} 
        Offices().update(_id, office)
        return redirect('/offices/%s' % _id)
    else:
        office = Offices().get(_id)
        office['notes'] = markdown(office['notes'])
        requests = Requests().list(office_id=_id)  
        complains = Complains().list(office_id=_id)
        updates = Updates().list('office', _id)
        return render_template('officeshow.html', requests=requests,
            complains=complains, office=office, updates=updates, who=session['user'])

@app.route('/offices/<string:_id>/edit')
def officeEdit(_id):
    if not 'user' in session:
        session['user'] = {}
        return render_template('officeform.html', _id = _id, office = Offices().get(_id), who=session['user'])

@app.route('/requests')
def requests():
    if not 'user' in session:
        session['user'] = {}
    r = Requests()
    drafts = r.list(status='0')
    running = r.list(status='1')
    done = r.list(status='2')
    return render_template('requestlist.html', drafts=drafts, running=running, 
        done=done, who=session['user'])

@app.route('/requests/new/', methods=['GET', 'POST'])
def requestNew():
    if not 'user' in session:
        session['user'] = {}
    if request.method == 'POST':
        req = {key: request.form[key] for key in Requests().keys}
        _id = Requests().new(req)
        return redirect('/requests')
    else:
        r = Requests()
        req = emptyDict(r.keys)
        req['result'] = 'ND'
        case_id = request.args.get('case_id')
        if case_id != None:
            req['case_id'] = case_id
        _id = 'new/'
        return render_template('requestform.html', _id=_id, req = req, 
            status = r.status, results = r.results, cases = Cases().list(), 
            offices = Offices().list(), who=session['user'])

@app.route('/requests/<string:_id>', methods=['GET', 'POST'])
def requestDetail(_id):
    if not 'user' in session:
        session['user'] = {}
    r = Requests()
    if request.method == 'POST':
        req = {key: request.form[key] for key in r.keys}
        r.update(_id, req)
        return redirect('/requests/%s' % _id)
    else: # It's GET
        req = r.get(_id)
        req['detail'] = markdown(req['detail'])
        req['status'] = r.status[int(req['status'])]
        req['result'] = r.results[req['result']]
        req['comment'] = markdown(req['comment'])
        case = Cases().get(req['case_id'])
        office = Offices().get(req['office_id'])
        updates = Updates().list('request', _id)
        updates_mod = []
        for element in updates:
            element['detail'] = markdown(element['detail'])
            updates_mod.append(element)
        docrels = DocRels().list('request', _id)
        docs = Documents().list()
        return render_template('requestshow.html', _id=_id, req = req, 
            office = office, case = case, updates=updates_mod,
            docrels=docrels, docs=docs, who=session['user'])

@app.route('/requests/<string:_id>/edit')
def requestEdit(_id):
    if not 'user' in session:
        session['user'] = {}
    r = Requests()
    req = r.get(_id)
    return render_template('requestform.html', _id=_id, req = req, status = r.status, results = r.results, cases = Cases().list(), offices = Offices().list(), who=session['user'])

@app.route('/updates/new/', methods=['POST'])
def updateNew():
    if not 'user' in session:
        session['user'] = {}
    u = Updates()
    update = {key: request.form[key] for key in u.keys}
    _id = u.new(update)
    return redirect(request.referrer)

@app.route('/complains')
def complains():
    if not 'user' in session:
        session['user'] = {}
    complains = Complains()
    drafts = complains.list(status='0')
    running = complains.list(status='1')
    done = complains.list(status='2')
    return render_template('complainlist.html', drafts=drafts, running=running,
        done=done, who=session['user'])

@app.route('/complains/new/', methods=['GET', 'POST'])
def complainNew():
    if not 'user' in session:
        session['user'] = {}
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
        o = Offices()
        offices = o.list()
        reviewers = o.list()
        return render_template('complainform.html', _id=_id, complain = complain, status = r.status, 
            results = r.results, cases = Cases().list(), offices = offices, reviewers = reviewers,
            who=session['user'])

@app.route('/complains/<string:_id>', methods=['GET', 'POST'])
def complainDetail(_id):
    if not 'user' in session:
        session['user'] = {}
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
        reviewer = Offices().get(complain['reviewer_id'])
        updates = Updates().list('complain', _id)
        docrels = DocRels().list('complain', _id)
        docs = Documents().list()
        return render_template('complainshow.html', _id=_id, 
            complain = complain, office = office, case=case, updates=updates,
            reviewer=reviewer, docrels=docrels, docs=docs, who=session['user'])

@app.route('/complains/<string:_id>/edit')
def complainEdit(_id):
    if not 'user' in session:
        session['user'] = {}
    r = Complains()
    complain = r.get(_id)
    o = Offices()
    offices = o.list()
    reviewers = o.list()
    return render_template('complainform.html', _id=_id, complain=complain, status=r.status, 
        results = r.results, cases=Cases().list(), offices=offices,
        reviewers=reviewers, who=session['user'])

@app.route('/users')
def users():
    if not 'user' in session:
        session['user'] = {}
    return render_template('userlist.html', users=Users().list(), who=session['user'])

@app.route('/users/new/', methods=['GET', 'POST'])
def userNew():
    if not 'user' in session:
        session['user'] = {}
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
        session['user'] = {}
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
                return render_template('userform.html', _id=_id, user=user, message=message, password1='', kinds=u.kinds, who=session['user'])
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
    if not 'user' in session:
        session['user'] = {}
    docs = Documents().list()
    return render_template('doclist.html', docs=docs, who=session['user']) 

@app.route('/docs/new/', methods=['GET', 'POST'])
def newDoc():
    if not 'user' in session:
        session['user'] = {}
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
        path = app.config['UPLOAD_FOLDER'] + '/' + d.getYear()
        if not os.path.exists(path):
            os.makedirs(path)
        path += '/' + d.getMonth()
        if not os.path.exists(path):
            os.makedirs(path)
        path += '/' + secure_filename(docfile.filename)
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
        session['user'] = {}
    d = Documents()
    if request.method == 'POST':
        doc = {key: request.form[key] for key in d.keys}
        del doc['path']
        d.update(_id, doc)
        return redirect('/docs/%s/edit' % _id)
    else:
        doc = d.get(_id)
        return render_template('docform.html', _id=_id, doc=doc,
            who=session['user'], message='')

@app.route('/docs/<string:_id>')
def docDownload(_id):
    if not 'user' in session:
        session['user'] = {}
    d = Documents()
    doc = d.get(_id)
    path = app.config['UPLOAD_FOLDER'] + '/' + doc['path']
    filename = path.split('/')[-1]
    return send_file(path, as_attachment=True, attachment_filename=filename)

@app.route('/docrels/new/', methods=['POST'])
def docrelNew():
    if not 'user' in session:
        session['user'] = {}
        return redirect(request.referrer)
    else:
        dr = DocRels()
        docrel = {key: request.form[key] for key in dr.keys}
        _id = dr.new(docrel)
        return redirect(request.referrer)

@app.route('/docrels/newdoc/', methods=['POST'])
def docrelNewWithDoc():
    if not 'user' in session:
        session['user'] = {}
        return redirect(request.referrer)
    else:
        doc = {}
        doc['title'] = request.form['prefix'] + ' - ' + request.form['title']
        doc['overview'] = ''
        doc['tags'] = ''
        doc['date'] = Dates().getDate() 
        docfile = request.files['file']
        path = uploadFile(docfile)
        if path:
            doc['path'] = Dates().getDatePath() + docfile.filename 
            doc_id = Documents().new(doc)
            docrel = {}
            docrel['source'] = request.form['source']
            docrel['source_id'] = request.form['source_id']
            docrel['doc_id'] = doc_id
            print(docrel)
            DocRels().new(docrel)
        return redirect(request.referrer)

if __name__ == '__main__':
    app.run()
