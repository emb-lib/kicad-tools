#!/usr/bin/python3
# coding: utf-8


import sys
import os
import re
#import yaml
from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction, QComboBox,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, QSplitter, QStyledItemDelegate,
                             QAbstractItemDelegate, 
                             QTableWidget, QTableWidgetItem, QCommonStyle, QTreeWidget, QTreeWidgetItem,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication)

from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent, QModelIndex, QItemSelectionModel
from PyQt5.QtCore import QT_VERSION_STR

print('Qt Version: ' + QT_VERSION_STR)

#-------------------------------------------------------------------------------
colEDIT = 0
colNAME = 0
colDATA = 1
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
                   ['Lib Name',         'TextItemDelegate', None],
                   ['Value',            'TextItemDelegate', None],
                   ['Footprint',        'TextItemDelegate', None],
                   ['Doc Sheet',        'TextItemDelegate', None],
                   ['X',                'TextItemDelegate', None],
                   ['Y',                'TextItemDelegate', None],
                   ['Timestamp',        'TextItemDelegate', None] ]

    
    StdParamsNameMap =\
    {
        'Ref'       : 'Ref',
        'Lib Name'  : 'LibName',
        'Value'     : 'Fields[1].Text',
        'Footprint' : 'Fields[2].Text',
        'Doc Sheet' : 'Fields[3].Text',
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
            print(editor)
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
            vals.insert(0, '<...>')
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
        for c in self.comps:
            l += c.Fields[4:]
           
        fnames  = [ i.Name for i in l]
        fvalues = [ i.Text for i in l]
        
        field_names = self.reduce_list(fnames)
        
        fdict = {}
        for fn in field_names:
            indices = [i for i, x in enumerate(fnames) if x == fn]
            fdict[fn] = self.reduce_list( [fvalues[i] for i in indices] )
            

        for c in self.comps:
            for f in fdict.keys():
                if not c.field(f):
                    fdict[f].append('~')
                    
        for f in fdict.keys():
            if len(fdict[f]) > 1:
                fdict[f] = self.reduce_list(fdict[f])
                fdict[f].insert(0, '<...>')
        
        return fdict
        
    #---------------------------------------------------------------------------    
    def load_cmp(self, cmps):
        
        #-------------------------------------
        #
        #    Create selected components list including parts
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
            
                        
        self.topLevelItem(1).takeChildren()
        user_fields = self.user_defined_params()        
        row_offset  = self.topLevelItem(0).childCount()
        
        for name in user_fields.keys():
            item = self.addChild(self.usr_items, name, user_fields[name][0])
            
            if len(user_fields[name]) == 1:
                self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.TEXT_DELEGATE)
            else:
                vals = user_fields[name]
                self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.CBOX_DELEGATE, vals)
            
                            
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
                
    #---------------------------------------------------------------------------    
    #
    #              Title              Field Name         Delegate         Delegate Data
    #
    ItemsTable = [ ['X',                'PosX',        'TextItemDelegate', None],
                   ['Y',                'PosY',        'TextItemDelegate', None],
                   ['Orientation',      'Orientation', 'CBoxItemDelegate', ['Horizontal', 'Vertical']],
                   ['Visible',          'Visible',     'CBoxItemDelegate', ['Yes', 'No']],
                   ['Horizontal Align', 'HJustify',    'CBoxItemDelegate', ['Left', 'Center', 'Right']],
                   ['Vertical Align',   'VJustify',    'CBoxItemDelegate', ['Top', 'Center', 'Bottom']],
                   ['Font Size',        'FontSize',    'TextItemDelegate', None],
                   ['Font Bold',        'FontBold',    'CBoxItemDelegate', ['Yes', 'No']],
                   ['Font Italic',      'FontItalic',  'CBoxItemDelegate', ['Yes', 'No']] ]
    
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
                #print('======== mouse leave')
                self.parent().finish_edit()
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
            self.setItemDelegateForRow( idx, eval('self.' + i[2])(self, i[3]) )
    
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

    #---------------------------------------------------------------------------    
    def prepare_item(self, item, pindex):
        l = []
        for fg in self.fgroup:
            if len(fg) == 2:
                fstr = 'fg[0].Fields[fg[1]].'  
            else:
                fstr = 'fg[2].'
                
                
            #print(fstr + ' ' + str(pindex))
            p = eval( fstr + self.ItemsTable[pindex][1] ) # p means 'parameter'
                
            l.append( p )

        vals = list(set(l))
        vals.sort()
        row  = self.indexFromItem(item, colDATA).row()
        if len(vals) == 1:
            s = 'self.' + self.ItemsTable[pindex][2]
            self.setItemDelegateForRow( row, eval( s )(self, self.ItemsTable[pindex][3]) ) 
        else:
            vals.insert(0, '<...>')
            
            if self.ItemsTable[pindex][2] == 'TextItemDelegate':
                self.setItemDelegateForRow( row, self.CBoxItemDelegate(self, vals, True) )   # True - editable combobox
            else:
                self.setItemDelegateForRow( row, eval('self.' + self.ItemsTable[pindex][2])(self, ['<...>'] + self.ItemsTable[pindex][3]) )  
                
        item.setData(colDATA, Qt.DisplayRole, vals[0])
            
    #---------------------------------------------------------------------------    
    def load_field(self):
        
        comps = self.comps
        param = self.param
        
        #comp = comps[0]
        #print(comps)
        #print(param)
        
        self.fgroup = []       # list of items 'Component:Fn[:Field]', 
                               # where Fn - field number of parameter, Field - optional part
        
        no_field_params = ['Lib Name', 'X', 'Y', 'Timestamp']
        std_params      = ['Ref', 'Value', 'Footprint', 'Doc Sheet']
        
        if param not in no_field_params:
            for c in comps:
                Fn = None
                if param in std_params:

                    Fn = std_params.index(param)
                    #print('Index Fn: ' + str(Fn))
                else:
                    for idx, field in enumerate(c.Fields[4:], start=4):
                        if field.Name == param:
                            Fn = idx
                            break
                if Fn != None:
                    self.fgroup.append([c, Fn])
                else:
                    Fn = len(c.Fields)
                    field = ComponentField.default(c, param, Fn)
                    self.fgroup.append([c, Fn, field])
             
        #print(self.fgroup)
                                       
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)
            if len(self.fgroup) > 0:
                self.prepare_item(item, i)
            else:
                item.setData( colDATA, Qt.DisplayRole, '' )
                    
#       if f:
#           cur_item = self.topLevelItem(0).child(0)
#           self.setCurrentItem(cur_item)
        #self.clearSelection()
    
    #---------------------------------------------------------------------------    
    def column_resize(self, idx, osize, nsize):
        self.setColumnWidth(idx, nsize)
                                    
#-------------------------------------------------------------------------------    
class Selector(QTreeWidget):
    
    #-------------------------------------------------------------------------------    
    def __init__(self, parent):
        super().__init__(parent)

        self.setIndentation(16)
        self.setColumnCount(2)
        self.header().resizeSection(2, 10)
        self.header().setSectionResizeMode(colNAME, QHeaderView.Interactive)
        self.setHeaderLabels( ('Parameter', 'Value' ) );
        
        self.model().setHeaderData(0, Qt.Horizontal, QColor('red'), Qt.BackgroundColorRole)
    

#-------------------------------------------------------------------------------
class ComponentsTable(QTableWidget):
    
    cells_chosen = pyqtSignal([list])
    mouse_click  = pyqtSignal([str])
    
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
        self.setHorizontalHeaderLabels( ('Ref', 'Name') )

        b   = read_file('det-1/det-1.sch')
        rcl = raw_cmp_list(b)
        ipl = ['LBL'] 
        self.CmpDict = cmp_dict(rcl, ipl)
        self.update_cmp_list(self.CmpDict)
        
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
        refs = []
        for i in items:
            if i.column() == 0:
                refs.append( self.CmpDict[i.data(Qt.DisplayRole)] )
        
        self.cells_chosen.emit(refs)
        
    #---------------------------------------------------------------------------    
    def update_cmp_list(self, cd):

        keys = list( cd.keys() )
        keys.sort( key=split_alphanumeric )    

        self.setRowCount(len(cd))

        for idx, k in enumerate( keys ):
            Name = QTableWidgetItem(cd[k][0].LibName)
            Ref  = QTableWidgetItem(k)
          #  print(ref + ' ' + cd[ref].Name)
            self.setItem(idx, 0, Ref)
            self.setItem(idx, 1, Name)
                                        
#-------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    
#    class EventFilter(QObject):
#        def __init__(self, parent):
#            super().__init__(parent)
#
#        def eventFilter(self, obj, e):
#            #print(obj.metaObject().className())
#
#            if e.type() == QEvent.KeyPress or e.type() == QEvent.ShortcutOverride:
#                key = e.key()
#                mod = e.modifiers()
#
#                print(str(e) + ' ' + str(e.type()) )
#
#                if mod == Qt.AltModifier:
#                    print('*'*30)
#                    print('alt pressed')
#                    if key == Qt.Key_Left or key == Qt.Key_Right:
#                        print('alt-left') if key == Qt.Key_Left else print('alt-right')
##                       action = QAbstractItemView.MoveLeft if key == Qt.Key_Left else QAbstractItemView.MoveRight
##                       idx = obj.moveCursor(action, Qt.NoModifier)
##                       item = obj.itemFromIndex(idx)
##                       obj.setCurrentItem(item)
#                        return True
#
#            return False

    #-------------------------------------------------------------------------------    

    class EventFilter(QObject):
        def __init__(self, parent):
            super().__init__(parent)

        def eventFilter(self, obj, e):
            if e.type() == QEvent.KeyPress or e.type() == QEvent.ShortcutOverride:
                key = e.key()
                mod = e.modifiers()

                #print(obj.focusWidget().metaObject().className())

            return False

    
    def scroll_left(self):
        print('alt-left')
        if self.ToolIndex == 3 or self.ToolIndex == 2:
            self.ToolList[self.ToolIndex].finish_edit()
            
        self.ToolIndex -= 1
        if self.ToolIndex < 0:
            self.ToolIndex = len(self.ToolList) - 1
            
        print('Tool Index: ' + str(self.ToolIndex))
        self.ToolList[self.ToolIndex].setFocus()
        
    def scroll_right(self):
        print('alt-right')
        if self.ToolIndex == 3 or self.ToolIndex == 2:
            self.ToolList[self.ToolIndex].finish_edit()
            
        self.ToolIndex += 1
        if self.ToolIndex == len(self.ToolList):
            self.ToolIndex = 0

        print('Tool Index: ' + str(self.ToolIndex))
        self.ToolList[self.ToolIndex].setFocus()
        
    def mouse_change_tool(self, s):
        print('Tool ' + s)
        if s == 'CmpTable':
            self.ToolIndex = 0
        elif s == 'Selector':
            self.ToolIndex = 1
        elif s == 'Inspector':
            self.ToolIndex = 2
        elif s == 'FieldInspector':
            self.ToolIndex = 3
            
        if self.ToolIndex != 3:
            self.ToolList[3].finish_edit()
        
        
    def __init__(self):
        super().__init__()
        
        self.initUI()

        self.installEventFilter(self.EventFilter(self))
        
        self.setFocusPolicy(Qt.WheelFocus)
        self.setTabOrder(self.CmpTable,      self.Inspector )
        self.setTabOrder(self.Inspector,     self.Selector)
        self.setTabOrder(self.Selector,      self.FieldInspector)
        #self.setTabOrder(self.FieldInspector, self.CmpTable)

        #----------------------------------------------------
        #
        #   Application hotkeys
        #
        self.shortcutLeft  = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Left), self)
        self.shortcutRight = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Right), self)
        self.shortcutLeft.setContext(Qt.ApplicationShortcut)
        self.shortcutRight.setContext(Qt.ApplicationShortcut)
        self.shortcutLeft.activated.connect(self.scroll_left)
        self.shortcutRight.activated.connect(self.scroll_right)
        
        
    def initUI(self):
        
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
        
        self.CmpTabLayout.setSizeConstraint(QVBoxLayout.SetMaximumSize)
        
        #----------------------------------------------------
        #
        #    Components table
        #
        self.CmpTable       = ComponentsTable(self) 
        self.CmpChooseButton = QPushButton('Choose', self)
        
        self.CmpTabLayout.addWidget(self.CmpTable)
        self.CmpTabLayout.addWidget(self.CmpChooseButton)
        
                
        #----------------------------------------------------
        #
        #    Selector
        #
        self.Selector = Selector(self)
        
        #----------------------------------------------------
        #
        #    Inspector
        #
        self.Inspector       = Inspector(self)
        self.FieldInspector  = FieldInspector(self)
        self.InspectorAdd    = QPushButton('Add Parameter', self)
        self.InspectorDelete = QPushButton('Delete Parameter', self)
        self.InspectorRename = QPushButton('Rename Parameter', self)
        
        self.InspectorBox    = QGroupBox('Inspector', self)
        self.InspectorSplit  = QSplitter(Qt.Vertical, self)
        self.InspectorLayout = QVBoxLayout(self.InspectorBox)
        self.InspectorLayout.setContentsMargins(4,10,4,4)
        self.InspectorLayout.setSpacing(2)
        
        
        self.InspectorSplit.addWidget(self.Inspector)
        self.InspectorSplit.addWidget(self.FieldInspector)
        self.InspectorLayout.addWidget(self.InspectorSplit)
        self.InspectorLayout.addWidget(self.InspectorAdd)
        self.InspectorLayout.addWidget(self.InspectorDelete)
        self.InspectorLayout.addWidget(self.InspectorRename)
                
        #----------------------------------------------------

        self.Splitter = QSplitter(self)
        self.Splitter.addWidget(self.CmpTabBox)
        self.Splitter.addWidget(self.Selector)   
        self.Splitter.addWidget(self.InspectorBox) 
                 
        self.centralWidget().layout().addWidget(self.Splitter)
        
        
        #----------------------------------------------------
        self.CmpTable.cells_chosen.connect(self.Inspector.load_cmp)
        self.Inspector.load_field.connect(self.FieldInspector.load_field_slot)
        
        self.CmpTable.mouse_click.connect(self.mouse_change_tool)
        self.Inspector.mouse_click.connect(self.mouse_change_tool)
        self.FieldInspector.mouse_click.connect(self.mouse_change_tool)

        self.Inspector.header().sectionResized.connect(self.FieldInspector.column_resize)
        
        self.ToolList = []
        self.ToolList.append(self.CmpTable)
        self.ToolList.append(self.Selector)
        self.ToolList.append(self.Inspector)
        self.ToolList.append(self.FieldInspector)
        self.ToolIndex = 0
        
        
        #----------------------------------------------------
        #
        #    Window
        #
        self.setWindowTitle('KiCad Schematic Component Manager')
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        #print(Settings.allKeys())
        if Settings.contains('geometry'):
            self.restoreGeometry( Settings.value('geometry') )
        else:
            self.setGeometry(100, 100, 1024, 768)

        if Settings.contains('cmptable'):
            w0, w1 = Settings.value('cmptable')
            self.CmpTable.setColumnWidth( 0, int(w0) )
            self.CmpTable.setColumnWidth( 1, int(w1) )
            
        if Settings.contains('inspector'):
            w0, w1, w2 = Settings.value('inspector')
            self.Inspector.setColumnWidth( 0, int(w0) )
            self.Inspector.setColumnWidth( 1, int(w1) )
            self.FieldInspector.setColumnWidth( 0, int(w0) )
            self.FieldInspector.setColumnWidth( 1, int(w1) )
            #self.Inspector.setColumnWidth( 2, int(w2) )
            
        if Settings.contains('splitter'):
            self.Splitter.restoreState( Settings.value('splitter') )
            
        if Settings.contains('inssplitter'):
            self.InspectorSplit.restoreState( Settings.value('inssplitter') )
            
        self.show()
        
                
    #---------------------------------------------------------------------------    
    def closeEvent(self, event):
        #print('close app')
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        Settings.setValue( 'geometry', self.saveGeometry() )
        Settings.setValue( 'cmptable',  [self.CmpTable.columnWidth(0), self.CmpTable.columnWidth(1)] )
        Settings.setValue( 'inspector', [self.Inspector.columnWidth(0), self.Inspector.columnWidth(1), self.Inspector.columnWidth(2)] )
        Settings.setValue( 'splitter', self.Splitter.saveState() )
        Settings.setValue( 'inssplitter', self.InspectorSplit.saveState() )
        QWidget.closeEvent(self, event)
        
        
#       for ref in self.CmpTable.CmpDict.keys():
#           print( ref + ' ' + self.CmpTable.CmpDict[ref][0].Fields[2].Text)
        

#-------------------------------------------------------------------------------
class ComponentField:
    
    #--------------------------------------------------------------
    def __init__(self, comp, rec):

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
        self.Orientation = 'Horizontal' if rec[2] == 'H' else 'Vertical'
        self.PosX        = str( int(rec[3]) - int(comp.PosX) )
        self.PosY        = str( int(rec[4]) - int(comp.PosY) )
        self.FontSize    = rec[5]
        self.Visible     = 'Yes'  if int(rec[6]) == 0 else 'No'
        self.HJustify    = 'Left' if rec[7]  == 'L' else 'Center' if rec[7] == 'C' else 'Right'
        self.VJustify    = 'Top'  if rec[8]  == 'T' else 'Center' if rec[8] == 'C' else 'Bottom'
        self.FontItalic  = 'Yes'  if rec[9]  == 'I' else 'No'
        self.FontBold    = 'Yes'  if rec[10] == 'B' else 'No'
    
    #--------------------------------------------------------------
    @classmethod
    def default(cls, comp, name, Fn):
        rec = []
        rec.append( str(Fn) )
        rec.append( '~' )
        rec.append( 'H' )
        rec.append( comp.PosX )
        rec.append( comp.PosY )
        rec.append( comp.Fields[0].FontSize )
        rec.append( '0000' )
        rec.append( 'C' )
        rec.append( 'C' )
        rec.append( 'N' )
        rec.append( 'N' )
        rec.append( name )
        return cls(comp, rec)
        
   #--------------------------------------------------------------
    def dump(self):
        print('Text        : ' + self.Text)
        print('Orientation : ' + self.Orientation)
        print('X           : ' + self.PosX)
        print('Y           : ' + self.PosY)
        print('Visible     : ' + self.Visible)
        print('H Justify   : ' + self.HJustify)
        print('V Justify   : ' + self.VJustify)
        print('Font Size   : ' + self.FontSize)
        print('Font Italic : ' + self.FontItalic)
        print('Font Bold   : ' + self.FontBold)
        
    #--------------------------------------------------------------
    def dump_line(self):
        print(self.Name        + ' '*(12 - len(self.Name)) +
              self.Text[0:11]  + ' '*(12 - len(self.Text[0:11])) +
              self.Orientation + ' '*(14 - len(self.Orientation)) + 
              self.PosX        + ' '*(6  - len(self.PosX)) + 
              self.PosY        + ' '*(6  - len(self.PosY)) + 
              self.Visible     + ' '*(8  - len(self.Visible)) + 
              self.HJustify    + ' '*(9  - len(self.HJustify)) + 
              self.VJustify    + ' '*(9  - len(self.VJustify)) + 
              self.FontSize    + ' '*(7  - len(self.FontSize)) + 
              self.FontItalic  + ' '*(8  - len(self.FontItalic)) + 
              self.FontBold    + ' '*(5  - len(self.FontBold)) + 
              'F' + self.InnerCode)
        
#-------------------------------------------------------------------------------
class Component:
    
    def __init__(self):
        self.Ref = '~'
        self.LibName = '~'
        
    def parse_comp(self, rec):
        r = re.search('L ([\w-]+) ([\w#]+)', rec)
        if r:
            self.LibName, self.Ref = r.groups()
        else:
            print('E: invalid component L record, rec: "' + rec + '"')
            sys.exit(1)
           
        if not re.match( '\D+\d+',  r.group(2) ):
            print('E: schematic must be annotated before loading in Component Manager' + os.linesep*2 + rec)
            sys.exit(2)
            
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
        #print(r)
        
        self.Fields = []
        for i in r:
            self.Fields.append( ComponentField(self, i) )
        
        r = re.search('(\s+\d\s+\d+\s+\d+\n\s+-*[01]\s+-*[01]\s+-*[01]\s+-*[01]\s*)', rec)
        if r:
            self.Trailer = r.groups()[0]
            print(self.Trailer)
        else:
            print('E: invalid component trailer record, rec: "' + rec + '"')
            sys.exit(1)
         
            
        #self.dump()

    #--------------------------------------------------------------
    def field(self, fname):
        for f in self.Fields:
            if fname == f.Name:
                return f
                
        return None
        
    #--------------------------------------------------------------
    def add_field(self, f):
        self.Fields.append(f)
        
    #--------------------------------------------------------------
    def dump(self):
        if int(self.PartNo) > 1:
            part = '.' + self.PartNo
        else:
            part = ''
            
        print('===================================================================================================')
        print('Ref       : ' + self.Ref + part)
        print('Lib Name  : ' + self.LibName)
        print('X         : ' + self.PosX)
        print('Y         : ' + self.PosY)
        print('Timestump : ' + self.Timestamp)
        
        print('--------------------------------------------------------------------------------------------------')
        print('Name         Text       Orientation    X     Y   Visible  H Align  V Align  Font  Italic  Bold  ID')
        print('--------------------------------------------------------------------------------------------------')
        for f in self.Fields:
            f.dump_line()
            #f.dump()
   
        print('===================================================================================================')
        
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
    
    with open('kscm.qss', 'rb') as fqss:
        qss = fqss.read().decode()
        qss = re.sub(os.linesep, '', qss )
    app.setStyleSheet(qss)
    
    mwin = MainWindow()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


