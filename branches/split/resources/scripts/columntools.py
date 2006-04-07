import sys
from grafity.arrays import *
from grafity.extend import extension, options, extension_types

@extension('column-tool')
@options(name='Sort Column/Ascending', image='sort-column-ascending')
def sortcol_asc(worksheet, col):
    col = col[0]
    notnan = ~isnan(col)
    col[notnan] = sorted(col[notnan])

@extension('column-tool')
@options(name='Sort Column/Descending')
def sortcol_desc(worksheet, col):
    col = col[0]
    notnan = ~isnan(col)
    col[notnan] = sorted(col[notnan], reverse=True)

@extension('column-tool')
@options(name='Normalize/Sum=1')
def sortcol_asc(worksheet, col):
    col = col[0]
    notnan = ~isnan(col)
    col[:] = col/sum(col[notnan])

@extension('column-tool')
@options(name='Normalize/Max=1')
def sortcol_desc(worksheet, col):
    col = col[0]
    notnan = ~isnan(col)
    col[:] = col/max(col[notnan])

@extension('column-tool')
@options(name='Squeeze')
def squeeze(worksheet, col):
    col = col[0]
    col[:] = col[~isnan(col)]
