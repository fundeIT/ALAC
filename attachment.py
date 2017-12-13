import models
import trust

class Attachment:
    def __init__(self, collection):
        self.d = models.DB(collection)
    def get(self, _id):
        doc = self.d.get(_id)
        if not 'downloaded' in doc.keys():
            self.d.update(_id, {'downloaded': 1})
        else:
            self.d.update(_id, {'downloaded': doc['downloaded'] + 1})
        path = trust.docs_path + doc['path']
        name = path.split('/')[-1]
        return {'path': path, 'name': name}
