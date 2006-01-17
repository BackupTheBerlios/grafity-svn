import sys
try:
    import metakit
except ImportError:
    import grafit.thirdparty.metakit as metakit

import cPickle as pickle

def wrap(value, type):
    if type == 'V':
        return view_to_list(value)
    else:
        return value

def row_to_dict(view, row):
    return dict((prop.name, wrap(getattr(row, prop.name), prop.type)) for prop in view.structure())

def view_to_list(view):
    return list(row_to_dict(view, row) for row in view)

def fill(view, data):
    for row in data:
        addrow(view, row)

def addrow(view, row):
    attrs = dict((k, v) for k, v in row.iteritems() if not isinstance(v, list))
    subviews = dict((k, v) for k, v in row.iteritems() if isinstance(v, list))
    ind = view.append(**attrs)
    for name, value in subviews.iteritems():
        fill(getattr(view[ind], name), value)
    return ind

def main():
    db = metakit.storage(sys.argv[1], 0)

    views = []

    sofar = []
    depth = 0
    for c in db.description():
        if c == '[': depth += 1
        elif c == ']': depth -= 1
        if depth == 0 and c == ',':
            views.append("".join(sofar))
            sofar[:] = []
        else:
            sofar.append(c)
    views.append("".join(sofar))

    di = dict(zip(views, [view_to_list(db.getas(v)) for v in views]))

    print "converted succesfully"

#####

    db = metakit.storage('out.db', 1)


    for viewdesc, data in di.iteritems():
        view = db.getas(viewdesc)
        fill(view, data)

    db.commit()

    print "converted succesfully"

if __name__=='__main__':
    main()
