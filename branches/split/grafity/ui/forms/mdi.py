# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'unknown'
#
# Created: Thu Jul 13 17:16:29 2006
#      by: PyQt4 UI code generator snapshot-20060424
#
# WARNING! All changes made in this file will be lost!

import sys
from grafity.ui.console import ConsoleTextEdit
from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,952,693).size()).expandedTo(MainWindow.minimumSizeHint()))

        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0,0,952,31))
        self.menubar.setObjectName("menubar")

        self.menu_Project = QtGui.QMenu(self.menubar)
        self.menu_Project.setObjectName("menu_Project")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setGeometry(QtCore.QRect(0,669,952,24))
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.bottom = QtGui.QDockWidget(MainWindow)
        self.bottom.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.bottom.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
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

        self.hboxlayout = QtGui.QHBoxLayout(self.tab_5)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(0)
        self.hboxlayout.setObjectName("hboxlayout")

        self.console = ConsoleTextEdit(self.tab_5)
        self.console.setObjectName("console")
        self.hboxlayout.addWidget(self.console)
        self.tabWidget_3.addTab(self.tab_5, "")

        self.tab_6 = QtGui.QWidget()
        self.tab_6.setObjectName("tab_6")
        self.tabWidget_3.addTab(self.tab_6, "")
        self.vboxlayout.addWidget(self.tabWidget_3)
        self.bottom.setWidget(self.dockWidgetContents_3)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(8),self.bottom)

        self.left = QtGui.QDockWidget(MainWindow)
        self.left.setMinimumSize(QtCore.QSize(16,16))
        self.left.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.left.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.left.setObjectName("left")

        self.dockWidgetContents = QtGui.QWidget(self.left)
        self.dockWidgetContents.setObjectName("dockWidgetContents")

        self.hboxlayout1 = QtGui.QHBoxLayout(self.dockWidgetContents)
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(0)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.tabWidget = QtGui.QTabWidget(self.dockWidgetContents)
        self.tabWidget.setTabPosition(QtGui.QTabWidget.West)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")

        self.hboxlayout2 = QtGui.QHBoxLayout(self.tab)
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(0)
        self.hboxlayout2.setObjectName("hboxlayout2")

        self.tree = QtGui.QTreeView(self.tab)
        self.tree.setObjectName("tree")
        self.hboxlayout2.addWidget(self.tree)
        self.tabWidget.addTab(self.tab, "")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.hboxlayout3 = QtGui.QHBoxLayout(self.tab_2)
        self.hboxlayout3.setMargin(0)
        self.hboxlayout3.setSpacing(0)
        self.hboxlayout3.setObjectName("hboxlayout3")

        self.listWidget = QtGui.QListWidget(self.tab_2)
        self.listWidget.setObjectName("listWidget")
        self.hboxlayout3.addWidget(self.listWidget)
        self.tabWidget.addTab(self.tab_2, "")
        self.hboxlayout1.addWidget(self.tabWidget)
        self.left.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1),self.left)

        self.right = QtGui.QDockWidget(MainWindow)
        self.right.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.right.setObjectName("right")

        self.dockWidgetContents_2 = QtGui.QWidget(self.right)
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")

        self.hboxlayout4 = QtGui.QHBoxLayout(self.dockWidgetContents_2)
        self.hboxlayout4.setMargin(0)
        self.hboxlayout4.setSpacing(0)
        self.hboxlayout4.setObjectName("hboxlayout4")

        self.tabWidget_2 = QtGui.QTabWidget(self.dockWidgetContents_2)
        self.tabWidget_2.setTabPosition(QtGui.QTabWidget.East)
        self.tabWidget_2.setObjectName("tabWidget_2")

        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.tabWidget_2.addTab(self.tab_3, "")

        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.tabWidget_2.addTab(self.tab_4, "")
        self.hboxlayout4.addWidget(self.tabWidget_2)
        self.right.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2),self.right)

        self.toolBar = QtGui.QToolBar(MainWindow)
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
        self.menu_Project.addAction(self.action_new)
        self.menu_Project.addAction(self.action_open)
        self.menu_Project.addAction(self.action_save)
        self.menu_Project.addAction(self.action_saveas)
        self.menubar.addAction(self.menu_Project.menuAction())
        self.toolBar.addAction(self.action_new)
        self.toolBar.addAction(self.action_open)
        self.toolBar.addAction(self.action_save)
        self.toolBar.addAction(self.action_saveas)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def tr(self, string):
        return QtGui.QApplication.translate("MainWindow", string, None, QtGui.QApplication.UnicodeUTF8)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(self.tr("MainWindow"))
        self.menu_Project.setTitle(self.tr("&Project"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_5), self.tr("Script"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_6), self.tr("Log"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), self.tr("Project"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), self.tr("Changes"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_3), self.tr("Tab 1"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_4), self.tr("Tab 2"))
        self.action_new.setText(self.tr("New &Project"))
        self.action_open.setText(self.tr("&Open Project"))
        self.action_save.setText(self.tr("&Save Project"))
        self.action_saveas.setText(self.tr("&Save Project &As..."))
