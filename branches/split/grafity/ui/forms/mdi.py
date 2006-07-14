# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'unknown'
#
# Created: Fri Jul 14 18:32:28 2006
#      by: PyQt4 UI code generator snapshot-20060424
#
# WARNING! All changes made in this file will be lost!

import sys
from grafity.ui.console import ConsoleTextEdit
from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,952,688).size()).expandedTo(MainWindow.minimumSizeHint()))

        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.hboxlayout = QtGui.QHBoxLayout(self.centralwidget)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(0)
        self.hboxlayout.setObjectName("hboxlayout")
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0,0,952,31))
        self.menubar.setObjectName("menubar")

        self.menu_Project = QtGui.QMenu(self.menubar)
        self.menu_Project.setObjectName("menu_Project")

        self.menu_Edit = QtGui.QMenu(self.menubar)
        self.menu_Edit.setObjectName("menu_Edit")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setGeometry(QtCore.QRect(0,664,952,24))
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.bottom = QtGui.QDockWidget(MainWindow)
        self.bottom.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.bottom.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.bottom.setObjectName("bottom")

        self.dockWidgetContents_3 = QtGui.QWidget(self.bottom)
        self.dockWidgetContents_3.setObjectName("dockWidgetContents_3")

        self.vboxlayout = QtGui.QVBoxLayout(self.dockWidgetContents_3)
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setSpacing(0)
        self.vboxlayout.setObjectName("vboxlayout")

        self.tabWidget_3 = QtGui.QTabWidget(self.dockWidgetContents_3)
        self.tabWidget_3.setTabPosition(QtGui.QTabWidget.South)
        self.tabWidget_3.setObjectName("tabWidget_3")

        self.tab_5 = QtGui.QWidget()
        self.tab_5.setObjectName("tab_5")

        self.hboxlayout1 = QtGui.QHBoxLayout(self.tab_5)
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(0)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.console = ConsoleTextEdit(self.tab_5)
        self.console.setObjectName("console")
        self.hboxlayout1.addWidget(self.console)
        self.tabWidget_3.addTab(self.tab_5, "")

        self.tab_6 = QtGui.QWidget()
        self.tab_6.setObjectName("tab_6")
        self.tabWidget_3.addTab(self.tab_6, "")
        self.vboxlayout.addWidget(self.tabWidget_3)
        self.bottom.setWidget(self.dockWidgetContents_3)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(8),self.bottom)

        self.left = QtGui.QDockWidget(MainWindow)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.left.sizePolicy().hasHeightForWidth())
        self.left.setSizePolicy(sizePolicy)
        self.left.setMinimumSize(QtCore.QSize(16,16))
        self.left.setMaximumSize(QtCore.QSize(170,16777215))
        self.left.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.left.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.left.setObjectName("left")

        self.dockWidgetContents = QtGui.QWidget(self.left)
        self.dockWidgetContents.setObjectName("dockWidgetContents")

        self.hboxlayout2 = QtGui.QHBoxLayout(self.dockWidgetContents)
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(0)
        self.hboxlayout2.setObjectName("hboxlayout2")

        self.tabWidget = QtGui.QTabWidget(self.dockWidgetContents)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setTabPosition(QtGui.QTabWidget.West)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")

        self.hboxlayout3 = QtGui.QHBoxLayout(self.tab)
        self.hboxlayout3.setMargin(0)
        self.hboxlayout3.setSpacing(0)
        self.hboxlayout3.setObjectName("hboxlayout3")

        self.tree = QtGui.QTreeView(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tree.sizePolicy().hasHeightForWidth())
        self.tree.setSizePolicy(sizePolicy)
        self.tree.setObjectName("tree")
        self.hboxlayout3.addWidget(self.tree)
        self.tabWidget.addTab(self.tab, "")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.hboxlayout4 = QtGui.QHBoxLayout(self.tab_2)
        self.hboxlayout4.setMargin(0)
        self.hboxlayout4.setSpacing(0)
        self.hboxlayout4.setObjectName("hboxlayout4")

        self.listWidget = QtGui.QListWidget(self.tab_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setObjectName("listWidget")
        self.hboxlayout4.addWidget(self.listWidget)
        self.tabWidget.addTab(self.tab_2, "")
        self.hboxlayout2.addWidget(self.tabWidget)
        self.left.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1),self.left)

        self.right = QtGui.QDockWidget(MainWindow)
        self.right.setMaximumSize(QtCore.QSize(170,16777215))
        self.right.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.right.setObjectName("right")

        self.dockWidgetContents_2 = QtGui.QWidget(self.right)
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")

        self.hboxlayout5 = QtGui.QHBoxLayout(self.dockWidgetContents_2)
        self.hboxlayout5.setMargin(0)
        self.hboxlayout5.setSpacing(0)
        self.hboxlayout5.setObjectName("hboxlayout5")

        self.tabs = QtGui.QTabWidget(self.dockWidgetContents_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabs.sizePolicy().hasHeightForWidth())
        self.tabs.setSizePolicy(sizePolicy)

        font = QtGui.QFont(self.tabs.font())
        font.setFamily("Sans Serif")
        font.setPointSize(9)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.tabs.setFont(font)
        self.tabs.setTabPosition(QtGui.QTabWidget.East)
        self.tabs.setTabShape(QtGui.QTabWidget.Rounded)
        self.tabs.setObjectName("tabs")

        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.tab_3)
        self.vboxlayout1.setMargin(0)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.hboxlayout6 = QtGui.QHBoxLayout()
        self.hboxlayout6.setMargin(0)
        self.hboxlayout6.setSpacing(6)
        self.hboxlayout6.setObjectName("hboxlayout6")

        self.add_button = QtGui.QToolButton(self.tab_3)
        self.add_button.setIcon(QtGui.QIcon("images/16/add.png"))
        self.add_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.add_button.setAutoRaise(True)
        self.add_button.setObjectName("add_button")
        self.hboxlayout6.addWidget(self.add_button)

        self.toolButton = QtGui.QToolButton(self.tab_3)
        self.toolButton.setIcon(QtGui.QIcon("images/16/add.png"))
        self.toolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toolButton.setAutoRaise(True)
        self.toolButton.setObjectName("toolButton")
        self.hboxlayout6.addWidget(self.toolButton)

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout6.addItem(spacerItem)
        self.vboxlayout1.addLayout(self.hboxlayout6)

        self.splitter = QtGui.QSplitter(self.tab_3)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName("splitter")

        self.widget_2 = QtGui.QWidget(self.splitter)
        self.widget_2.setObjectName("widget_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.widget_2)
        self.vboxlayout2.setMargin(0)
        self.vboxlayout2.setSpacing(0)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.label = QtGui.QLabel(self.widget_2)
        self.label.setObjectName("label")
        self.vboxlayout2.addWidget(self.label)

        self.treeView = QtGui.QTreeView(self.widget_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(sizePolicy)
        self.treeView.setObjectName("treeView")
        self.vboxlayout2.addWidget(self.treeView)

        self.widget_21 = QtGui.QWidget(self.splitter)
        self.widget_21.setObjectName("widget_21")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.widget_21)
        self.vboxlayout3.setMargin(0)
        self.vboxlayout3.setSpacing(0)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.label_2 = QtGui.QLabel(self.widget_21)
        self.label_2.setObjectName("label_2")
        self.vboxlayout3.addWidget(self.label_2)

        self.listView = QtGui.QListView(self.widget_21)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listView.sizePolicy().hasHeightForWidth())
        self.listView.setSizePolicy(sizePolicy)
        self.listView.setObjectName("listView")
        self.vboxlayout3.addWidget(self.listView)

        self.widget_22 = QtGui.QWidget(self.splitter)
        self.widget_22.setObjectName("widget_22")

        self.vboxlayout4 = QtGui.QVBoxLayout(self.widget_22)
        self.vboxlayout4.setMargin(0)
        self.vboxlayout4.setSpacing(0)
        self.vboxlayout4.setObjectName("vboxlayout4")

        self.label_3 = QtGui.QLabel(self.widget_22)
        self.label_3.setObjectName("label_3")
        self.vboxlayout4.addWidget(self.label_3)

        self.listView_2 = QtGui.QListView(self.widget_22)
        self.listView_2.setObjectName("listView_2")
        self.vboxlayout4.addWidget(self.listView_2)
        self.vboxlayout1.addWidget(self.splitter)
        self.tabs.addTab(self.tab_3, "")

        self.Style = QtGui.QWidget()
        self.Style.setObjectName("Style")

        self.vboxlayout5 = QtGui.QVBoxLayout(self.Style)
        self.vboxlayout5.setMargin(0)
        self.vboxlayout5.setSpacing(6)
        self.vboxlayout5.setObjectName("vboxlayout5")

        self.vboxlayout6 = QtGui.QVBoxLayout()
        self.vboxlayout6.setMargin(0)
        self.vboxlayout6.setSpacing(0)
        self.vboxlayout6.setObjectName("vboxlayout6")

        self.vboxlayout7 = QtGui.QVBoxLayout()
        self.vboxlayout7.setMargin(0)
        self.vboxlayout7.setSpacing(0)
        self.vboxlayout7.setObjectName("vboxlayout7")

        self.textLabel1_3 = QtGui.QLabel(self.Style)
        self.textLabel1_3.setObjectName("textLabel1_3")
        self.vboxlayout7.addWidget(self.textLabel1_3)

        self.hboxlayout7 = QtGui.QHBoxLayout()
        self.hboxlayout7.setMargin(0)
        self.hboxlayout7.setSpacing(0)
        self.hboxlayout7.setObjectName("hboxlayout7")

        spacerItem1 = QtGui.QSpacerItem(8,20,QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Minimum)
        self.hboxlayout7.addItem(spacerItem1)

        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)
        self.gridlayout.setObjectName("gridlayout")

        self.lwidth_ch = QtGui.QCheckBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lwidth_ch.sizePolicy().hasHeightForWidth())
        self.lwidth_ch.setSizePolicy(sizePolicy)
        self.lwidth_ch.setObjectName("lwidth_ch")
        self.gridlayout.addWidget(self.lwidth_ch,2,0,1,1)

        self.lwidth = QtGui.QSpinBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lwidth.sizePolicy().hasHeightForWidth())
        self.lwidth.setSizePolicy(sizePolicy)
        self.lwidth.setMaximum(40)
        self.lwidth.setMinimum(1)
        self.lwidth.setObjectName("lwidth")
        self.gridlayout.addWidget(self.lwidth,2,2,1,1)

        self.lstyle = QtGui.QComboBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lstyle.sizePolicy().hasHeightForWidth())
        self.lstyle.setSizePolicy(sizePolicy)
        self.lstyle.setObjectName("lstyle")
        self.gridlayout.addWidget(self.lstyle,1,2,1,1)

        self.textLabel5_2 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel5_2.sizePolicy().hasHeightForWidth())
        self.textLabel5_2.setSizePolicy(sizePolicy)
        self.textLabel5_2.setObjectName("textLabel5_2")
        self.gridlayout.addWidget(self.textLabel5_2,1,1,1,1)

        self.textLabel6_2 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel6_2.sizePolicy().hasHeightForWidth())
        self.textLabel6_2.setSizePolicy(sizePolicy)
        self.textLabel6_2.setObjectName("textLabel6_2")
        self.gridlayout.addWidget(self.textLabel6_2,2,1,1,1)

        self.ltype_ch = QtGui.QCheckBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ltype_ch.sizePolicy().hasHeightForWidth())
        self.ltype_ch.setSizePolicy(sizePolicy)
        self.ltype_ch.setObjectName("ltype_ch")
        self.gridlayout.addWidget(self.ltype_ch,0,0,1,1)

        self.lstyle_ch = QtGui.QCheckBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lstyle_ch.sizePolicy().hasHeightForWidth())
        self.lstyle_ch.setSizePolicy(sizePolicy)
        self.lstyle_ch.setObjectName("lstyle_ch")
        self.gridlayout.addWidget(self.lstyle_ch,1,0,1,1)

        self.textLabel4_2 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel4_2.sizePolicy().hasHeightForWidth())
        self.textLabel4_2.setSizePolicy(sizePolicy)
        self.textLabel4_2.setObjectName("textLabel4_2")
        self.gridlayout.addWidget(self.textLabel4_2,0,1,1,1)

        self.ltype = QtGui.QComboBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ltype.sizePolicy().hasHeightForWidth())
        self.ltype.setSizePolicy(sizePolicy)
        self.ltype.setObjectName("ltype")
        self.gridlayout.addWidget(self.ltype,0,2,1,1)
        self.hboxlayout7.addLayout(self.gridlayout)
        self.vboxlayout7.addLayout(self.hboxlayout7)
        self.vboxlayout6.addLayout(self.vboxlayout7)

        self.textLabel1_4 = QtGui.QLabel(self.Style)
        self.textLabel1_4.setObjectName("textLabel1_4")
        self.vboxlayout6.addWidget(self.textLabel1_4)

        self.hboxlayout8 = QtGui.QHBoxLayout()
        self.hboxlayout8.setMargin(0)
        self.hboxlayout8.setSpacing(0)
        self.hboxlayout8.setObjectName("hboxlayout8")

        spacerItem2 = QtGui.QSpacerItem(8,20,QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Minimum)
        self.hboxlayout8.addItem(spacerItem2)

        self.gridlayout1 = QtGui.QGridLayout()
        self.gridlayout1.setMargin(0)
        self.gridlayout1.setSpacing(0)
        self.gridlayout1.setObjectName("gridlayout1")

        self.color_ch = QtGui.QCheckBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.color_ch.sizePolicy().hasHeightForWidth())
        self.color_ch.setSizePolicy(sizePolicy)
        self.color_ch.setObjectName("color_ch")
        self.gridlayout1.addWidget(self.color_ch,3,0,1,1)

        self.shape = QtGui.QComboBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.shape.sizePolicy().hasHeightForWidth())
        self.shape.setSizePolicy(sizePolicy)
        self.shape.setObjectName("shape")
        self.gridlayout1.addWidget(self.shape,0,2,1,1)

        self.textLabel4 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel4.sizePolicy().hasHeightForWidth())
        self.textLabel4.setSizePolicy(sizePolicy)
        self.textLabel4.setObjectName("textLabel4")
        self.gridlayout1.addWidget(self.textLabel4,0,1,1,1)

        self.color = QtGui.QComboBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.color.sizePolicy().hasHeightForWidth())
        self.color.setSizePolicy(sizePolicy)
        self.color.setObjectName("color")
        self.gridlayout1.addWidget(self.color,3,2,1,1)

        self.fill = QtGui.QComboBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fill.sizePolicy().hasHeightForWidth())
        self.fill.setSizePolicy(sizePolicy)
        self.fill.setObjectName("fill")
        self.gridlayout1.addWidget(self.fill,1,2,1,1)

        self.textLabel4_3 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel4_3.sizePolicy().hasHeightForWidth())
        self.textLabel4_3.setSizePolicy(sizePolicy)
        self.textLabel4_3.setObjectName("textLabel4_3")
        self.gridlayout1.addWidget(self.textLabel4_3,1,1,1,1)

        self.textLabel7 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel7.sizePolicy().hasHeightForWidth())
        self.textLabel7.setSizePolicy(sizePolicy)
        self.textLabel7.setObjectName("textLabel7")
        self.gridlayout1.addWidget(self.textLabel7,3,1,1,1)

        self.size_ch = QtGui.QCheckBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.size_ch.sizePolicy().hasHeightForWidth())
        self.size_ch.setSizePolicy(sizePolicy)
        self.size_ch.setObjectName("size_ch")
        self.gridlayout1.addWidget(self.size_ch,2,0,1,1)

        self.fill_ch = QtGui.QCheckBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fill_ch.sizePolicy().hasHeightForWidth())
        self.fill_ch.setSizePolicy(sizePolicy)
        self.fill_ch.setObjectName("fill_ch")
        self.gridlayout1.addWidget(self.fill_ch,1,0,1,1)

        self.shape_ch = QtGui.QCheckBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.shape_ch.sizePolicy().hasHeightForWidth())
        self.shape_ch.setSizePolicy(sizePolicy)
        self.shape_ch.setObjectName("shape_ch")
        self.gridlayout1.addWidget(self.shape_ch,0,0,1,1)

        self.textLabel6 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel6.sizePolicy().hasHeightForWidth())
        self.textLabel6.setSizePolicy(sizePolicy)
        self.textLabel6.setObjectName("textLabel6")
        self.gridlayout1.addWidget(self.textLabel6,2,1,1,1)

        self.size = QtGui.QSpinBox(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.size.sizePolicy().hasHeightForWidth())
        self.size.setSizePolicy(sizePolicy)
        self.size.setMaximum(60)
        self.size.setMinimum(1)
        self.size.setProperty("value",QtCore.QVariant(5))
        self.size.setObjectName("size")
        self.gridlayout1.addWidget(self.size,2,2,1,1)
        self.hboxlayout8.addLayout(self.gridlayout1)
        self.vboxlayout6.addLayout(self.hboxlayout8)
        self.vboxlayout5.addLayout(self.vboxlayout6)

        self.hboxlayout9 = QtGui.QHBoxLayout()
        self.hboxlayout9.setMargin(0)
        self.hboxlayout9.setSpacing(6)
        self.hboxlayout9.setObjectName("hboxlayout9")

        self.textLabel4_2_2 = QtGui.QLabel(self.Style)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel4_2_2.sizePolicy().hasHeightForWidth())
        self.textLabel4_2_2.setSizePolicy(sizePolicy)
        self.textLabel4_2_2.setObjectName("textLabel4_2_2")
        self.hboxlayout9.addWidget(self.textLabel4_2_2)

        self.group = QtGui.QComboBox(self.Style)
        self.group.setObjectName("group")
        self.hboxlayout9.addWidget(self.group)
        self.vboxlayout5.addLayout(self.hboxlayout9)

        spacerItem3 = QtGui.QSpacerItem(213,191,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout5.addItem(spacerItem3)
        self.tabs.addTab(self.Style, "")

        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")

        self.vboxlayout8 = QtGui.QVBoxLayout(self.tab_4)
        self.vboxlayout8.setMargin(0)
        self.vboxlayout8.setSpacing(6)
        self.vboxlayout8.setObjectName("vboxlayout8")

        self.vboxlayout9 = QtGui.QVBoxLayout()
        self.vboxlayout9.setMargin(0)
        self.vboxlayout9.setSpacing(0)
        self.vboxlayout9.setObjectName("vboxlayout9")

        self.textLabel1 = QtGui.QLabel(self.tab_4)
        self.textLabel1.setObjectName("textLabel1")
        self.vboxlayout9.addWidget(self.textLabel1)

        self.hboxlayout10 = QtGui.QHBoxLayout()
        self.hboxlayout10.setMargin(0)
        self.hboxlayout10.setSpacing(0)
        self.hboxlayout10.setObjectName("hboxlayout10")

        spacerItem4 = QtGui.QSpacerItem(8,20,QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Minimum)
        self.hboxlayout10.addItem(spacerItem4)

        self.gridlayout2 = QtGui.QGridLayout()
        self.gridlayout2.setMargin(0)
        self.gridlayout2.setSpacing(0)
        self.gridlayout2.setObjectName("gridlayout2")

        self.xscale = QtGui.QComboBox(self.tab_4)
        self.xscale.setObjectName("xscale")
        self.gridlayout2.addWidget(self.xscale,3,1,1,1)

        self.xtitle = QtGui.QLineEdit(self.tab_4)
        self.xtitle.setObjectName("xtitle")
        self.gridlayout2.addWidget(self.xtitle,0,1,1,1)

        self.textLabel5 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel5.sizePolicy().hasHeightForWidth())
        self.textLabel5.setSizePolicy(sizePolicy)
        self.textLabel5.setObjectName("textLabel5")
        self.gridlayout2.addWidget(self.textLabel5,1,0,1,1)

        self.textLabel4_5 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel4_5.sizePolicy().hasHeightForWidth())
        self.textLabel4_5.setSizePolicy(sizePolicy)
        self.textLabel4_5.setObjectName("textLabel4_5")
        self.gridlayout2.addWidget(self.textLabel4_5,0,0,1,1)

        self.textLabel7_3 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel7_3.sizePolicy().hasHeightForWidth())
        self.textLabel7_3.setSizePolicy(sizePolicy)
        self.textLabel7_3.setObjectName("textLabel7_3")
        self.gridlayout2.addWidget(self.textLabel7_3,3,0,1,1)

        self.xfrom = QtGui.QLineEdit(self.tab_4)
        self.xfrom.setObjectName("xfrom")
        self.gridlayout2.addWidget(self.xfrom,1,1,1,1)

        self.xto = QtGui.QLineEdit(self.tab_4)
        self.xto.setObjectName("xto")
        self.gridlayout2.addWidget(self.xto,2,1,1,1)

        self.textLabel6_4 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel6_4.sizePolicy().hasHeightForWidth())
        self.textLabel6_4.setSizePolicy(sizePolicy)
        self.textLabel6_4.setObjectName("textLabel6_4")
        self.gridlayout2.addWidget(self.textLabel6_4,2,0,1,1)
        self.hboxlayout10.addLayout(self.gridlayout2)
        self.vboxlayout9.addLayout(self.hboxlayout10)
        self.vboxlayout8.addLayout(self.vboxlayout9)

        self.vboxlayout10 = QtGui.QVBoxLayout()
        self.vboxlayout10.setMargin(0)
        self.vboxlayout10.setSpacing(0)
        self.vboxlayout10.setObjectName("vboxlayout10")

        self.textLabel1_2 = QtGui.QLabel(self.tab_4)
        self.textLabel1_2.setObjectName("textLabel1_2")
        self.vboxlayout10.addWidget(self.textLabel1_2)

        self.hboxlayout11 = QtGui.QHBoxLayout()
        self.hboxlayout11.setMargin(0)
        self.hboxlayout11.setSpacing(0)
        self.hboxlayout11.setObjectName("hboxlayout11")

        spacerItem5 = QtGui.QSpacerItem(8,20,QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Minimum)
        self.hboxlayout11.addItem(spacerItem5)

        self.gridlayout3 = QtGui.QGridLayout()
        self.gridlayout3.setMargin(0)
        self.gridlayout3.setSpacing(0)
        self.gridlayout3.setObjectName("gridlayout3")

        self.yscale = QtGui.QComboBox(self.tab_4)
        self.yscale.setObjectName("yscale")
        self.gridlayout3.addWidget(self.yscale,3,1,1,1)

        self.ytitle = QtGui.QLineEdit(self.tab_4)
        self.ytitle.setObjectName("ytitle")
        self.gridlayout3.addWidget(self.ytitle,0,1,1,1)

        self.textLabel5_3 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel5_3.sizePolicy().hasHeightForWidth())
        self.textLabel5_3.setSizePolicy(sizePolicy)
        self.textLabel5_3.setObjectName("textLabel5_3")
        self.gridlayout3.addWidget(self.textLabel5_3,1,0,1,1)

        self.textLabel4_4 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel4_4.sizePolicy().hasHeightForWidth())
        self.textLabel4_4.setSizePolicy(sizePolicy)
        self.textLabel4_4.setObjectName("textLabel4_4")
        self.gridlayout3.addWidget(self.textLabel4_4,0,0,1,1)

        self.textLabel7_2 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel7_2.sizePolicy().hasHeightForWidth())
        self.textLabel7_2.setSizePolicy(sizePolicy)
        self.textLabel7_2.setObjectName("textLabel7_2")
        self.gridlayout3.addWidget(self.textLabel7_2,3,0,1,1)

        self.yfrom = QtGui.QLineEdit(self.tab_4)
        self.yfrom.setObjectName("yfrom")
        self.gridlayout3.addWidget(self.yfrom,1,1,1,1)

        self.yto = QtGui.QLineEdit(self.tab_4)
        self.yto.setObjectName("yto")
        self.gridlayout3.addWidget(self.yto,2,1,1,1)

        self.textLabel6_3 = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel6_3.sizePolicy().hasHeightForWidth())
        self.textLabel6_3.setSizePolicy(sizePolicy)
        self.textLabel6_3.setObjectName("textLabel6_3")
        self.gridlayout3.addWidget(self.textLabel6_3,2,0,1,1)
        self.hboxlayout11.addLayout(self.gridlayout3)
        self.vboxlayout10.addLayout(self.hboxlayout11)
        self.vboxlayout8.addLayout(self.vboxlayout10)

        spacerItem6 = QtGui.QSpacerItem(163,73,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout8.addItem(spacerItem6)
        self.tabs.addTab(self.tab_4, "")

        self.tab_7 = QtGui.QWidget()
        self.tab_7.setObjectName("tab_7")
        self.tabs.addTab(self.tab_7, "")
        self.hboxlayout5.addWidget(self.tabs)
        self.right.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2),self.right)

        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setMovable(False)
        self.toolBar.setOrientation(QtCore.Qt.Horizontal)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(self.toolBar)

        self.action_new = QtGui.QAction(MainWindow)
        self.action_new.setIcon(QtGui.QIcon(":/images/general/new.png"))
        self.action_new.setObjectName("action_new")

        self.action_open = QtGui.QAction(MainWindow)
        self.action_open.setIcon(QtGui.QIcon(":/images/general/open.png"))
        self.action_open.setObjectName("action_open")

        self.action_save = QtGui.QAction(MainWindow)
        self.action_save.setIcon(QtGui.QIcon(":/images/general/save.png"))
        self.action_save.setObjectName("action_save")

        self.action_saveas = QtGui.QAction(MainWindow)
        self.action_saveas.setIcon(QtGui.QIcon(":/images/general/saveas.png"))
        self.action_saveas.setObjectName("action_saveas")

        self.actionNew_Worksheet = QtGui.QAction(MainWindow)
        self.actionNew_Worksheet.setIcon(QtGui.QIcon(":/images/general/new-worksheet.png"))
        self.actionNew_Worksheet.setObjectName("actionNew_Worksheet")

        self.actionNew_Graph = QtGui.QAction(MainWindow)
        self.actionNew_Graph.setIcon(QtGui.QIcon(":/images/general/new-graph.png"))
        self.actionNew_Graph.setObjectName("actionNew_Graph")

        self.actionNew_Folder = QtGui.QAction(MainWindow)
        self.actionNew_Folder.setIcon(QtGui.QIcon(":/images/general/new-folder.png"))
        self.actionNew_Folder.setObjectName("actionNew_Folder")
        self.menu_Project.addAction(self.action_new)
        self.menu_Project.addAction(self.action_open)
        self.menu_Project.addAction(self.action_save)
        self.menu_Project.addAction(self.action_saveas)
        self.menubar.addAction(self.menu_Project.menuAction())
        self.menubar.addAction(self.menu_Edit.menuAction())
        self.toolBar.addAction(self.action_new)
        self.toolBar.addAction(self.action_open)
        self.toolBar.addAction(self.action_save)
        self.toolBar.addAction(self.action_saveas)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionNew_Worksheet)
        self.toolBar.addAction(self.actionNew_Graph)
        self.toolBar.addAction(self.actionNew_Folder)
        self.label.setBuddy(self.treeView)
        self.label_2.setBuddy(self.listView)
        self.label_3.setBuddy(self.listView_2)
        self.textLabel5_2.setBuddy(self.lstyle)
        self.textLabel6_2.setBuddy(self.lwidth)
        self.textLabel4_2.setBuddy(self.ltype)
        self.textLabel4.setBuddy(self.shape)
        self.textLabel4_3.setBuddy(self.fill)
        self.textLabel7.setBuddy(self.color)
        self.textLabel6.setBuddy(self.size)
        self.textLabel4_2_2.setBuddy(self.group)
        self.textLabel5.setBuddy(self.xfrom)
        self.textLabel4_5.setBuddy(self.xtitle)
        self.textLabel7_3.setBuddy(self.xscale)
        self.textLabel6_4.setBuddy(self.xto)
        self.textLabel5_3.setBuddy(self.yfrom)
        self.textLabel4_4.setBuddy(self.ytitle)
        self.textLabel7_2.setBuddy(self.textLabel7_2)

        self.retranslateUi(MainWindow)
        self.tabs.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def tr(self, string):
        return QtGui.QApplication.translate("MainWindow", string, None, QtGui.QApplication.UnicodeUTF8)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(self.tr("MainWindow"))
        self.menu_Project.setTitle(self.tr("&Project"))
        self.menu_Edit.setTitle(self.tr("&Edit"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_5), self.tr("Script"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_6), self.tr("Log"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), self.tr("Project"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), self.tr("Changes"))
        self.add_button.setText(self.tr("Add"))
        self.toolButton.setText(self.tr("Replace"))
        self.label.setText(self.tr("<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:Sans Serif; font-size:9pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">worksheet</span></p></body></html>"))
        self.label_2.setText(self.tr("<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:Sans Serif; font-size:9pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">x axis</span></p></body></html>"))
        self.label_3.setText(self.tr("<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:Sans Serif; font-size:9pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">y axis</span></p></body></html>"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_3), self.tr("Data"))
        self.textLabel1_3.setText(self.tr("<b>line</b>"))
        self.textLabel5_2.setText(self.tr("style"))
        self.textLabel6_2.setText(self.tr("width"))
        self.textLabel4_2.setText(self.tr("type"))
        self.ltype.addItem(self.tr("(no line)"))
        self.ltype.addItem(self.tr("straight"))
        self.ltype.addItem(self.tr("spline"))
        self.textLabel1_4.setText(self.tr("<b>symbol</b>"))
        self.textLabel4.setText(self.tr("shape"))
        self.fill.addItem(self.tr("filled"))
        self.fill.addItem(self.tr("open"))
        self.textLabel4_3.setText(self.tr("fill"))
        self.textLabel7.setText(self.tr("color"))
        self.textLabel6.setText(self.tr("size"))
        self.textLabel4_2_2.setText(self.tr("<b>group</b>"))
        self.group.addItem(self.tr("identical"))
        self.group.addItem(self.tr("series"))
        self.tabs.setTabText(self.tabs.indexOf(self.Style), self.tr("Style"))
        self.textLabel1.setText(self.tr("<b>x axis</b>"))
        self.xscale.addItem(self.tr("linear"))
        self.xscale.addItem(self.tr("log"))
        self.textLabel5.setText(self.tr("from"))
        self.textLabel4_5.setText(self.tr("title"))
        self.textLabel7_3.setText(self.tr("scale"))
        self.textLabel6_4.setText(self.tr("to"))
        self.textLabel1_2.setText(self.tr("<b>y axis</b>"))
        self.yscale.addItem(self.tr("linear"))
        self.yscale.addItem(self.tr("log"))
        self.textLabel5_3.setText(self.tr("from"))
        self.textLabel4_4.setText(self.tr("title"))
        self.textLabel7_2.setText(self.tr("scale"))
        self.textLabel6_3.setText(self.tr("to"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_4), self.tr("Axes"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_7), self.tr("Fit"))
        self.action_new.setText(self.tr("New &Project"))
        self.action_open.setText(self.tr("&Open Project"))
        self.action_save.setText(self.tr("&Save Project"))
        self.action_saveas.setText(self.tr("&Save Project &As..."))
        self.actionNew_Worksheet.setText(self.tr("New &Worksheet"))
        self.actionNew_Graph.setText(self.tr("New &Graph"))
        self.actionNew_Folder.setText(self.tr("New &Folder"))
