#!/usr/bin/python3
# coding: utf-8


import re
import sys
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, 
                             QTableWidget, QTableWidgetItem, QCommonStyle,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication)

from PyQt5.QtGui import QIcon

#-------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):
        
        #----------------------------------------------------
        #
        #    Main Window
        #
        work_zone = QWidget(self)
        Layout    = QHBoxLayout(work_zone)
        #work_zone.setLayout(Layout)
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
        self.CmpTable.setColumnWidth(0, 60)
        self.CmpTable.setColumnWidth(1, 153)
        self.CmpTable.setFixedWidth(260)
        self.CmpTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.CmpTable.verticalHeader().setDefaultSectionSize(20)
        self.CmpTable.setHorizontalHeaderLabels( ('Ref', 'Name') )
        #self.CmpTable.resize( 100, self.CmpTable.height() )
        
        b   = read_file('det-1/det-1.sch')
        rcl = raw_cmp_list(b)
        self.CmpDict = cmp_dict(rcl)
        self.update_cmp_list(self.CmpDict)
        self.CmpTable.show()
        #----------------------------------------------------
        
        self.CmpApplyButton = QPushButton('Apply', self)
        #self.CmpApplyButton.resize( 100, self.CmpApplyButton.height() )
        
        self.CmpTabLayout.addWidget(self.CmpTable)
        self.CmpTabLayout.addWidget(self.CmpApplyButton)
        self.centralWidget().layout().addWidget(self.CmpTabBox)
        self.centralWidget().layout().addStretch(1)
        
                
        #----------------------------------------------------
        #
        #    Window
        #
        self.setWindowTitle('KiCad Schematic Component Manager')
        self.setGeometry(100, 100, 1024, 768)
        self.show()
        
        
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
            Name = QTableWidgetItem(cd[k].Name)
            Ref  = QTableWidgetItem(k)
          #  print(ref + ' ' + cd[ref].Name)
            self.CmpTable.setItem(idx, 0, Ref)
            self.CmpTable.setItem(idx, 1, Name)
            
        

#-------------------------------------------------------------------------------
class Component:
    
    def __init__(self):
        self.Ref = '~'
        self.Name = '~'
        self.Footprint = '~'
        
    def parse_comp(self, rec):
        r = re.search('L ([\w-]+) ([\w#]+)', rec)
        if r:
            self.Name, self.Ref = r.groups()
        else:
            print('E: invalid component L record, rec: "' + rec + '"')
            sys.exit(1)
        
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
def cmp_dict(rcl):
    
    cdict = {}
    
    for i in rcl:
        cmp = Component()
        cmp.parse_comp(i)
        cdict[cmp.Ref] = cmp
        
    return cdict
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    app  = QApplication(sys.argv)
    app.setStyleSheet('QGroupBox {\
                           border: 1px solid gray;\
                           border-radius: 3px;\
                           margin: 10px;\
                           padding: 4px;\
                       }\
                       QGroupBox::title {\
                           subcontrol-origin: margin;\
                           subcontrol-position: top left;\
                           padding: 2px;\
                           left: 20px;\
                       }' )
    mwin = MainWindow()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


