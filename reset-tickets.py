import pymongo
import trust
from subprocess import call

client = pymongo.MongoClient()
db = client.alac

db.tickets.delete_many({})
db.threads.delete_many({})
db.ticketdocs.delete_many({})
db.counters.delete_many({'kind': 'ticket'})
call(['rm', '-fr', trust.docs_path + '/2017/tickets/*'])

