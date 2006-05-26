import sys
import re

from dispatch import dispatcher

from grafity.base.squirrel import Item, Attr, Container
from grafity.base.arrays import MkArray, transpose, array, asarray
from grafity.base.items import ProjectItem

class Graph(ProjectItem):
    def __init__(self, *args):
        ProjectItem.__init__(self, *args)


