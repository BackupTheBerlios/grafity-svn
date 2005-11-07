# create a new worksheet
ws = project.new_worksheet('ws')

ws.name # returns 'ws'
ws.name = 'ws2'

ws.A = [] # add new column
ws.A = [2,5,6]
ws.A = arange(100)

ws.A.name = 'B'

del ws.A # delete column

ws.B = 'ws.A + 14' # set as calculated column

ws.delete()

ws.view.show()
ws.view.hide()
ws.view.resize(100, 300)



gr = Graph('graph1')

gr.add(Dataset(ws.A, ws.B))
gr.ws.B.A.symbol_size = 10

# Global objects

# project: project object
project.worksheets
project.graphs
project.save(filename, compression)
project.load(filename)
project.clear()

# mainwin: main window object
mainwin.console

project.new_worksheet('data1')
project.new_graph('graph1')
data1.A = [1,2,3]
data1.B = [4,5,6]
graph1.add(data1.A.B)

# settings
settings['/grafit/plugins/load'] = 'dielectric'

COMMANDS:

Worksheet Commands
------------------
-   Create worksheet
-   Delete worksheet
-   Rename worksheet
-   Add column
-   Remove column
x   Change calc
-   Move column
x   Rename column
x   Change data
-   Delete
-   Paste

Graph Commands
--------------
-   Create graph
-   Delete graph
-   Rename graph
-   Add dataset
-   Remove dataset
-   Change dataset style
-   Change dataset range
-   Zoom
-   Change axis scale
-   Change axis title

Fit Commands
------------
-   Add function
-   Remove function
-   Rename function
-   Change fit datasets
-   Change parameter sharing
-   Change parameter value
    Change parameter lock
    Change fit settings
