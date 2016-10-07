# coding: utf-8


import sys
import os
import re
import shutil

from utils import *

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction, QComboBox,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, QSplitter, QStyledItemDelegate,
                             QAbstractItemDelegate, 
                             QTableWidget, QTableWidgetItem, QCommonStyle, QTreeWidget, QTreeWidgetItem,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication,
                             QFileDialog, QInputDialog, QMessageBox)

from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent, QModelIndex, QItemSelectionModel

#-------------------------------------------------------------------------------
class ComponentsTable(QTableWidget):
    
    cells_chosen = pyqtSignal([list])
    mouse_click  = pyqtSignal([str])
    file_load    = pyqtSignal()
    cmps_updated = pyqtSignal([dict])
    
    def __init__(self, parent):
        super().__init__(0, 2, parent)
        
        self.cellActivated.connect(self.cell_chosen)
        self.cellClicked.connect  (self.cell_chosen)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # select whole row
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)   # disable edit cells

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)
        self.setHorizontalHeaderLabels( ('Ref', 'Description') )
        self.setTabKeyNavigation(False)        
        
#       for r in range(self.rowCount()):
#           for c in range(self.columnCount()):
#               self.item(r, c).setFocusPolicy(Qt.NoFocus)
        
           
    #---------------------------------------------------------------------------    
    def mousePressEvent(self, e):
        print('--------------   mouse press event CmpTable -------------')
        self.mouse_click.emit('CmpTable')
        QTableWidget.mousePressEvent(self, e)
    #---------------------------------------------------------------------------    
    def cell_chosen(self, row, col):
        items = self.selectedItems()
        if len(items) == 0:
            return
            
        refs = []
        for i in items:
            if i.column() == 0:
                refs.append( self.CmpDict[i.data(Qt.DisplayRole)] )
        
        self.cells_chosen.emit(refs)
    #---------------------------------------------------------------------------    
    def select_comps_slot(self, refs):
        self.clearSelection()
        
        #print('select_comps_slot', refs)
        
        sel_mode = self.selectionMode()
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        for ref in refs:
            for row in range( self.rowCount() ):
                reftext = self.item(row, 0).text()
                if ref == reftext:
                    #print(ref, reftext)
                    self.selectRow(row)
                    #self.item(row, 0).setSelected(True)
                   
        self.setSelectionMode(sel_mode)
        self.cell_chosen(0, 0)
    #---------------------------------------------------------------------------    
    def load_file(self, fname):
                
        from cmpmgr import CmpMgr
        
        fname = os.path.abspath(fname)
        self.CmpDict = CmpMgr.load_file(fname)
        self.update_cmp_list(self.CmpDict)
        self.selectRow(0)
        self.cell_chosen(0, 0)
        CmpMgr.set_curr_file_path(fname)
        self.file_load.emit()
        self.cmps_updated.emit( self.CmpDict )
    #---------------------------------------------------------------------------    
    def reload_file(self, fname):
        self.clear()
        self.load_file(fname)
    #---------------------------------------------------------------------------    
    def cmp_dict(self):
        return self.CmpDict
    #---------------------------------------------------------------------------    
    def update_cmp_list_slot(self):
        self.update_cmp_list(self.CmpDict)
        self.cmps_updated.emit( self.CmpDict )
        self.cell_chosen(0,0)
    #---------------------------------------------------------------------------    
    def update_cmp_list(self, cd):

        keys = list( cd.keys() )
        keys.sort( key=split_alphanumeric )    

        self.setRowCount(len(cd))

        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        if Settings.contains('component-view'):
            CmpViewDict = Settings.value('component-view')
        else:
            CmpViewDict = {}
        
        for idx, k in enumerate( keys ):
            Ref  = QTableWidgetItem(k)
            res  = re.match('([a-zA-Z]+)\d+', k)
            Pattern = '$LibRef'
            if res:
                RefBase = res.groups()[0]
                if RefBase in CmpViewDict.keys():
                    Pattern = CmpViewDict[RefBase]
            
            cmp = cd[k][0]
            info_str = cmp.get_str_from_pattern(Pattern)
            Name = QTableWidgetItem(info_str)
            self.setItem(idx, 0, Ref)
            self.setItem(idx, 1, Name)
#-------------------------------------------------------------------------------

