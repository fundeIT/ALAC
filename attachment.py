# Management of attachments

import models
import trust

class Attachment:
    """
    Class for the management of documents attachet to dosiers.
    """
    def __init__(self, collection):
        self.d = models.DB(collection)
    def get(self, _id):
        """
        For a given _id returns the path and the name
        of a correspondent file. A counter is increased
        each time a document is gotten.
        """
        doc = self.d.get(_id)
        if not 'downloaded' in doc.keys():
            # Counter is created
            self.d.update(_id, {'downloaded': 1})
        else:
            # Counter is increased by 1
            self.d.update(_id, {'downloaded': doc['downloaded'] + 1})
        path = trust.docs_path + doc['path']
        name = path.split('/')[-1]
        return {'path': path, 'name': name}
