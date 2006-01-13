# mingui - minimalist gui for python

from base import Widget, Container, Button, Image, Label, run, app, \
                 Frame, Spin, Choice, ImageChoice, ProgressBar, Checkbox, ColorSelect
from commands import Menu, Menubar, Toolbar, Command, \
                     Item, Separator, commands, CommandRef
from images import images

from containers import Box, Splitter, Notebook, Panel, Grid, Scrolled
from window import Window, Dialog
from tree import Tree, TreeNode
from listctrl import List, ListData
from text import Text, Html

from python import PythonEditor, PythonShell
from table import Table
from opengl import OpenGLWidget

from dialogs import request_file_save, request_file_open, alert_yesnocancel

import xml
"""
base classes
------------
    Widget
    ------
        properties:
            x         -- x-coordinate of upper left corner
            y         -- y-coordinate of upper left corner
            position  -- equivalent to (x, y)
            width     -- widget width
            height    -- widget height
            size      -- equivalent to (width, height)
            min_size  -- minimum size (min_x, min_y) that the widget is allowed to have
            geometry  -- equivalent to (x, y, width, height)
            visible   -- whether the widget is visible
            enabled   -- whether the widget is enabled
            text      -- text associated with the widget
            parent    -- the containing widget
    
    Container
    ---------

top level
---------
    Window
    Dialog

containers
----------
    Box
    ---
        place options:
            expand   --
            stretch  --
    Grid
    ----
        place options
            position --
            span     --
    Frame
    -----

    Notebook
    --------
        place options:
            label    -- text in the notebook tab
            image    -- image in the notebook tab
    Splitter
    --------
        place options:
            width    -- initial width to give the pane
    Panel
    -----
        place options:
            label    -- text in the panel button
            image    -- image in the panel button

    Scrolled
    --------

static
------
    Label
    Image
    Html

controls
--------
    Button
    Choice
    Checkbox
    ImageChoice
    ColorSelect
    Spin
    Text

python
------
    PythonEditor
    PythonShell

data
----
    List
    Tree
    Table

special
-------
    OpenGLWidget
"""
