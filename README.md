# ALAC's information system

This app supports ALAC's information system. Right now it includes recording information requests and complains to different El Salvador's government offices.

<http://alac.funde.org>

## Requeriments

- Python 3.0
- Python libraries: pymongo, flask, markdown, numpy, whoosh
- MongoDB

## Installation

Before install application you need to have installed requeriments indicated above.

Download the source code:

    $ git clone https://github.com/fundeIT/ALAC.git

Create a file named 'trust.py' with the following content:

    secret_key = "CHOOSE_YOUR_SECRET_KEY"
    docs_path = "DIRECTORY_WHERE_FILES_WILL_STORED"
    db_server = "DATABASE_SERVER_HOST_NAME"
    db_name = "DATABASE_NAME"
    db_port = SERVER_PORT
    db_user = "DATABASE USERNAME ACCESS"
    db_password = "DATABASE PASSWORD ACCESS"
    email_user = "USERNAME-EMAIL-SERVER"
    email_password = "PASSWORD-EMAIL-SERVER"
    email_server = "NAME-EMAIL-SERVER"
    email_port = "PORT_EMAIL_SERVER"
    cert_file = "YOUR_CERTIFICATE_PATH"
    key_priv = "YOUR_PRIVATE_KEY_PATH"

Run the utility program 'resetadmin.py' to create the admin user:

    $ python resetadmin.py

The new user admin created has the following attributes:

- Usarname: admin
- Email: admin@localhost
- Password: 1234

## Running

To run the application:

    $ ./server.py
