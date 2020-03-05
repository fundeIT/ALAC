import os
import pandas as pd
from flask import make_response, jsonify
from flask_restful import Resource

import trust

STATSFILE = 'data/website_hits.csv'
LOGPATH = trust.log_path + "hits/"

def count_hits():
    # If the stats file does not exists,
    # it is created
    if not os.path.isfile(STATSFILE):
        with open(STATSFILE, "w") as fd:
            fd.write("month,hits,updated\n")

    # Updating the stats dataset
    stats = pd.read_csv(STATSFILE)
    stats['month'] = stats.month.astype(str)
    log_files = os.listdir(LOGPATH)
    for lf in log_files:
        if lf == 'README.md':
            continue
        updated = os.path.getmtime(LOGPATH + lf)
        # Checking if the has a record
        if not lf in stats.month.values:
            hits = len(open(LOGPATH + lf, "r").readlines())
            rec = {'month': lf, 'hits': hits, 'updated': updated}
            stats = stats.append(rec, ignore_index=True)
        else:
            if stats.loc[stats.month == lf, 'updated'].values[0] < updated:
                hits = len(open(LOGPATH + lf, "r").readlines())
                stats.loc[stats.month == lf, 'updated'] = updated
                stats.loc[stats.month == lf, 'hits'] = hits
    stats = stats.sort_values('month')
    stats.to_csv("stats.csv", index=False)
    stats.drop(['updated'], axis=1, inplace=True)
    return stats

class apiWebsiteUsage(Resource):
    def get(self):
        stats = count_hits()
        """
        output = make_response({
            'month': list(stats.month.values),
            'hits': list(stats.hits.values)
        })
        output.headers["Content-Disposition"] = \
            "attachment; filename=website_usage.json"
        output.headers["Content-type"] = "application/json"
        """
        return jsonify({
            'month': list(stats.month.values),
            'hits': list(stats.hits.values)
        })
