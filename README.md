# ALAC's information system

This app supports ALAC's information system. Right now it includes recording information requests and complains to different El Salvador's government offices.

## Requeriments

- Python 3.0
- Python libraries: pymongo, flask, markdown
- MongoDB

## Installation

Before install application you need to have installed requeriments indicated above.

Download the source code:

    $ git clone https://github.com/fundeIT/ALAC.git

Create a file named 'trust.py' with the following content:

    secret_key = "CHOOSE_YOUR_SECRET_KEY"
    docs_path = "DIRECTORY_WHERE_FILES_WILL_STORED"

Run the utility program 'resetadmin.py' to create the admin user:

    $ python resetadmin.py

The new user admin created has the following attributes:

- Usarname: admin
- Email: admin@localhost
- Password: 1234

## Running

To run the application:

    $ ./run.sh

Or if you are using a Windows system, execute the file `run.bat`
