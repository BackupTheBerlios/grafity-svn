import urllib
import sys
from elementtree import ElementTree

url = "http://grafity.berlios.de/grafity-plugins.xml"

print >>sys.stderr, "getting plugins...",
root = ElementTree.fromstring(urllib.urlopen(url).read())
print >>sys.stderr, "ok"

for element in root.findall('plugin'):
    print "Plugin %s, version %s" % (element.get('name'), element.get('version'))
    for dl in element.findall('download'):
        print "   download from %s" % (dl.get('url'))
    desc = element.find('description')
    if desc is not None:
        print desc.text
