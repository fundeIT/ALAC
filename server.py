#!/usr/bin/python3

# Importing standard libraries

import os
import sys
import getopt
import json

# Import specific libraries for web deploying

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import FallbackHandler, RequestHandler, Application, \
                        StaticFileHandler
from flask import Flask, request, render_template, redirect, session, \
                  send_file, make_response, jsonify, Response
from werkzeug.utils import secure_filename

# Other supporting libraries

from markdown import markdown
import datetime

# Own libraries

from models import *
import trust
from attachment import *
import emailmgr
import ticket
import govsearcher
import iaip

app = Flask(__name__)
app.secret_key = trust.secret_key
app.config['UPLOAD_FOLDER'] = trust.docs_path
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'docx', 'xlsx', 'jpg', 'pptx', 'txt'])

def request_analytics(req):
    print(req.path)
    print(req.headers)

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
        
def uploadAttachment(rec):
    rec['file'].filename = secure_filename(rec['file'].filename)
    path = app.config['UPLOAD_FOLDER'] + '/' + rec['year']
    if not os.path.exists(path):
        os.makedirs(path)
    path += '/tickets'
    if not os.path.exists(path):
        os.makedirs(path) 
    path += '/' + rec['ticket_id']
    if not os.path.exists(path):
        os.makedirs(path)
    path += '/' + rec['thread_id']
    if not os.path.exists(path):
        os.makedirs(path)
    path += '/' + rec['file'].filename
    rec['file'].save(path)
    return path[len(app.config['UPLOAD_FOLDER']):]

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

@app.before_request
def before_request():
    f = open('log.txt', 'a')
    line = str(datetime.datetime.now()) + ' ' 
    line += request.remote_addr + ' ' 
    line += request.path + ' '
    line += str(request.accept_languages) + ' '
    line += request.user_agent.platform + ' '
    line += request.user_agent.browser
    line += '\n'
    f.write(line)
    f.close()

@app.route('/')
def index():
    if 'user' in session:
        user = session['user']
        return redirect('/notes')
    else:
        user = {}
        if 'user_id' in request.cookies:
            user['_id'] = request.cookies.get('user_id')
            user['name'] = request.cookies.get('user_name')
            user['kind'] = request.cookies.get('user_kind')
            user['email'] = request.cookies.get('user_email')
            session['user'] = user
            return redirect('/')
        else:
            return redirect('/start')

@app.route('/faq')
def faq():
    request_analytics(request)
    user = {}
    if 'user' in session:
        user = session['user']
    return render_template('ticket/alac.html', who=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users().login(email, password)
        if user:
            user['_id'] = str(user['_id'])
            session['user'] = user
            resp = make_response(redirect('/'))
            if 'remember' in request.form:
                exp = datetime.datetime.now() + datetime.timedelta(days=30)
                resp.set_cookie('user_id', user['_id'], expires=exp)
                resp.set_cookie('user_name', user['name'], expires=exp)
                resp.set_cookie('user_kind', user['kind'], expires=exp)
                resp.set_cookie('user_email', user['email'], expires=exp)
            else:
                resp.set_cookie('user_id', '', expires=0)
                resp.set_cookie('user_name', '', expires=0)
                resp.set_cookie('user_kind', '', expires=0)
                resp.set_cookie('user_email', '', expires=0)
            return resp
        else:
            message = 'Usuario no registrado o contraseña incorrecta'
            return render_template('login.html', message=message, who={})
    else:
        if 'user' in session:
            user = session['user']
        else:
            user = {}
        return render_template('login.html', message=None, who=user)

@app.route('/logout')
def logout():
    del session['user']
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', '', expires=0)
    resp.set_cookie('user_name', '', expires=0)
    resp.set_cookie('user_kind', '', expires=0)
    resp.set_cookie('user_email', '', expires=0)
    return resp

@app.route('/cases')
def cases():
    if not 'user' in session:
        return redirect('/')
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
    return render_template('request/list.html', 
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
        return render_template('request/form.html', _id=_id, req = req, 
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
            if 'user_id' in element:
                u = Users().get(element['user_id'])
                if u:
                    element['user_name'] = u['name']
            updates_mod.append(element)
        docrels = DocRels().list('request', _id)
        docs = Documents().list()
        return render_template('request/show.html', 
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
    return render_template('request/form.html', _id=_id, req=req, status=r.status, results=r.results, cases = Cases().list(), offices = Offices().list(), users_right=users_right, users_list=users_list, who=user)

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
        return render_template('request/close.html', _id=_id, req=req, results=r.results,
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

@app.route('/updates/<string:_id>/delete', methods=['GET'])
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
    return render_template('complain/list.html', drafts=drafts, running=running,
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
        return render_template('complain/form.html', _id=_id, complain=complain,
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
        docrels = DocRels().list('complain', _id)
        docs = Documents().list()
        return render_template('complain/show.html', 
                _id=_id, 
                complain=complain,
                office=office,
                case=case, 
                updates=updates,
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
    return render_template('complain/form.html', _id=_id, complain=complain, status=r.status, results = r.results, cases=Cases().list(), offices=offices, reviewers=reviewers, users_right=users_right, users_list=users_list, who=user)

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
def publicDocs():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    docs = Documents().list(public=True)
    return render_template('doclist.html', docs=docs, who=user)

@app.route('/docs/admin')
def documents():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    docs = Documents().list()
    return render_template('docadmin.html', docs=docs, who=user) 

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
        doc['public'] = request.form['public']
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
        rf = {key: request.form[key] for key in request.form.keys()}
        if not 'public' in rf.keys():
            rf['public'] = ''
        doc = {key: rf[key] for key in d.keys}
        del doc['path']
        d.update(_id, doc)
        return redirect(request.form['referrer'])
    else:
        doc = d.get(_id)
        return render_template('docform.html', _id=_id, doc=doc,
            referrer=request.referrer, who=session['user'], message='')

@app.route('/docs/<string:_id>')
def docDownload(_id):
    d = Attachment('docs').get(_id)
    return send_file(d['path'], as_attachment=True, attachment_filename=d['name'])

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
        doc['title'] = request.form['title']
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
        return redirect("%s#docs" % request.referrer)

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
    user = {}
    if 'user' in session:
        user = session['user']
    notes = Notes().list()
    notelist = [note for note in notes]
    for i in range(len(notelist)):
        a = notelist[i]['content']
        notelist[i]['content'] = markdown(a[0:a.find("\r\n\r\n")])
    return render_template('ticket/notelist.html', notes=notelist, who=user)

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
        return render_template('ticket/noteshow.html', _id=_id, note=note, who=user)

@app.route('/notes/<string:_id>/edit')
def editNote(_id):
    """
    Allows to edit a note previously stored in the database.
    It checks if the user has right to edit the note.
    """
    if not 'user' in session:
        return redirect('/notes')
    n = Notes()
    note = n.get(_id)
    users_right = Rights().listBySource('note', _id)
    users_list = Users().list()
    return render_template('noteform.html', _id=_id, note=note, 
            users_right=users_right, users_list=users_list, 
            who=session['user'])

@app.route('/clients')
def clients():
    if not 'user' in session:
        return redirect('/')
    user = session['user']
    return render_template('client/list.html', 
            clients = Clients().list(), who=user) 

@app.route('/clients/new/', methods=['GET', 'POST'])
def clientNew():
    if not 'user' in session:
        return redirect('/')
    user = session['user']
    if request.method == 'POST':
        c = Clients()
        client = {key: request.form[key] for key in c.keys}
        _id = c.new(client)
        right = {
                'source': 'client',
                'source_id': str(_id),
                'user_id': user['_id']
                }
        Rights().new(right)
        return redirect('/clients')
    else:
        c = Clients()
        client = emptyDict(c.keys)
        _id = 'new/'
        return render_template('client/form.html', _id=_id, client=client, 
            kinds=c.kinds, vulnerables=c.vulnerables, ages=c.ages, who=user)

@app.route('/clients/<string:_id>', methods=['GET', 'POST'])
def clientDetail(_id):
    if not 'user' in session:
        return redirect('/')
    user = session['user']
    if request.method == 'POST':
        if 'user' in session:
            c = Clients()
            client = {key: request.form[key] for key in c.keys} 
            c.update(_id, client)
        return redirect('/clients/%s' % _id)
    else:
        c = Clients()
        tickets = ticket.Ticket().getByClient(_id)
        client = c.get(_id)
        return render_template('client/show.html', 
                client=client,
                kinds=c.kinds, 
                vulnerables=c.vulnerables, 
                ages=c.ages,
                has_right = hasRight('client', _id, ['OPR', 'MNR', 'USR']),
                year=Dates().getYear(), tickets=tickets, who=session['user'])

@app.route('/clients/<string:_id>/edit')
def clientEdit(_id):
    if not 'user' in session:
        return redirect('/clients/%s' % _id)
    if request.method == 'GET':
        c = Clients()
        client = c.get(_id)
        return render_template('client/form.html', _id = _id, client = client, 
            kinds=c.kinds, vulnerables=c.vulnerables, ages=c.ages, 
            who=session['user'])

@app.route('/data/requests')
def dataRequest():
    raw = DB('requests').raw()
    data = []
    for item in raw:
        item['_id'] = str(item['_id'])
        if item['case_id']:
            item['case'] = Cases().get(item['case_id'])['title']
        item['office'] = Offices().get(item['office_id'])['name']
        if item['result']:
            item['result'] = Requests().results[item['result']]
        if 'touched' in item.keys():
            item['touched'] = str(item['touched'])
        data.append(item)
    return jsonify(data)

@app.route("/start")
def start():
    user = {}
    if 'user' in session:
        user = session['user']
    year = Dates().getYear()
    ticket = ''
    email = ''
    remember = False
    if 'ticket' in request.cookies:
        year = request.cookies.get('year')
        ticket = request.cookies.get('ticket')
        email = request.cookies.get('email')
        remember = True
    return render_template("ticket/start.html", year=year, ticket=ticket, email=email, remember=remember, who=user)
        
@app.route("/ticket", methods=['GET', 'POST'])
def get_ticket():
    user = None
    if 'user' in session:
        user = session['user']
    t = ticket.Ticket()
    t.update_referrer(request)
    if request.method == 'GET':
        t.restore_cookie(request)
    else: # POST
        t.get_form(request)
    t.get_threads()
    resp = make_response(render_template("ticket/userform.html", 
        ticket=t, who=user))
    if 'remember' in request.form:
        exp = datetime.datetime.now() + datetime.timedelta(days=90)
        resp.set_cookie('ticket', str(t.ticket), expires=exp)
        resp.set_cookie('year', t.year, expires=exp)
        resp.set_cookie('email', t.email, expires=exp)
    elif t.referrer == 'start':
        resp.set_cookie('ticket', '', expires=0)
        resp.set_cookie('year', '', expires=0)
        resp.set_cookie('email', '', expires=0)
    return resp

@app.route("/ticket/<string:year>/<int:tckt>")
def get_ticketByID(year, tckt):
    # Checking privileges. Only managers and operators are
    # allowed to use this function.
    if not 'user' in session:
        return redirect('/login')
    user = session['user']
    if not user['kind'] in ['MNG', 'OPR']:
        return redirect('/')
    t = ticket.Ticket()
    t.year = year
    t.ticket = tckt
    t.update_hash(is_email=False)
    t.get_threads()
    resp = make_response(render_template("ticket/userform.html", 
        ticket=t, who=user))
    return resp

@app.route("/ticket/<string:year>/<int:tckt>/msg", methods=['GET', 'POST'])
def editTicketMsg(year, tckt):
    if not 'user' in session:
        return redirect('/login')
    user = session['user']
    if not user['kind'] in ['MNG', 'OPR']:
        return redirect('/')
    t = ticket.Ticket()
    t.year = year
    t.ticket = tckt
    t.update_hash(is_email=False)
    if request.method == 'POST':
        msg = request.form['msg']
        t.updateMsg(msg)
        return redirect('/ticket/' + year + '/' + str(tckt))
    else:
        return render_template('editmsg.html', ticket=t, who=user)

@app.route("/ticket/new", methods=['POST'])
def new_ticket():
    user = None
    if 'user' in session:
        user = session['user']
    d = Dates()
    t = ticket.Ticket()
    t.ticket = int(request.form['ticket'])
    t.year = request.form['year']
    t.email = request.form['email']
    t.hash = request.form['ticket_id']
    msg = request.form['msg']
    if t.ticket == 0:
        t.ticket = newCounter('ticket', d.getYear())
        t.append_to_db(msg)
    t.open(t.hash)
    name = ''
    if 'user' in session:
        name = session['user']['name']
    if t.email != '':
        emailmgr.notify(t.year, t.ticket, t.email) 
    emailmgr.notify(t.year, t.ticket, trust.email_user)
    thread = {
        'ticket_id': t.hash, 
        'msg': msg, 
        'date': d.getDate(),
        'name': name
    }
    thread_id = DB('threads').new(thread)
    t.get_threads()
    return render_template("ticket/userform.html", ticket=t, who=user)

@app.route("/ticket/close", methods=['POST'])
def close_ticket():
    if not 'user' in session:
        return redirect('/login')
    _id = request.form['ticket_id']
    ticket.Ticket().close(_id)
    return redirect(request.environ['HTTP_REFERER'])

@app.route("/ticket/link", methods=['POST'])
def linkTicket():
    if not 'user' in session:
        return redirect('/login')
    t = ticket.Ticket()
    t.year = request.form['year']
    t.ticket = int(request.form['ticket'])
    t.update_hash(is_email=False)
    if t.hash:
        DB('tickrels').new({'ticket': t.hash, 'client': request.form['client']})
    return redirect(request.environ['HTTP_REFERER'])

@app.route("/ticket/open", methods=['POST'])
def open_ticket():
    if not 'user' in session:
        return redirect('/login')
    _id = request.form['ticket_id']
    ticket.Ticket().open(_id)
    return redirect(request.environ['HTTP_REFERER'])

@app.route("/threads", methods=['POST'])
def thread():
    user = None
    if 'user' in session:
        user = session['user']
    data = {}
    data['ticket'] = int(request.form['ticket'])
    data['email'] = request.form['email']
    data['year'] = request.form['year']
    ticket = getTicket(data)
    if ticket:
        data['ticket_id'] = str(ticket['_id'])
        threads = getThreads(data['ticket_id'])
        t = []
        docs = {}
        for thread in threads:
            el = dict(thread)
            el['msg'] = markdown(el['msg'])
            t.append(el)
            res = getDocuments(data['ticket_id'], str(thread['_id']))
            docs[str(thread['_id'])] = [x for x in res]
        return render_template("ticket/threads.html", ticket=data,
            threads=t, docs=docs, who=user)
    else:
        return "Your ticket was not found"

@app.route("/threads/<string:_id>/edit", methods=['GET', 'POST'])
def threadEdit(_id):
    if not 'user' in session:
        return redirect('/')
    user = session['user']
    db = DB('threads')
    thread = dict(db.get(_id))
    if request.method == 'GET':
        return render_template('threadform.html', thread=thread, who=user)
    else:
        msg = request.form['msg']
        if len(msg) > 0:
            db.update(_id, {'msg': msg})
        db = DB('tickets')
        ret = db.get(thread['ticket_id'])
        t = ticket.Ticket()
        t.hash = str(ret['_id'])
        t.ticket = ret['ticket']
        t.email = ret['email']
        t.year = ret['year']
        t.get_threads()
        return redirect('/ticket/' + t.year + '/' + str(t.ticket)) 

@app.route('/ticket/<string:status>')
def adminTicket(status):
    # Checking privileges. Only managers and operators are
    # allowed to use this function.
    if not 'user' in session:
        return redirect('/login')
    user = session['user']
    if not user['kind'] in ['MNG', 'OPR']:
        return redirect('/')
    # Setting list parameters
    #   Default values
    limit = 20    # How many items
    skip = 0      # Get since this item
    #   Checking if user gives own values
    if 'limit' in request.args:
        limit = int(request.args.get('limit'))
    if 'skip' in request.args:
        skip = int(request.args.get('skip'))
    # Querying database
    db = DB('tickets')
    count = db.count({'status': status}) # How many items exist
    r = range(0, count, limit)           # Ranges for pagination
    tickets = db.list(skip, limit, {'status': status}, -1) # Getting data
    return render_template('ticket/admin.html',
        tickets=tickets, status=status, rng=r, who=session['user'])

@app.route('/ticket/admin')
def adminEmptyTicket():
    return redirect('/ticket/openned/0')

@app.route('/attachment/<string:_id>')
def attachment(_id):
    d = Attachment('ticketdocs').get(_id)
    return send_file(d['path'], as_attachment=True, attachment_filename=d['name'])

@app.route("/attachment/upload", methods=['POST'])
def attachmentUpload():
    user = None
    if 'user' in session:
        user = session['user']
    rec = {}
    rec['year'] = request.form['year']
    rec['ticket_id'] = request.form['ticket_id'];
    rec['thread_id'] = request.form['thread_id']
    rec['desc'] = request.form['desc']
    rec['file'] = request.files['file']
    path = uploadAttachment(rec)
    if (path):
        del rec['file']
        rec['path'] = path
        _id = str(DB('ticketdocs').new(rec))
        t = ticket.Ticket()
        t.get_form(request)
        t.get_threads()
        return render_template("ticket/userform.html", ticket=t, who=user)
    else:
        return "Failed"

@app.route('/dosiers')
def dosiers():
    if 'user' in session:
        user = session['user']
    else:
        user = {}
    return render_template('dosierlist.html', who=user)

class MainHandler(RequestHandler):
    def get(self):
        self.write("Hello")

tr = WSGIContainer(app)

application = Application([
    (r"/support", MainHandler),
    (r"/favicon.ico", StaticFileHandler, {'path': 'static/favicon.ico'}),
    (r"/static/(.*)", StaticFileHandler, {'path': 'static'}),
    (r"/govsearcher", govsearcher.GovSearcher),
    (r"/iaip", iaip.IAIP),
    (r"/iaip/(.+)", iaip.Res),
    (r"/.well-known/acme-challenge/(.*)", StaticFileHandler, {'path': 'cert'}),

    (r".*", FallbackHandler, dict(fallback=tr)),
], debug=trust.debug)

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dp:", ["debug", "port"])
    except getoopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    debug = False
    port = 5000
    for o, a in opts:
        if o in ["-d", "--debug"]:
            debug = True
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "unhandled option"
    if debug:
        app.run(port=port, host='0.0.0.0', debug=True)
    else:
        http_server = HTTPServer(application, ssl_options={
            "certfile": trust.cert_file,
            "keyfile": trust.key_priv
        })
        http_server.listen(443)
        # application.listen(port)
        IOLoop.instance().start()
