#!/usr/bin/python3
# coding: utf-8


import re
import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit,
    QTextEdit, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QApplication)

#-------------------------------------------------------------------------------
class MainForm(QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):
        
        self.Layout = QGridLayout(self)
        self.CmpTable = QTableWidget(0, 2, self)
        
        self.CmpTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.CmpTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.CmpTable.verticalHeader().setDefaultSectionSize(20)
        self.CmpTable.setHorizontalHeaderLabels( ('Ref', 'Name') )
        
        self.Layout.addWidget(self.CmpTable, 0, 0)
        
        b   = read_file('det-1/det-1.sch')
        rcl = raw_cmp_list(b)
        self.CmpDict = cmp_dict(rcl)
        self.update_cmp_list(self.CmpDict)
        self.CmpTable.show()
        
        
        self.setWindowTitle('KiCad Schematic Component Manager')
        self.setGeometry(100, 100, 1024, 768)
        self.show()
        
        #self.CmpTable.
        
        
    
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

    app = QApplication(sys.argv)
    mform = MainForm()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


