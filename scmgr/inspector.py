# coding: utf-8


import sys
import os
import re
import shutil

from cmpmgr    import *

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
colEDIT = 0
colNAME = 0
colDATA = 1
MULTIVALUE = '<...>'
#-------------------------------------------------------------------------------
class TComboBox(QComboBox):

    def __init__(self, parent):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, e):
        key = e.key()
        mod = e.modifiers()
        if key == Qt.Key_Down or key == Qt.Key_Up:
            if not mod:
                QApplication.sendEvent( self.parent(), e ) 
                return
            elif mod == Qt.AltModifier:
                self.showPopup()

        QComboBox.keyPressEvent(self, e)


    def set_index(self, text):
        items = [self.itemText(i) for i in range(self.count()) ]
        self.setCurrentIndex( items.index(text) )

#-------------------------------------------------------------------------------    
class Inspector(QTreeWidget):
    
    #---------------------------------------------------------------------------    
    #
    #              Title                  Delegate         Delegate Data
    #
    ItemsTable = [ ['Ref',              'TextItemDelegate', None],
                   ['LibName',          'TextItemDelegate', None],
                   ['Value',            'TextItemDelegate', None],
                   ['Footprint',        'TextItemDelegate', None],
                   ['DocSheet',         'TextItemDelegate', None],
                   ['X',                'TextItemDelegate', None],
                   ['Y',                'TextItemDelegate', None],
                   ['Timestamp',        'TextItemDelegate', None] ]

    
    StdParamsNameMap =\
    {
        'Ref'       : 'Ref',
        'LibName'   : 'LibName',
        'Value'     : 'Fields[1].Text',
        'Footprint' : 'Fields[2].Text',
        'DocSheet'  : 'Fields[3].Text',
        'X'         : 'PosX',
        'Y'         : 'PosY',
        'Timestamp' : 'Timestamp'
    }
    
    
    #---------------------------------------------------------------------------    
    load_field  = pyqtSignal( [list], [str] )
    mouse_click = pyqtSignal([str])
    #---------------------------------------------------------------------------    
            
#-------------------------------------------------------------------------------    
    class InspectorItemsDelegate(QStyledItemDelegate):

        TEXT_DELEGATE = 0
        CBOX_DELEGATE = 1
        
        def __init__(self, parent):
            super().__init__(parent)
            self.editors = {}
        
        def clear_editor_data(self):
            self.editors = {}
            
        def add_editor_data(self, name, editor_type, editor_data = []):
            self.editors[name] = [editor_type, editor_data]
            
        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                name = idx.sibling(idx.row(), 0).data()
                etype = self.editors[name][0]
                if etype == self.TEXT_DELEGATE:
                    editor = QStyledItemDelegate.createEditor(self, parent, option, idx)
                    return editor
                else:
                    editor = TComboBox(parent)
                    editor.setEnabled(True)
                    editor.setEditable(True)
                    editor.addItems( self.editors[name][1] )
                    return editor
                

        def setEditorData(self, editor, idx):
            #print(editor.metaObject().className() )
            name = idx.sibling(idx.row(), 0).data()
            if self.editors[name][0] == self.TEXT_DELEGATE:
                QStyledItemDelegate.setEditorData(self, editor, idx)
            else:
                value = idx.model().data(idx, Qt.EditRole)
                editor.set_index(value)

        def setModelData(self, editor, model, idx):
            name = idx.sibling(idx.row(), 0).data()
            if self.editors[name][0] == self.TEXT_DELEGATE:
                QStyledItemDelegate.setModelData(self, editor, model, idx)
            else:
                value = editor.currentText()
                values = self.editors[name][1]
                if value not in values:
                    values.append(value)

                QStyledItemDelegate.setModelData(self, editor, model, idx)

    #---------------------------------------------------------------------------    
    def add_property(self):
        print('add property')
        text, ok = QInputDialog.getText(self, 'Add Property', 'Enter Property Name')
        
        for c in self.comps:
            if not c.field(text):
                f = ComponentField.default(c, text)
                c.add_field(f)
        
        self.load_user_defined_params()
            
    #---------------------------------------------------------------------------    
    def remove_property(self):
        print('delete property')
        
        item = self.currentItem()
        name  = item.data(colNAME, Qt.DisplayRole)
        reply = QMessageBox.question(self, 'Delete Property', 'Delete "' + name + '" property?' )
        
        if reply == QMessageBox.No:
            return

        for c in self.comps:
            f = c.field(name)
            c.remove_field(f)

        self.load_user_defined_params()

    #---------------------------------------------------------------------------    
    def rename_property(self):
        print('rename property')
        item = self.currentItem()
        name  = item.data(colNAME, Qt.DisplayRole)
        text, ok = QInputDialog.getText(self, 'Rename Property', 'Enter New Proterty Name')

        for c in self.comps:
            f = c.field(name)
            f.Name = text

        self.load_user_defined_params()

    #---------------------------------------------------------------------------    
    def mousePressEvent(self, e):
        self.mouse_click.emit('Inspector')
        QTreeWidget.mousePressEvent(self, e)
        
    #-------------------------------------------------------------------------------    
    def __init__(self, parent):
        super().__init__(parent)
        #self.setAlternatingRowColors(True)
        self.setIndentation(16)
        self.setColumnCount(2)
        self.header().resizeSection(2, 10)
        self.header().setSectionResizeMode(colNAME, QHeaderView.Interactive)
        self.setHeaderLabels( ('Property', 'Value') );
        self.std_items = self.addParent(self, 0, 'Standard', 'slon')
        self.usr_items = self.addParent(self, 0, 'User Defined', 'mamont')
    
        for idx, i in enumerate(self.ItemsTable):
            self.addChild(self.std_items, i[0], '')
            
        self.addChild(self.usr_items, '<empty>', '')
        
        self.ItemsDelegate = self.InspectorItemsDelegate(self)
        self.setItemDelegate(self.ItemsDelegate)
        
        self.itemClicked.connect(self.item_clicked)
        self.currentItemChanged.connect(self.item_changed)
        self.itemActivated.connect(self.item_activated)
        
    #---------------------------------------------------------------------------    
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setExpanded (True)
        item.setFlags(Qt.ItemIsEnabled)
        return item
        
    #---------------------------------------------------------------------------    
    def addChild(self, parent, title, data, flags=Qt.NoItemFlags):
        item = QTreeWidgetItem(parent, [title])
        item.setData(colDATA, Qt.DisplayRole, data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | flags)
        
        return item
        
    #---------------------------------------------------------------------------    
    def item_row(self, item):
        parent = item.parent()
        
        for i in range( self.topLevelItemCount() ):
            if parent == self.topLevelItem(i):
                row = self.indexFromItem(item, colDATA).row()
                for j in range(i):
                    row += self.topLevelItem(j).childCount()
                
                return row
                
    #---------------------------------------------------------------------------    
    def item_clicked(self, item, col):
        
        param = item.data(colNAME, Qt.DisplayRole)
        comps = self.comps
        if item.parent() == self.topLevelItem(0):
            self.load_field.emit([comps, param])
                
        if item.parent() == self.topLevelItem(1):
            self.load_field.emit([comps, param])
            
    #---------------------------------------------------------------------------    
    def item_activated(self, item, col):
        self.editItem(item, colDATA)
        #print('Inspector::item_activated')
            
    #---------------------------------------------------------------------------    
    def item_changed(self, item, prev):

        #print('Inspector::item_changed')
                
        idx    = self.indexFromItem(prev, colDATA)
        editor = self.indexWidget(idx)

        
        if editor:
            #print(editor)
            self.commitData(editor)
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)


        self.editItem(item, colDATA)
        self.item_clicked(item, colNAME)

    #---------------------------------------------------------------------------    
    def finish_edit(self):
        print('Inspector::finish_edit')
        idx    = self.indexFromItem(self.currentItem(), colDATA)
        editor = self.indexWidget(idx)

       # print(editor)

        if editor:
            #print( self.itemFromIndex(idx).data(colNAME, Qt.DisplayRole) )
            self.commitData(editor)
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
        
        self.save_cmps()
            
    #---------------------------------------------------------------------------    
    def prepare_std_params(self, item):
        name  = item.data(colNAME, Qt.DisplayRole)
        param = self.StdParamsNameMap[name]
        
        l = []
        for c in self.comps:
            l.append( eval('c.' + param) )

        vals = list(set(l))
        vals.sort()
        if len(vals) == 1:
            self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.TEXT_DELEGATE)
            item.setData(colDATA, Qt.DisplayRole, vals[0])

        else:
            vals.insert(0, MULTIVALUE)
            self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.CBOX_DELEGATE, vals)
            item.setData(colDATA, Qt.DisplayRole, vals[0])
        
        
    #---------------------------------------------------------------------------    
    def reduce_list(self, l):
        l = list(set(l))
        l.sort()
        return l
        
    #---------------------------------------------------------------------------    
    def user_defined_params(self):
        
        l = []
        fnames_set = set([ i.Name for i in self.comps[0].Fields[4:]])
        for c in self.comps[1:]:
            fnames_set &= set( [ i.Name for i in c.Fields[4:]] )
           
        fnames = list(fnames_set)
        
        fdict = {}
        for fn in fnames:
            fvalues =  []
            for c in self.comps:
                f = c.field(fn)
                if f:
                    fvalues.append(f.Text)
            fdict[fn] = self.reduce_list(fvalues)
        
                    
        for f in fdict.keys():
            if len(fdict[f]) > 1:
                fdict[f] = self.reduce_list(fdict[f])
                fdict[f].insert(0, MULTIVALUE)
        
        return fdict
        
    #---------------------------------------------------------------------------
    def load_user_defined_params(self):
        self.topLevelItem(1).takeChildren()
        user_fields = self.user_defined_params()        

        for name in user_fields.keys():
            item = self.addChild(self.usr_items, name, user_fields[name][0])

            if len(user_fields[name]) == 1:
                self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.TEXT_DELEGATE)
            else:
                vals = user_fields[name]
                self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.CBOX_DELEGATE, vals)
        
    #---------------------------------------------------------------------------
    def load_cmp(self, cmps):
        
        #-------------------------------------
        #
        #    Create selected components list including component parts
        #
        comps = []
        for c in cmps:
            if len(c) > 1:
                comps += c
            else:
                comps.append(c[0])
        
        self.comps = comps
        self.ItemsDelegate.clear_editor_data()
        comp = self.comps[0]
        
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)
            self.prepare_std_params(item)
            
        self.load_user_defined_params()            
            
    #---------------------------------------------------------------------------                            
    def save_cmps(self):
        for c in self.comps:
            for i in range( self.topLevelItem(0).childCount() ):
                item = self.topLevelItem(0).child(i)
                item_name  = item.data(colNAME, Qt.DisplayRole)
                item_value = item.data(colDATA, Qt.DisplayRole)
                if item_value != MULTIVALUE:
                    exec('c.' + self.StdParamsNameMap[item_name] + ' = item_value')
                
            for i in range( self.topLevelItem(1).childCount() ):
                item = self.topLevelItem(1).child(i)
                item_name  = item.data(colNAME, Qt.DisplayRole)
                item_value = item.data(colDATA, Qt.DisplayRole)
                if item_value != MULTIVALUE:
                    f = c.field(item_name)
                    f.Text = item_value
                    
#                   for i in FieldInspector.fgroup:
#                   f = c.field(item_name)
#                   if f:
#                       f.Text = item_value
#                   else:
                        
        
                                            
#-------------------------------------------------------------------------------    
class FieldInspector(QTreeWidget):
    
    mouse_click = pyqtSignal([str])
    
    #---------------------------------------------------------------------------    
    class TextItemDelegate(QStyledItemDelegate):


        def __init__(self, parent, values):
            super().__init__(parent)

        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                return QStyledItemDelegate.createEditor(self, parent, option, idx)
    
    #---------------------------------------------------------------------------    
    class CBoxItemDelegate(QStyledItemDelegate):

        def __init__(self, parent, values, editable=False):
            super().__init__(parent)
            self.values = values
            self.editable = editable

        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                editor = TComboBox(parent)
                editor.setEnabled(True)
                editor.setEditable(self.editable)
                editor.addItems( self.values )
                #editor.setFocusPolicy(Qt.ClickFocus)
                return editor

        def setEditorData(self, editor, idx):
            #print(editor.metaObject().className() )
            value = idx.model().data(idx, Qt.EditRole)
            editor.set_index(value)
            
        def setModelData(self, editor, model, idx):
            value = editor.currentText()
            if value not in self.values:
                self.values.append(value)

            QStyledItemDelegate.setModelData(self, editor, model, idx)
                
            
    class FieldInspectorItemsDelegate(QStyledItemDelegate):

        TEXT_DELEGATE = 0
        CBOX_DELEGATE = 1

        def __init__(self, parent):
            super().__init__(parent)
            self.editors = {}

        def clear_editor_data(self):
            self.editors = {}

        def add_editor_data(self, name, editor_type, editor_data = []):
            self.editors[name] = [editor_type, editor_data]

        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                name = idx.sibling(idx.row(), 0).data()
                etype = self.editors[name][0]
                if etype == self.TEXT_DELEGATE:
                    editor = QStyledItemDelegate.createEditor(self, parent, option, idx)
                    return editor
                else:
                    editor = TComboBox(parent)
                    editor.setEnabled(True)
                    editor.setEditable(True)
                    editor.addItems( self.editors[name][1] )
                    return editor


        def setEditorData(self, editor, idx):
            #print(editor.metaObject().className() )
            name = idx.sibling(idx.row(), 0).data()
            if self.editors[name][0] == self.TEXT_DELEGATE:
                QStyledItemDelegate.setEditorData(self, editor, idx)
            else:
                value = idx.model().data(idx, Qt.EditRole)
                editor.set_index(value)

        def setModelData(self, editor, model, idx):
            name = idx.sibling(idx.row(), 0).data()
            if self.editors[name][0] == self.TEXT_DELEGATE:
                QStyledItemDelegate.setModelData(self, editor, model, idx)
            else:
                value = editor.currentText()
                values = self.editors[name][1]
                if value not in values:
                    values.append(value)

                QStyledItemDelegate.setModelData(self, editor, model, idx)
            
            
    #---------------------------------------------------------------------------    
    #
    #              Title              Field Name         Delegate         Delegate Data
    #
    ItemsTable = [ ['X',                'PosX',        'TextItemDelegate', None],
                   ['Y',                'PosY',        'TextItemDelegate', None],
                   ['Orientation',      'Orientation', 'CBoxItemDelegate', ['Horizontal', 'Vertical']],
                   ['Visible',          'Visible',     'CBoxItemDelegate', ['Yes',  'No']],
                   ['Horizontal Align', 'HJustify',    'CBoxItemDelegate', ['Left', 'Center', 'Right']],
                   ['Vertical Align',   'VJustify',    'CBoxItemDelegate', ['Top',  'Center', 'Bottom']],
                   ['Font Size',        'FontSize',    'TextItemDelegate', None],
                   ['Font Bold',        'FontBold',    'CBoxItemDelegate', ['Yes', 'No']],
                   ['Font Italic',      'FontItalic',  'CBoxItemDelegate', ['Yes', 'No']] ]
    
    ItemsParamNameMap =\
    {
        'X'                : [ 'PosX'                                      ],
        'Y'                : [ 'PosY'                                      ], 
        'Orientation'      : [ 'Orientation', ['Horizontal', 'Vertical']   ],
        'Visible'          : [ 'Visible',     ['Yes',  'No']               ],
        'Horizontal Align' : [ 'HJustify',    ['Left', 'Center', 'Right']  ],
        'Vertical Align'   : [ 'VJustify',    ['Top',  'Center', 'Bottom'] ],
        'Font Size'        : [ 'FontSize'                                  ],
        'Font Bold'        : [ 'FontBold',    ['Yes',  'No']               ],
        'Font Italic'      : [ 'FontItalic',  ['Yes',  'No']               ]
    }
    
    #---------------------------------------------------------------------------    
    class TreeWidgetItem(QTreeWidgetItem):
        
        def __init__(self, parent, title):
            super().__init__(parent, title)
            
        def focusOutEvent(self, event):
            print('TreeItem::focusOutEvetnevent ' + str(event))
            
    #---------------------------------------------------------------------------    
    class EventFilter(QObject):
        def __init__(self, parent):
            super().__init__(parent)

        def eventFilter(self, obj, e):
            if e.type() == QEvent.KeyPress:
                
                if e.key() == Qt.Key_Down or e.key() == Qt.Key_Up:
                    action = QAbstractItemView.MoveDown if e.key() == Qt.Key_Down else QAbstractItemView.MoveUp
                    idx = obj.moveCursor(action, Qt.NoModifier)
                    item = obj.itemFromIndex(idx)
                    obj.setCurrentItem(item)
                    return True

                            
            if e.type() == QEvent.Leave:
                print('======== mouse leave')
               # self.parent().finish_edit()
                return False
                
            return False
            
    #-------------------------------------------------------------------------------    
    def mousePressEvent(self, e):
        self.mouse_click.emit('FieldInspector')
        QTreeWidget.mousePressEvent(self, e)
        
    #-------------------------------------------------------------------------------    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.installEventFilter(self.EventFilter(self))
        
        self.setIndentation(16)
        self.setColumnCount(2)
        self.header().resizeSection(2, 10)
        self.header().setSectionResizeMode(colNAME, QHeaderView.Interactive)
        self.setHeaderLabels( ('Field Name', 'Value' ) );
        self.setHeaderHidden(True)
        
        self.setFocusPolicy(Qt.WheelFocus)
        #self.setTabKeyNavigation(False)
        
        self.field_items = self.addParent(self, 0, 'Field', '')
    
        for idx, i in enumerate(self.ItemsTable):
            self.addChild(self.field_items, i[0], '')
            #self.setItemDelegateForRow( idx, eval('self.' + i[2])(self, i[3]) )
            
        self.ItemsDelegate = self.FieldInspectorItemsDelegate(self)
        self.setItemDelegate(self.ItemsDelegate)
                
        self.itemClicked.connect(self.item_clicked)
        self.itemPressed.connect(self.item_pressed)
        self.currentItemChanged.connect(self.item_changed)
        self.itemActivated.connect(self.item_activated)
    
        self.field = None
        
        #self.setItemDelegate(self.ItemDelegate(self))
    
    #---------------------------------------------------------------------------    
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setExpanded (True)
        item.setFlags(Qt.ItemIsEnabled)
        return item
    
    #---------------------------------------------------------------------------    
    def addChild(self, parent, title, data, flags=Qt.NoItemFlags):
        item = self.TreeWidgetItem(parent, [title])
        item.setData(colDATA, Qt.DisplayRole, data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | flags)
        return item
    
    #---------------------------------------------------------------------------    
#   def keyPressEvent(self, e):
#       if e.key() == Qt.Key_Down or e.key() == Qt.Key_Up:
#           action = QAbstractItemView.MoveDown if e.key() == Qt.Key_Down else QAbstractItemView.MoveUp
#           print('Down') if e.key() == Qt.Key_Down else print('Up')
#           idx = self.moveCursor(action, Qt.NoModifier)
#           item = self.itemFromIndex(idx)
#           self.setCurrentItem(item)
#       else:
#           QTreeWidget.keyPressEvent(self, e)
        
    #---------------------------------------------------------------------------    
    def item_clicked(self, item, col):
        self.select_item(item)            
        
    #---------------------------------------------------------------------------    
    def item_pressed(self, item, col):
        self.select_item(item)
        
    #---------------------------------------------------------------------------    
    def item_changed(self, item, prev):
        
        if not item.data(colDATA, Qt.DisplayRole):
            return 
                
        idx    = self.indexFromItem(prev, colDATA)
        editor = self.indexWidget(idx)
            
        if editor:
            self.commitData(editor)
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            
                        
        self.editItem(item, colDATA)
        self.handle_item(item)    
        self.item_clicked(item, colNAME)
    
    #---------------------------------------------------------------------------    
    def item_activated(self, item, col):
        if not item.data(colDATA, Qt.DisplayRole):
            return 

        self.editItem(item, colDATA)
    
    #---------------------------------------------------------------------------    
    def select_item(self, item):
        pass
        #self.setCurrentItem(item, colNAME)
        #self.selectionModel().setCurrentIndex(self.currentIndex(), QItemSelectionModel.ClearAndSelect)
        
    #---------------------------------------------------------------------------    
    def load_field_slot(self, d):
        self.comps = d[0]
        self.param = d[1]
        
        self.load_field()
        
    #---------------------------------------------------------------------------    
    def handle_item(self, item):
        if not self.field:
            return 
            
        if item.data(colNAME, Qt.DisplayRole) == 'X':
            self.field.PosX = item.data(colDATA, Qt.DisplayRole)

        if item.data(colNAME, Qt.DisplayRole) == 'Y':
            self.field.PosY = item.data(colDATA, Qt.DisplayRole)

    #---------------------------------------------------------------------------    
    def finish_edit(self):
        print('FieldInspector::finish_edit')
        idx    = self.indexFromItem(self.currentItem(), colDATA)
        editor = self.indexWidget(idx)

        #print(editor)

        if editor:
            #print( self.itemFromIndex(idx).data(colNAME, Qt.DisplayRole) )
            self.commitData(editor)
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)

        self.save_fields()
            
    #---------------------------------------------------------------------------    
    def reduce_list(self, l):
        l = list(set(l))
        l.sort()
        return l
    
    #---------------------------------------------------------------------------    
    def prepare_item(self, item, flist):
        item_name   = item.data(colNAME, Qt.DisplayRole)
        fparam_name = self.ItemsParamNameMap[item_name][0]
        
        vals = []
        for f in flist:
            vals.append( eval('f.' + fparam_name) )
                
        vals = self.reduce_list(vals)
        #print(vals)
                     
        if len( self.ItemsParamNameMap[item_name] ) == 1:
            if len(vals) == 1:
                self.ItemsDelegate.add_editor_data(item_name, self.FieldInspectorItemsDelegate.TEXT_DELEGATE)
            else:
                vals.insert(0, MULTIVALUE)
                self.ItemsDelegate.add_editor_data(item_name, self.FieldInspectorItemsDelegate.CBOX_DELEGATE, vals)
                
            data_val = vals[0]
        else:
#           print('*'*20)
#           print(item_name)
#           print(fparam_name)
            data_val = vals[0]
            if len(vals) > 1:
                vals = [MULTIVALUE] + self.ItemsParamNameMap[item_name][1] 
                data_val = vals[0]
            else:
                vals = self.ItemsParamNameMap[item_name][1] 

            self.ItemsDelegate.add_editor_data(item_name, self.FieldInspectorItemsDelegate.CBOX_DELEGATE, vals)
            
            
        #print(item_name + ' : ' + data_val)
        #print(vals)
        item.setData(colDATA, Qt.DisplayRole, data_val)
            
    #---------------------------------------------------------------------------    
    def load_field(self):
        
        NO_FIELD_PARAMS = ['LibName', 'X', 'Y', 'Timestamp']

        comps = self.comps
        param = self.param
        
        if param in NO_FIELD_PARAMS:
            for i in range( self.topLevelItem(0).childCount() ):
                item = self.topLevelItem(0).child(i)
                item.setData(colDATA, Qt.DisplayRole, '')
                if hasattr(self, 'field_list'):
                    delattr(self, 'field_list')
            return
        
        #print(param)
        
        flist = []
        for c in comps:
            flist.append( c.field(param) )
            #print(c.field(param))
                        
                        
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)
            self.prepare_item(item, flist)
        
        self.field_list = flist
                
#           if len(self.fgroup) > 0:
#           else:
#               item.setData( colDATA, Qt.DisplayRole, '' )
                    
    #---------------------------------------------------------------------------    
    def save_fields(self):
        
        if not hasattr(self, 'field_list'):
            return
        
        for i in range( self.topLevelItem(0).childCount() ):
            item        = self.topLevelItem(0).child(i)
            item_name   = item.data(colNAME, Qt.DisplayRole)
            fparam_name = self.ItemsParamNameMap[item_name][0]
            val         = item.data(colDATA, Qt.DisplayRole)
            if val != MULTIVALUE:
                for f in self.field_list:
                    exec('f.' + fparam_name + ' = val')
            
        
    #---------------------------------------------------------------------------    
    def column_resize(self, idx, osize, nsize):
        self.setColumnWidth(idx, nsize)
                                    
#-------------------------------------------------------------------------------    

