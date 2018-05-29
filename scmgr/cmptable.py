# coding: utf-8

#-------------------------------------------------------------------------------
#
#    Project: KiCad Tools
#    
#    Name:    KiCad Schematic Component Manager
#   
#    Purpose: Table representation and manual selection of components
#
#    Copyright (c) 2016, emb-lib Project Team
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining  a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
#    THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------------

import sys
import os
import re
import shutil

from utils import *

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView

from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent, QModelIndex, QItemSelectionModel

#-------------------------------------------------------------------------------
class ComponentsTable(QTableWidget):
    
    cells_chosen  = pyqtSignal([list])
    mouse_click   = pyqtSignal([str])
    file_load     = pyqtSignal()
    cmps_updated  = pyqtSignal([dict])
    cmps_selected = pyqtSignal([str])
    
    def __init__(self, parent):
        super().__init__(0, 2, parent)
        
        self.itemSelectionChanged.connect(self.cell_chosen)
        self.cellClicked.connect  (self.cell_chosen)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # select whole row
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)   # disable edit cells

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.horizontalHeader().resizeSection(1, 200)
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
    def cell_chosen(self):
        items = self.selectedItems()
        refs = []
     #   if len(items) > 0:
        for i in items:
            if i.column() == 0:
                refs.append( self.CmpDict[i.data(Qt.DisplayRole)] )
    
        self.cells_chosen.emit(refs)
        self.cmps_selected.emit(str(len(refs)) + ' components selected')
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
        self.cell_chosen()
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
        self.cell_chosen()
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

