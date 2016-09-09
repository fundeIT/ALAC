from models import Users

if __name__ == '__main__':
    u = Users()
    admin = u.getByName('admin')
    if admin:
        admin['password'] = '1234'
        admin['kind'] = 'OPR'
        u.update(admin['_id'], admin)
        print('La contraseña del administrado fue reestalecida')
    else:
        admin = {
            'name': 'admin', 
            'email': 'admin@localhost', 
            'password': '1234',
            'kind': 'OPR'
        }
        u.new(admin)
        print('El usuario admin ha sido creado')

