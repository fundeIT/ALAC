# Makinig a dump from the database
ssh root@alac.funde.org "mongodump --db alac"
# Generating a compressed file of the database dump
ssh root@alac.funde.org "tar czf dump.tar.gz dump"
# Copying the database compressed file to the local computer
scp root@alac.funde.org:dump.tar.gz .
# Copying files from the server to the local computer
rsync -av --delete root@alac.funde.org:/files .
# Updating searching indexes in the server
ssh root@alac.funde.org "cd ALAC && python searcher.py"
ssh root@alac.funde.org "cd ALAC && python ticketsearcher.py"
ssh root@alac.funde.org "cd ALAC && python iaipupdate.py"

