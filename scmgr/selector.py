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
    
        def __init__(self, parent):
            super().__init__(parent)
            self.Parent = parent

        def add_editor_data(self, props_dict):
            self.PropsDict = props_dict
            
        def createEditor(self, parent, option, idx):
            if idx.column() == 0:
                editor = TComboBox(parent)
                editor.setEnabled(True)
                editor.setEditable(True)
                names = list(self.PropsDict.keys())
                names.sort()
                editor.addItems(names)
                return editor
            elif idx.column() == 1:
                print('col: ', idx.column())
                editor = TComboBox(parent)
                name = idx.sibling(idx.row(), 0).data()
                if not name or not name in self.PropsDict.keys():
                    editor.setEnabled(False)
                    editor.setEditable(False)
                else:
                    editor.setEnabled(True)
                    editor.setEditable(True)
                    print(name, self.PropsDict[name])
                    editor.addItems( self.PropsDict[name] )
                    
                return editor
            else:
                print('col: ', idx.column())
                editor = TComboBox(parent)
                editor.setEnabled(True)
                editor.setEditable(False)
                editor.addItems( self.Parent.sel_options )
                return editor
    
    
#       def setEditorData(self, editor, idx):
#           #print(editor.metaObject().className() )
#           name = idx.sibling(idx.row(), 0).data()
#           if self.editors[name][0] == self.TEXT_DELEGATE:
#               QStyledItemDelegate.setEditorData(self, editor, idx)
#           else:
#               value = idx.model().data(idx, Qt.EditRole)
#               editor.set_index(value)
#
#       def setModelData(self, editor, model, idx):
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

    FieldItemsTable = [ ['X',                'X'           ],
                        ['Y',                'Y'           ],
                        ['Orientation',      'Orientation' ],
                        ['Visible',          'Visible'     ],
                        ['Horizontal Align', 'HJustify'    ],
                        ['Vertical Align',   'VJustify'    ],
                        ['Font Size',        'FontSize'    ],
                        ['Font Bold',        'FontBold'    ],
                        ['Font Italic',      'FontItalic'  ] ]
    
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
    #---------------------------------------------------------------------------    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            print('enter')
            item = self.currentItem()
            col  = self.currentColumn()
            print(item, col)
            self.editItem(item, col)
        else:
            QTreeWidget.keyPressEvent(self, e)
        
    #---------------------------------------------------------------------------    
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setExpanded(False)
#        item.setFlags(Qt.ItemIsEnabled)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        return item

    #---------------------------------------------------------------------------    
    def addChild(self, parent, title, data, flags=Qt.NoItemFlags):
        item = QTreeWidgetItem(parent, [title])
        item.setData(colDATA, Qt.DisplayRole, data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | flags)

        return item
    #---------------------------------------------------------------------------    
    def process_comps_slot(self, comps):
        props = {}
        for c in comps:
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
        
        self.addParent(self, 0, '<enter name>', '')
    #---------------------------------------------------------------------------    
    def change_mode_slot(self, state):
        print('state: ', state)
        
    #---------------------------------------------------------------------------    
    def comp_template_slot(self, comps):
        self.comp = comps[0][0]
        print('component template: ', self.comp.Ref)

        
    #---------------------------------------------------------------------------    
    def item_changed(self, item, col):
        print('Selector::item_changed', col)

        if col == self.colNAME:
            item.setData(self.colVALUE, Qt.EditRole, '')
            item.setData(self.colSELOPT, Qt.EditRole, self.sel_options[0])
        
        for i in range( self.topLevelItemCount() ):
            item = self.topLevelItem(i)
            if item.data(self.colNAME, Qt.DisplayRole) == self.NAME_PLACE_HOLDER:
                return
        
        self.addParent(self, self.colNAME, self.NAME_PLACE_HOLDER, '')
    #---------------------------------------------------------------------------    
    
#-------------------------------------------------------------------------------    
    
