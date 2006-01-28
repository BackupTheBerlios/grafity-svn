from grafity.data import column_tool
from grafity.arrays import *

@column_tool('Sort Column/Ascending', image='sort-column-ascending')
def sortcol_asc(worksheet, col):
    col = col[0]
    notnan = ~isnan(col)
    col[notnan] = sorted(col[notnan])

@column_tool('Sort Column/Descending')
def sortcol_desc(worksheet, col):
    col = col[0]
    notnan = ~isnan(col)
    col[notnan] = sorted(col[notnan])

@column_tool('Squeeze')
def squeeze(worksheet, col):
    col = col[0]
    col[:] = col[~isnan(col)]
