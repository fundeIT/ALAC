#/bin/sh

ssh alac@alac.funde.org "cd ALAC/monitoring && ./makereports.py 2017-04-10 2021-11-30"
ssh alac@alac.funde.org "cd ALAC/monitoring && zip -r reports.zip data/ images/"
scp alac@alac.funde.org:ALAC/monitoring/report.zip .