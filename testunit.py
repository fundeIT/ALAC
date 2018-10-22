#!/usr/bin/python

import models
import resetadmin

def ResetAdminCredentialTest():
    resetadmin.ResetAdminCredentials()
    dbUsers = models.Users()
    admin = dbUsers.getByName('admin')
    assert admin
    assert admin['password'] == dbUsers.encrypt('1234')
    assert admin['kind'] == 'OPR'

if __name__ == '__main__':
    ResetAdminCredentialTest()
