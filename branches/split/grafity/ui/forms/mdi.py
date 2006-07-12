# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'unknown'
#
# Created: Wed Jul 12 23:49:15 2006
#      by: PyQt4 UI code generator 4.0
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,952,703).size()).expandedTo(MainWindow.minimumSizeHint()))

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
        self.statusbar.setGeometry(QtCore.QRect(0,679,952,24))
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

        self.textEdit = QtGui.QTextEdit(self.tab_5)
        self.textEdit.setObjectName("textEdit")
        self.hboxlayout.addWidget(self.textEdit)
        self.tabWidget_3.addTab(self.tab_5, "")
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

        self.treeView = QtGui.QTreeView(self.tab)
        self.treeView.setObjectName("treeView")
        self.hboxlayout2.addWidget(self.treeView)
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

        self.actionNew_Project = QtGui.QAction(MainWindow)
        self.actionNew_Project.setIcon(QtGui.QIcon(":/images/general/new.png"))
        self.actionNew_Project.setObjectName("actionNew_Project")

        self.action_Open_Project = QtGui.QAction(MainWindow)
        self.action_Open_Project.setIcon(QtGui.QIcon(":/images/general/open.png"))
        self.action_Open_Project.setObjectName("action_Open_Project")

        self.action_Save_Project = QtGui.QAction(MainWindow)
        self.action_Save_Project.setIcon(QtGui.QIcon(":/images/general/save.png"))
        self.action_Save_Project.setObjectName("action_Save_Project")

        self.action_Save_Project_As = QtGui.QAction(MainWindow)
        self.action_Save_Project_As.setIcon(QtGui.QIcon(":/images/general/saveas.png"))
        self.action_Save_Project_As.setObjectName("action_Save_Project_As")
        self.menu_Project.addAction(self.actionNew_Project)
        self.menu_Project.addAction(self.action_Open_Project)
        self.menu_Project.addAction(self.action_Save_Project)
        self.menu_Project.addAction(self.action_Save_Project_As)
        self.menubar.addAction(self.menu_Project.menuAction())
        self.toolBar.addAction(self.actionNew_Project)
        self.toolBar.addAction(self.action_Open_Project)
        self.toolBar.addAction(self.action_Save_Project)
        self.toolBar.addAction(self.action_Save_Project_As)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def tr(self, string):
        return QtGui.QApplication.translate("MainWindow", string, None, QtGui.QApplication.UnicodeUTF8)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(self.tr("MainWindow"))
        self.menu_Project.setTitle(self.tr("&Project"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_5), self.tr("Script"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), self.tr("Project"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), self.tr("Changes"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_3), self.tr("Tab 1"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_4), self.tr("Tab 2"))
        self.actionNew_Project.setText(self.tr("New &Project"))
        self.action_Open_Project.setText(self.tr("&Open Project"))
        self.action_Save_Project.setText(self.tr("&Save Project"))
        self.action_Save_Project_As.setText(self.tr("&Save Project &As..."))
