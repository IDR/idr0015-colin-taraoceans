#!/usr/bin/env python

import omero
from omero.rtypes import unwrap
from omero.util.populate_metadata import BulkToMapAnnotationContext
import pandas as pd
import re

# execfile() this from inside `omero shell --login`
# (client variable must exist)

bulkcsv = 'taraoceans.BULK_ANNOTATION.csv'
screenid = 151

# OMERO.web crashes if a non-FileAnnotation on a Plate has namespace
# NSBULKANNOTATIONS, so change it until the bug is fixed.
ns = omero.constants.namespaces.NSBULKANNOTATIONS + '/MapAnnotation'


qs = client.getSession().getQueryService()  # noqa
us = client.getSession().getUpdateService()  # noqa

df = pd.read_csv(bulkcsv)

q = ('SELECT spl.child.id, spl.child.name FROM ScreenPlateLink spl '
     'WHERE spl.parent.id=%d' % screenid)
rs = unwrap(qs.projection(q, None))


class PlateInfo:
    def __init__(self, i, platename):
        self.i = i
        self.name, u, v = re.match(
            '([\w_-]+)_chamber--(U\d\d)--(V\d\d)', r[1]).groups()
        self.well = "%s%s" % (u, v)


plateinfos = [PlateInfo(r[0], r[1]) for r in rs]

names_csv = set(df['Plate'])
names_run = set(pm.name for pm in plateinfos)
# Check all plates have an entry in the CSV
assert names_csv.intersection(names_run) == names_run
#

links = []
for pm in plateinfos:
    r = df.loc[(df['Plate'] == pm.name) & (df['Well'] == pm.well), :]
    target = omero.model.PlateI(pm.i, False)
    rowkvs = zip(r.columns, r.values.squeeze())
    link = BulkToMapAnnotationContext.create_map_annotation(
        [target], rowkvs, ns)
    links.extend(link)

ids = us.saveAndReturnIds(links)
print 'Created MapAnnotation links: %s' % ids
