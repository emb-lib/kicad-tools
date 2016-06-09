#!/usr/bin/python3
# coding: utf-8


import sys
import os
import re
import yaml
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, QSplitter, 
                             QTableWidget, QTableWidgetItem, QCommonStyle, QTreeWidget, QTreeWidgetItem,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication)

from PyQt5.QtGui import (QIcon, QBrush, QColor)
from PyQt5.QtCore import QSettings


#-------------------------------------------------------------------------------
class Inspector(QTreeWidget):
    
    def __init__(self, parent):
        super().__init__(parent)
        #self.setAlternatingRowColors(True)
        self.setIndentation(16)
        self.setColumnCount(2)
        #self.header().resizeSection(0, 150)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        #self.header().setStretchLastSection(False)
        self.setHeaderLabels( ('Property', 'Value') );
        std_items   = self.addParent(self, 0, 'Standard', 'slon')
        usr_items   = self.addParent(self, 0, 'User Defined', 'mamont')
        field_items = self.addParent(self, 0, 'Field Details', '')
        
        self.addChild(std_items, 0, 'Ref', '?')
        self.addChild(std_items, 0, 'Value', '~')
        self.addChild(std_items, 0, 'Footprint', '~')
        self.addChild(std_items, 0, 'DocSheet', '~')
    
        self.addChild(usr_items, 0, 'Name', '?')
        self.addChild(usr_items, 0, 'Type', '?')

        self.addChild(field_items, 0, '<empty>', '?')
            
        
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        item.setExpanded (True)
#       item.setBackground( 0, QBrush(QColor('#FFDCA4'), Qt.SolidPattern) )
#       item.setBackground( 1, QBrush(QColor('#FFDCA4'), Qt.SolidPattern) )
        return item
        
        
    def addChild(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        #item.setCheckState (column, Qt.Unchecked)
        return item
            
#-------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):
        
        self.cfg = yaml.load( open('kscm.yml') )
        
        #----------------------------------------------------
        #
        #    Main Window
        #
        work_zone = QWidget(self)
        Layout    = QHBoxLayout(work_zone)
        self.setCentralWidget(work_zone)
        
        exitAction = QAction(QIcon('exit24.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)        
        
        self.statusBar().showMessage('Ready')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)        
        
        self.CmpTabBox    = QGroupBox('Components', self)
        self.CmpTabLayout = QVBoxLayout(self.CmpTabBox)
        self.CmpTabLayout.setContentsMargins(4,10,4,4)
        self.CmpTabLayout.setSpacing(10)
        
        #self.CmpTabLayout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.CmpTabLayout.setSizeConstraint(QVBoxLayout.SetMaximumSize)
        
        #----------------------------------------------------
        #
        #    Components table
        #
        self.CmpTable = QTableWidget(0, 2, self)
        
        self.CmpTable.cellActivated.connect(self.cellActivated)
        
        self.CmpTable.setSelectionBehavior(QAbstractItemView.SelectRows)  # select whole row
        self.CmpTable.setEditTriggers(QAbstractItemView.NoEditTriggers)   # disable edit cells
        
        self.CmpTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.CmpTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        
        cmptab = self.cfg['ComponentTable']
        
        self.CmpTable.setColumnWidth(0, cmptab['RefWidth'])
        self.CmpTable.setColumnWidth(1, cmptab['NameWidth'])
        self.CmpTable.setFixedWidth(cmptab['Width'])
        self.CmpTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.CmpTable.verticalHeader().setDefaultSectionSize(20)
        self.CmpTable.setHorizontalHeaderLabels( ('Ref', 'Name') )
        #self.CmpTable.resize( 100, self.CmpTable.height() )
        
        b   = read_file('det-1/det-1.sch')
        rcl = raw_cmp_list(b)
        ipl = self.cfg['Ignore']
        self.CmpDict = cmp_dict(rcl, ipl)
        self.update_cmp_list(self.CmpDict)
        self.CmpTable.show()
        #----------------------------------------------------
        
        self.CmpApplyButton = QPushButton('Apply', self)
        #self.CmpApplyButton.resize( 100, self.CmpApplyButton.height() )
        
        self.CmpTabLayout.addWidget(self.CmpTable)
        self.CmpTabLayout.addWidget(self.CmpApplyButton)
        
                
        #----------------------------------------------------
        #
        #    Select View
        #
        self.SelectView = QTreeWidget(self)
        self.SelectView.setColumnCount(2)
        self.SelectView.setHeaderLabels( ('Property', 'Value') );

        self.SVTopItem = QTreeWidgetItem(self.SelectView)
        self.SVTopItem.setText(1, 'Standard')
        
        self.SVItem1 = QTreeWidgetItem(self.SVTopItem)
        self.SVItem1.setText(0, 'sub-slonick')
        
        #----------------------------------------------------
        #
        #    Inspector
        #
        self.Inspector = Inspector(self)
        
        self.InspectorBox    = QGroupBox('Inspector', self)
        self.InspectorLayout = QVBoxLayout(self.InspectorBox)
        self.InspectorLayout.setContentsMargins(4,10,4,4)
        self.InspectorLayout.setSpacing(10)
        
        self.InspectorLayout.addWidget(self.Inspector)
        #self.InspectorLayout.addStretch()
                
        #----------------------------------------------------
        self.Splitter = QSplitter(self)
        #Splitter.addWidget(self.CmpTabBox)    
        self.Splitter.addWidget(self.SelectView)   
        self.Splitter.addWidget(self.InspectorBox) 
                 
        self.centralWidget().layout().addWidget(self.CmpTabBox)    
        self.centralWidget().layout().addWidget(self.Splitter)
        
#       self.centralWidget().layout().addWidget(self.CmpTabBox)
#       self.centralWidget().layout().addWidget(self.SelectView)
#       #self.centralWidget().layout().addStretch()
#       self.centralWidget().layout().addWidget(self.InspectorBox)


        #----------------------------------------------------
        #
        #    Window
        #
        self.setWindowTitle('KiCad Schematic Component Manager')
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        print(Settings.allKeys())
        if Settings.contains('geometry'):
            self.restoreGeometry( Settings.value('geometry') )
        else:
            self.setGeometry(100, 100, 1024, 768)

        if Settings.contains('splitter'):
            self.Splitter.restoreState( Settings.value('splitter') )
            
        self.show()
        
        
    def closeEvent(self, event):
        print('close app')
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        Settings.setValue( 'geometry', self.saveGeometry() )
        Settings.setValue( 'splitter', self.Splitter.saveState() )
        QWidget.closeEvent(self, event)
        
        
    def cellActivated(self, row, col):
        items = self.CmpTable.selectedItems()
        for i in items:
            if i.column() == 0:
                print( i.data(Qt.DisplayRole) )
    
    def update_cmp_list(self, cd):
        
        keys = list( cd.keys() )
        keys.sort( key=split_alphanumeric )    

        self.CmpTable.setRowCount(len(cd))
            
        for idx, k in enumerate( keys ):
            Name = QTableWidgetItem(cd[k][0].LibName)
            Ref  = QTableWidgetItem(k)
          #  print(ref + ' ' + cd[ref].Name)
            self.CmpTable.setItem(idx, 0, Ref)
            self.CmpTable.setItem(idx, 1, Name)
        

#-------------------------------------------------------------------------------
class ComponentField:
    
    def __init__(self, rec):

        self.InnerCode = rec[0]
        
        if self.InnerCode == '0':
            self.Name = 'Ref'
        elif self.InnerCode == '1':
            self.Name = 'Value'
        elif self.InnerCode == '2':
            self.Name = 'Footprint'
        elif self.InnerCode == '3':
            self.Name = 'DocSheet'
        else:
            self.Name = rec[11]
            
        self.Text        = rec[1]
        self.Orientation = rec[2]
        self.PosX        = rec[3]
        self.PosY        = rec[4]
        self.FontSize    = rec[5]
        self.Visible     = True if int(rec[6]) == 0 else False
        self.HJustify    = rec[7]
        self.VJustify    = rec[8]
        self.FontItalic  = rec[9]
        self.FontBold    = rec[10]
    
class Component:
    
    def __init__(self):
        self.Ref = '~'
        self.Name = '~'
        self.Footprint = '~'
        
    def parse_comp(self, rec):
        r = re.search('L ([\w-]+) ([\w#]+)', rec)
        if r:
            self.LibName, self.Ref = r.groups()
        else:
            print('E: invalid component L record, rec: "' + rec + '"')
            sys.exit(1)
            
        r = re.search('U (\d+) (\d+) ([\w\d]+)', rec)

        if r:
            self.PartNo, self.mm, self.Timestamp = r.groups()
        else:
            print('E: invalid component U record, rec: "' + rec + '"')
            sys.exit(1)

        r = re.search('P (\d+) (\d+)', rec)
        if r:
            self.PosX, self.PosY = r.groups()
        else:
            print('E: invalid component P record, rec: "' + rec + '"')
            sys.exit(1)
            
        cfre = re.compile('F\s+(\d+)\s+\"(.*?)\"\s+(H|V)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([LRCBT])\s+([LRCBT])([NI])([NB])\s+(?:\"(.*)\")*')
        r = re.findall(cfre, rec)
        
        r.sort(key=lambda x: int(x[0]))
        
        self.Fields = []
        for i in r:
            self.Fields.append( ComponentField(i) )
        
#       for i in self.Fields:
#           print(vars(i))
#
#       print('***********************')
            
        
#-------------------------------------------------------------------------------
def split_alphanumeric(x):
    r = re.split('(\d+)', x)
    
    return ( r[0], int(r[1]) )
#-------------------------------------------------------------------------------
def read_file(fname):
    with open(fname, 'rb') as f:
        b = f.read()
        
    return b.decode()
#-------------------------------------------------------------------------------
def raw_cmp_list(s):
    pattern = '\$Comp\n((?:.*\n)+?)\$EndComp'
    res = re.findall(pattern, s)
    
    return res

#-------------------------------------------------------------------------------
def cmp_dict(rcl, ipl):   # rcl: raw component list; ipl: ignore pattern list
    
    cdict = {}
    
    for i in rcl:
        cmp = Component()
        cmp.parse_comp(i)
        ignore = False
        for ip in ipl:
            r = re.search(ip+'.*\d+', cmp.Ref)
            if r:
                ignore = True
                continue
           
        if ignore:
            continue
            
        if not cmp.Ref in cdict:
            cdict[cmp.Ref] = []

        cdict[cmp.Ref].append(cmp)
     
        
           
    return cdict
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    app  = QApplication(sys.argv)
    app.setStyleSheet('QGroupBox {\
                           border: 1px solid gray;\
                           border-radius: 3px;\
                           margin: 4px;\
                           padding: 4px;\
                       }\
                       QGroupBox::title {\
                           subcontrol-origin: margin;\
                           subcontrol-position: top left;\
                           padding: 2px;\
                           left: 20px;\
                       }\
                      Inspector {\
                        alternate-background-color: #ffffd0;\
                      }\
                       Inspector {\
                           show-decoration-selected: 1;\
                       }\
                       QTreeView::item {\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-bottom-color: transparent;\
                       }\
                       QTreeView::item:has-children {\
                           left: 18px;\
                           background-color: #FFDCA4;\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-right-color: transparent;\
                           border-bottom-color: transparent;\
                       }\
                       QTreeWidget::item:hover {\
                           background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);\
                           border: 1px solid #bfcde4;\
                       }\
                       QTreeWidget::item:selected {\
                           border: 1px solid #567dbc;\
                       }\
                       QTreeWidget::item:selected:active{\
                           background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);\
                       }\
                       QTreeWidget::item:selected:!active {\
                           background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);\
                       }'
                      )
    
    
     #background-color: #fffff0;\
    #                           border-top-color: transparent;\
    #                           border-bottom-color: transparent;\
    
    mwin = MainWindow()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


