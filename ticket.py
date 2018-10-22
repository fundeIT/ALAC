# Standard libraries
from markdown import markdown
from bson.objectid import ObjectId

# Own libraries
from models import *

class Ticket:
    def __init__(self):
        self.ticket = 0
        self.year = Dates().getYear()
        self.email = ""
        self.msg = ''
        self.hash = None
        self.referrer = None
        self.threads = None
        self.docs = None
        self.status = 'openned'
    def update_referrer(self, request):
        if request.referrer:
            self.referrer = request.referrer.split('/')[-1]
    def update_hash(self, is_email=True):
        db = DB('tickets')
        if is_email:
            query = {
                    'ticket': self.ticket,
                    'email': self.email,
                    'year': self.year
            }
        else:
            query = {
                    'ticket': self.ticket,
                    'year': self.year
            }
        ret = db.collection.find_one(query)
        if ret:
            self.hash = str(ret['_id'])
            self.msg  = ret['msg']
            self.status = ret['status']
        else:
            self.__init__()
    def updateMsg(self, msg):
        self.msg = msg
        DB('tickets').update(self.hash, {'msg': msg})
    def restore_cookie(self, request):
         if 'ticket' in request.cookies and self.referrer != 'start':
            self.ticket = int(request.cookies.get('ticket'))
            self.year = request.cookies.get('year')
            self.email = request.cookies.get('email')
            self.update_hash()
    def get_form(self, request):
        self.ticket = int(request.form['ticket'])
        self.year = request.form['year']
        self.email = request.form['email']
        self.update_hash()
    def get_documents(self, thread_id):
        db = DB('ticketdocs')
        return db.collection.find({'ticket_id': self.hash, 'thread_id': thread_id})
    def get_threads(self):
        ret = None
        if self.hash:
            db = DB('threads')
            ret = db.collection.find({'ticket_id': self.hash})
        if ret:
            t = []
            self.docs = {}
            for thread in ret:
                el = dict(thread)
                el['_id'] = str(thread['_id'])
                el['msg'] = markdown(el['msg'])
                t.append(el)
                res = self.get_documents(el['_id'])
                self.docs[el['_id']] = [x for x in res]
            self.threads = t
    def append_to_db(self, msg):
        self.hash = DB('tickets').new({
            'ticket': self.ticket,
            'year': self.year,
            'email': self.email,
            'status': self.status,
            'msg': ''
        })
    def close(self, _id):
        DB('tickets').update(_id, {'status': 'closed'})
    def open(self, _id):
        DB('tickets').update(_id, {'status': 'openned'})
    def getByClient(self, client_id):
        ids = DB('tickrels').list(filt={'client': client_id})
        if ids:
            ret = []
            for identifier in ids:
                ret.append(DB('tickets').get(ObjectId(identifier['ticket'])))
            return ret
        else:
            return None
    def getClient(self):
        clients = DB('tickrels').list(filt={'ticket': self.hash})
        if not clients:
            return None
        for el in clients:
            client_id = el['client']
            client = DB('clients').get(client_id)
            return client

if __name__ == '__main__':
    upd('2018-05')
