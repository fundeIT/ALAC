#!/usr/bin/python

# This script reset credentials for the administrator user.
# 
# It must be runned when the system runs the first time or when for any reason
# you need to gain priviliged access to the system.
#
# The new credentials are 'admin' as username and '1234' as password. It is
# advisable to change the admin password as soon as posible.

import models

def ResetAdminCredentials():
    dbUsers = models.Users()
    admin = dbUsers.getByName('admin')
    if admin: 
        # Does it exist? Yes
        admin['password'] = '1234'
        admin['kind'] = 'OPR'
        dbUsers.update(admin['_id'], admin)
    else:
        admin = {
            'name': 'admin', 
            'email': 'admin@localhost', 
            'password': '1234',
            'kind': 'OPR'
        }
        dbUsers.new(admin)

def TestResetAdminCredentials():
    ResetAdminCredentials()
    dbUsers = models.Users()
    admin = dbUsers.getByName('admin')
    assert admin
    assert admin['password'] == dbUsers.encrypt('1234')
    assert admin['kind'] == 'OPR'

if __name__ == '__main__':
    ResetAdminCredentials()
