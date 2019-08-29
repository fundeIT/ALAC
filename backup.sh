#!/bin/sh
#
# Backup - ALAC app
#
# This script makes a backup from the server where the ALAC
# app is running.
#
# 2019 - Fundación Nacional para el Desarrollo
#
# Contributors:
#   Jaime Lopez <jailop AT protonmail DOT com>

SERVER="root@alac.funde.org"

# Makinig a dump from the database
ssh $SERVER "mongodump --db alac"

# Generating a compressed file of the database dump
ssh $SERVER "tar czf dump.tar.gz dump"

# Copying the database compressed file to the local computer
scp $SERVER:dump.tar.gz .

# Copying files from the server to the local computer
rsync -av --delete $SERVER:/files .

# Updating searching indexes in the server
ssh $SERVER "cd ALAC && python searcher.py"
ssh $SERVER "cd ALAC && python ticketsearcher.py"
ssh $SERVER "cd ALAC && python iaipupdate.py"
