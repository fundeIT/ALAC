#!/bin/sh

# This script is intented to make a backup of the data contained in the ALAC
# application.  Beside that, it also update the search indexes.

SERVER="SERVER_NAME"
APP_DIR="/home/alac/ALAC"
FILE_DIR="/home/alac/files"
LOG_DIR="/home/alac/log"

# Dump the database to a folder named 'dump'
# Files are in bson format
ssh $SERVER "mongodump -d alac"
# The database dump is copied to the local machine
rsync -av --delete $SERVER:dump .

# The attachments and other files are copied
# to the local machine
rsync -av --delete $SERVER:$FILE_DIR
rsync -av --delete $SERVER:$LOG_DIR

# Config file are saved
scp $SERVER:$APP_DIR/trust.py .
scp $SERVER:$APP_DIR/monitoring/.env env

# Search indexes are updated
ssh $SERVER "cd $APP_DIR && python searcher.py"
ssh $SERVER "cd $APP_DIR && python ticketsearcher.py"
