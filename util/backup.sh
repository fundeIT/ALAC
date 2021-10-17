#!/bin/sh

# This script is intented to make a backup of the data contained in the ALAC
# application.  Beside that, it also update the search indexes.

SERVER="SERVER_NAME"
# Dump the database to a folder named 'dump'
# Files are in bson format
ssh $SERVER "mongodump -d alac"
# The database dump is copied to the local machine
rsync -av --delete $SERVER:dump .

# The attachments and other files are copied
# to the local machine
rsync -av --delete $SERVER:/home/alac/files .
rsync -av --delete $SERVER:/home/alac/log .

# Config file are saved
scp $SERVER:ALAC/trust.py .
scp $SERVER:ALAC/monitoring/.env env

# Search indexes are updated
ssh $SERVER "cd ALAC && python searcher.py"
ssh $SERVER "cd ALAC && python ticketsearcher.py"
