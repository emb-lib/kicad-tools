# coding: utf-8


import sys
import os
import re
import shutil

from utils import *
from inspector import TComboBox

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction, QComboBox,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, QSplitter, QStyledItemDelegate,
                             QAbstractItemDelegate, 
                             QTableWidget, QTableWidgetItem, QCommonStyle, QTreeWidget, QTreeWidgetItem,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication,
                             QFileDialog, QInputDialog, QMessageBox)

from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent, QModelIndex, QItemSelectionModel



#-------------------------------------------------------------------------------    
class Selector(QTreeWidget):

    colNAME   = 0
    colVALUE  = 1
    colSELOPT = 2
    
    NAME_PLACE_HOLDER = '<enter name>'
    
    sel_options = ['', '+', '-', 're']
    
    #---------------------------------------------------------------------------
    def __init__(self, parent):
        super().__init__(parent)

        self.setIndentation(16)
        self.setColumnCount(2)
        self.header().resizeSection(2, 10)
        #self.header().setSectionResizeMode(colNAME, QHeaderView.Interactive)
        self.setHeaderLabels( ('Property', 'Value' ) );
        
        self.model().setHeaderData(0, Qt.Horizontal, QColor('red'), Qt.BackgroundColorRole)
    
    #---------------------------------------------------------------------------
    class SelectorItemsDelegate(QStyledItemDelegate):
    
        TEXT_DELEGATE = 0
        CBOX_DELEGATE = 1
        
        edit_finished = pyqtSignal([list])
    
        def __init__(self, parent):
            super().__init__(parent)
            self.Parent = parent

        def add_editor_data(self, props_dict):
            self.PropsDict = props_dict
            
        def createEditor(self, parent, option, idx):
            #---------------------------------------------------------
            #
            #    Child item
            #
            if idx.parent().isValid():    
                if idx.column() == self.Parent.colVALUE:
                    name = idx.sibling(idx.row(), 0).data()
                    for i in self.Parent.FieldItemsTable:
                        if i[0] == name:
                            if i[2]:
                                editor = TComboBox(parent)
                                editor.setEnabled(True)
                                editor.addItems( i[2] )
                            else:
                                editor = QStyledItemDelegate.createEditor(self, parent, option, idx)
                    
                            return editor
                elif idx.column() == self.Parent.colSELOPT:
                    editor = TComboBox(parent)
                    editor.setEnabled(True)
                    editor.setEditable(False)
                    editor.addItems( self.Parent.sel_options )
                    return editor
                    
                return             
            #---------------------------------------------------------
            #
            #    Top-level item
            #
            if idx.column() == 0:
                editor = TComboBox(parent)
                editor.setEnabled(True)
                editor.setEditable(True)
                names = list(self.PropsDict.keys())
                names.sort()
                editor.addItems(names)
                return editor
            elif idx.column() == 1:
                editor = TComboBox(parent)
                name = idx.sibling(idx.row(), 0).data()
                if not name or not name in self.PropsDict.keys():
                    editor.setEnabled(False)
                    editor.setEditable(False)
                else:
                    editor.setEnabled(True)
                    editor.setEditable(True)
                    editor.addItems( self.PropsDict[name] )
                    
                return editor
            else:
                editor = TComboBox(parent)
                editor.setEnabled(True)
                editor.setEditable(False)
                editor.addItems( self.Parent.sel_options )
                return editor
    
    
#       def setEditorData(self, editor, idx):
#           print('setEditorData: ', editor.currentText())
#           QStyledItemDelegate.setEditorData(self, editor, idx)
            
#           #print(editor.metaObject().className() )
#           name = idx.sibling(idx.row(), 0).data()
#           if self.editors[name][0] == self.TEXT_DELEGATE:
#               QStyledItemDelegate.setEditorData(self, editor, idx)
#           else:
#               value = idx.model().data(idx, Qt.EditRole)
#               editor.set_index(value)
#
        def setModelData(self, editor, model, idx):
            
            value    = editor.currentText() if editor.metaObject().className() == 'TComboBox' else editor.text()
            prev_val = idx.sibling(idx.row(), 0).data()
            self.edit_finished.emit( [idx, prev_val, value ] )
            QStyledItemDelegate.setModelData(self, editor, model, idx)

            
#           name = idx.sibling(idx.row(), 0).data()
#           if self.editors[name][0] == self.TEXT_DELEGATE:
#               QStyledItemDelegate.setModelData(self, editor, model, idx)
#           else:
#               value = editor.currentText()
#               values = self.editors[name][1]
#               if value not in values:
#                   values.append(value)
#
#               QStyledItemDelegate.setModelData(self, editor, model, idx)
    
    #---------------------------------------------------------------------------    
    #
    #              Title                  Delegate         Delegate Data
    #
    StdItemsTable = [ 'Ref',
                      'LibRef',
                      'Value',
                      'Footprint',
                      'DocSheet',
                      'X',
                      'Y',
                      'Timestamp' ]

    NonFieldProps = [ 'LibRef',
                      'X',
                      'Y',
                      'Timestamp' ]

    StdParamsNameMap =\
    {
        'Ref'       : 'Ref',
        'LibRef'    : 'LibRef',
        'Value'     : 'Fields[1].Text',
        'Footprint' : 'Fields[2].Text',
        'DocSheet'  : 'Fields[3].Text',
        'X'         : 'X',
        'Y'         : 'Y',
        'Timestamp' : 'Timestamp'
    }

    FieldItemsTable = [ ['X',                'X',           None,                         '0'          ],
                        ['Y',                'Y',           None,                         '0'          ],
                        ['Orientation',      'Orientation', ['Horizontal', 'Vertical'],   'Horizontal' ],
                        ['Visible',          'Visible',     ['Yes',  'No'],               'No'         ],
                        ['Horizontal Align', 'HJustify',    ['Left', 'Center', 'Right'],  'Left'       ],
                        ['Vertical Align',   'VJustify',    ['Top',  'Center', 'Bottom'], 'Center'     ],
                        ['Font Size',        'FontSize',    None,                         '100'        ],
                        ['Font Bold',        'FontBold',    ['Yes', 'No'],                'No'         ],
                        ['Font Italic',      'FontItalic',  ['Yes', 'No'],                'No'         ] ]
    
    #---------------------------------------------------------------------------    
    def __init__(self, parent):
        super().__init__(parent)

        self.setIndentation(16)
        self.setColumnCount(3)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.header().resizeSection(1, 200)
        self.header().setSectionResizeMode(self.colNAME, QHeaderView.Interactive)
        self.setHeaderLabels( ('Property', 'Value', 'Sel') );
        self.ItemsDelegate = self.SelectorItemsDelegate(self)
        self.setItemDelegate(self.ItemsDelegate)
    
        self.itemChanged.connect(self.item_changed)
        self.currentItemChanged.connect(self.current_item_changed)
        self.ItemsDelegate.edit_finished.connect(self.edit_finished_slot)
        
        self.state = Qt.Unchecked
    #---------------------------------------------------------------------------    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            item = self.currentItem()
            col  = self.currentColumn()
            self.editItem(item, col)
        else:
            QTreeWidget.keyPressEvent(self, e)
        
    #---------------------------------------------------------------------------    
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setExpanded(False)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        #item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicatorWhenChildless)
        return item
    #---------------------------------------------------------------------------    
    def addChild(self, parent, title, data, flags=Qt.NoItemFlags):
        item = QTreeWidgetItem(parent, [title])
        item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | flags)
        item.setData(self.colVALUE, Qt.DisplayRole, data)

        return item
    #---------------------------------------------------------------------------    
    def process_comps_slot(self, comps):
        self.comps = comps
        props = {}
        for c in comps:
            for name in self.NonFieldProps:
                value = getattr(c[0], name)
                if name in props.keys():
                    props[name].append(value)
                else:
                    props[name] = [value]

            for f in c[0].Fields:
                if f.Name in props.keys():
                    props[f.Name].append(f.Text)
                else:
                    props[f.Name] = [f.Text]
        
        for p in props.keys():
            props[p] = list(set(props[p]))
            props[p].sort()
                   
        self.props = props 
        self.ItemsDelegate.add_editor_data(self.props)
        
        #self.add_default_item()
    #---------------------------------------------------------------------------    
    def add_item(self, name):
        if name in self.NonFieldProps:
            value = getattr(self.comp, name)
        else:
            f     = self.comp.field(name)
            value = f.Text

        item = self.addParent(self, self.colNAME, name, '')
        item.setData(self.colVALUE, Qt.DisplayRole, value)

        if name in self.NonFieldProps:
            return 
            
        for fprop in self.FieldItemsTable:
            name  = fprop[0]
            value = getattr( f, fprop[1])
            self.addChild(item, name, value)

    #---------------------------------------------------------------------------    
    def add_default_item(self):
        self.addParent(self, self.colNAME, self.NAME_PLACE_HOLDER, '')
    #---------------------------------------------------------------------------    
    def update_items(self):
        self.clear()
        if self.state == Qt.Checked:
            for prop in self.StdItemsTable:
                self.add_item(prop)
                
            for f in self.comp.Fields[4:]:
                self.add_item(f.Name)

        self.add_default_item()
    #---------------------------------------------------------------------------    
    def change_mode_slot(self, state):
        self.state = state
        self.update_items()
            
    #---------------------------------------------------------------------------    
    def comp_template_slot(self, comps):
        self.comp = comps[0][0]
        self.update_items()
    #---------------------------------------------------------------------------    
    def item_changed(self, item, col):
        #print('Selector::item_changed', col)

        if col == self.colNAME:
            item.setData(self.colVALUE, Qt.EditRole, '')
            item.setData(self.colSELOPT, Qt.EditRole, self.sel_options[0])
    #---------------------------------------------------------------------------    
    def current_item_changed(self, curr, prev):
        print('selector::current_item_changed')

    #---------------------------------------------------------------------------    
    def edit_finished_slot(self, data):
        print('edit_finished_slot')

        idx      = data[0]
        prev_val = data[1]
        value    = data[2]
        
        if prev_val == self.NAME_PLACE_HOLDER and value != self.NAME_PLACE_HOLDER:
            self.add_default_item()
            
            if value not in self.NonFieldProps:
                item = self.currentItem()
                for fprop in self.FieldItemsTable:
                    name  = fprop[0]
                    value = fprop[3]
                    self.addChild(item, name, value)
                 
#       if prev_val != value:
#           print('>>>>>',prev_val, value)
#           self.select_comps()
                       
    #---------------------------------------------------------------------------    
    def apply_slot(self):
        self.select_comps()
    #---------------------------------------------------------------------------    
    def select_comps(self):
        print('select_comps')
        
        sel_refs = []
        
        for c in self.comps:
            for i in range( self.topLevelItemCount() ):
                item = self.topLevelItem(i)
                name  = item.data(self.colNAME, Qt.DisplayRole)
                if name == self.NAME_PLACE_HOLDER:
                    continue
                    
                sel_opt = item.data(self.colSELOPT, Qt.DisplayRole)
                if sel_opt:
                    value = item.data(self.colVALUE, Qt.DisplayRole)
                    print(c[0].Ref, name, value, sel_opt)
                    
    #---------------------------------------------------------------------------    
    
#-------------------------------------------------------------------------------    
    
