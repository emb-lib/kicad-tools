# coding: utf-8

#-------------------------------------------------------------------------------
#
#    Project: KiCad Tools
#    
#    Name:    KiCad Schematic Component Manager
#   
#    Purpose: Edit components properties (and its parameters)
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

from cmpmgr    import *

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QApplication, QLineEdit,QComboBox, 
                             QStyledItemDelegate, QAbstractItemDelegate, 
                             QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView, 
                             QInputDialog, QMessageBox)

from PyQt5.Qt     import QShortcut, QKeySequence, QStyle
from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent, QPen
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
                   ['LibRef',           'TextItemDelegate', None],
                   ['Value',            'TextItemDelegate', None],
                   ['Footprint',        'TextItemDelegate', None],
                   ['DocSheet',         'TextItemDelegate', None],
                   ['X',                'TextItemDelegate', None],
                   ['Y',                'TextItemDelegate', None],
                   ['Timestamp',        'TextItemDelegate', None] ]

    NonFieldProps = [ 'LibRef',
                      'X',
                      'Y',
                      'Timestamp' ]
    
    #---------------------------------------------------------------------------    
    load_field   = pyqtSignal( [list], [str] )
    mouse_click  = pyqtSignal([str])
    #data_changed = pyqtSignal()
    update_comps = pyqtSignal()
    #---------------------------------------------------------------------------    
            
#-------------------------------------------------------------------------------    
    class InspectorItemsDelegate(QStyledItemDelegate):

        TEXT_DELEGATE = 0
        CBOX_DELEGATE = 1
        
        #----------------------------------------------------------------
        def __init__(self, parent):
            super().__init__(parent)
            self.editors = {}
        #----------------------------------------------------------------
        def clear_editor_data(self):
            self.editors = {}
        #----------------------------------------------------------------    
        def add_editor_data(self, name, editor_type, editor_data = []):
            self.editors[name] = [editor_type, editor_data]
        #----------------------------------------------------------------    
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
        #----------------------------------------------------------------
        def setEditorData(self, editor, idx):
            #print(editor.metaObject().className() )
            name = idx.sibling(idx.row(), 0).data()
            if self.editors[name][0] == self.TEXT_DELEGATE:
                QStyledItemDelegate.setEditorData(self, editor, idx)
            else:
                value = idx.model().data(idx, Qt.EditRole)
                editor.set_index(value)
        #----------------------------------------------------------------
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
        #----------------------------------------------------------------
        def paint(self, painter, option, idx):
            painter.save()
                
            # set background color
            painter.setPen(QPen(Qt.NoPen))
            
            if idx.column() == 0:
                ccode = 245
                painter.setBrush(QBrush(QColor(ccode, ccode, ccode)))
            else:
                painter.setBrush(QBrush(Qt.transparent))

            if not idx.parent().isValid():
                painter.setBrush(QBrush(QColor(0xFF, 0xDC, 0xA4) ) )
                    
            painter.drawRect(option.rect)
    
            # draw the rest
            
            QStyledItemDelegate.paint(self, painter, option, idx)
                
            painter.restore()            
    #---------------------------------------------------------------------------    
    def add_property(self):
        print('Inspector::add property')
        text, ok = QInputDialog.getText(self, 'Add Property', 'Enter Property Name')
        
        if len(text) > 0:
            for c in self.comps:
                if not c.field(text):
                    f = ComponentField.default(c, text)
                    c.add_field(f)
        
            self.load_user_defined_props()
    #---------------------------------------------------------------------------    
    def remove_property(self):
        print('Inspector::delete property')
        
        item = self.currentItem()
        name  = item.data(colNAME, Qt.DisplayRole)
        reply = QMessageBox.question(self, 'Delete Property', 'Delete "' + name + '" property?' )
        
        if reply == QMessageBox.No:
            return

        for c in self.comps:
            f = c.field(name)
            c.remove_field(f)

        self.load_user_defined_props()
    #---------------------------------------------------------------------------    
    def rename_property(self):
        print('Inspector::rename property')
        item = self.currentItem()
        name  = item.data(colNAME, Qt.DisplayRole)
        print(name)
        text, ok = QInputDialog.getText(self, 'Rename Property', 'Enter New Proterty Name', QLineEdit.Normal, name)
        print(text)

        if len(text) > 0:
            for c in self.comps:
                f = c.field(name)
                f.Name = text
    
            self.load_user_defined_props()
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
        self.itemChanged.connect(self.item_changed)
        self.currentItemChanged.connect(self.curr_item_changed)
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
    #---------------------------------------------------------------------------    
    def item_changed(self, item, col):
        if self.load_cmp_sem:
            return
            
        print(item.data(colNAME, Qt.DisplayRole), item.data(colDATA, Qt.DisplayRole))
        self.save_cmps()
        #self.data_changed.emit()    
    #---------------------------------------------------------------------------    
    def curr_item_changed(self, item, prev):
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
    def prepare_std_props(self, item):
        name  = item.data(colNAME, Qt.DisplayRole)
        l = []
        for c in self.comps:
            if name in self.NonFieldProps:
                l.append( getattr(c, name) )
            else:
                #print(c.Ref, name)
                f = c.field(name)
                l.append( getattr(f, 'Text') )
                
        vals = list(set(l))
        vals.sort()
        
        if len(vals) == 0:
            self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.TEXT_DELEGATE)
            item.setData(colDATA, Qt.DisplayRole, '')

        elif len(vals) == 1:
            self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.TEXT_DELEGATE)
            item.setData(colDATA, Qt.DisplayRole, vals[0])

        else:
            vals.insert(0, MULTIVALUE)
            self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.CBOX_DELEGATE, vals)
            idx    = self.indexFromItem(self.currentItem(), colDATA)
            editor = self.indexWidget(idx)
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            item.setData(colDATA, Qt.DisplayRole, vals[0])
    #---------------------------------------------------------------------------    
    def reduce_list(self, l):
        l = list(set(l))
        l.sort()
        return l
    #---------------------------------------------------------------------------    
    def user_defined_props(self):
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
    def load_user_defined_props(self):
        #self.topLevelItem(1).takeChildren()
        if not self.comps:
            return 
        
        user_fields = self.user_defined_props()        

        user_fields_names = list(user_fields.keys())
        user_fields_names.sort()
        
        item_names = []
        for i in range( self.topLevelItem(1).childCount()-1, -1, -1 ):  # reverse order to prevent collision with indices when take child
            item = self.topLevelItem(1).child(i)
            item_name = item.data(colNAME, Qt.DisplayRole)
            item_names.append( item_name )
            if item_name not in user_fields_names:
                if item == self.currentItem():
                    self.setCurrentItem(self.topLevelItem(1))
                self.topLevelItem(1).takeChild(i)
        
        for name in user_fields_names:
            if name not in item_names:
                item = self.addChild(self.usr_items, name, user_fields[name][0])
            else:
                for i in range( self.topLevelItem(1).childCount() ):
                    item = self.topLevelItem(1).child(i)
                    if item.data(colNAME, Qt.DisplayRole) == name:
                        break

            vals = user_fields[name]
            if len(vals) == 1:
                self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.TEXT_DELEGATE)
            else:
                self.ItemsDelegate.add_editor_data(name, self.InspectorItemsDelegate.CBOX_DELEGATE, vals)
                
            item.setData(colDATA, Qt.DisplayRole, vals[0])
    #---------------------------------------------------------------------------
    def load_cmp(self, cmps):
        print('Inspector::load_cmp')
        
        self.load_cmp_sem = True
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
        
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)
            self.prepare_std_props(item)
        
        self.load_user_defined_props()            
        curr_item = self.currentItem()   
        if curr_item:
            self.item_clicked(curr_item, colNAME)
            
        self.load_cmp_sem = False
    #---------------------------------------------------------------------------                            
    def save_cmps(self):
        print('Inspector::save_cmps')
        if not hasattr(self, 'comps'):
            return

        for c in self.comps:
            subst_list = []
            item_list =  []
            #---------------------------------------------
            #
            #   Collect items
            #        
            for i in range( self.topLevelItem(0).childCount() ):
                item_list.append( self.topLevelItem(0).child(i) )
                
            for i in range( self.topLevelItem(1).childCount() ):
                item_list.append( self.topLevelItem(1).child(i) )
                
            #---------------------------------------------
            #
            #   Process items
            #        
            for item in item_list:
                
                item_name  = item.data(colNAME, Qt.DisplayRole)
                item_value = item.data(colDATA, Qt.DisplayRole)
                
                if item_name[0] == '@':
                    if item_value != MULTIVALUE:
                        subst_list.append( [item_name[1:], item_value] )
                        c.field(item_name).Text = item_value
                    else:
                        subst_list.append( [item_name[1:], c.field(item_name).Text] )
                    
                    #print(c.Ref, item_name, item_value)
                    continue
                    
                if '$' in item_value:
                    subst_list.append( [item_name, item_value] )
                    continue
                    
                if item_value != MULTIVALUE:
                    if item_name in self.NonFieldProps:
                        setattr(c, item_name, item_value)
                    else:
                        f = c.field(item_name)
                        f.Text = item_value
                    
            #---------------------------------------------
            #
            #   Pattern substitution
            #        
            for s in subst_list:
                item_name  = s[0]
                item_value = c.get_str_from_pattern( s[1] )
                if item_name in self.NonFieldProps:
                    setattr(c, item_name, item_value)
                else:
                    f = c.field(item_name)
                    f.Text = item_value
                    
                #s[2].setData(colDATA, Qt.DisplayRole, item_value)

                    
        self.update_comps.emit()
#-------------------------------------------------------------------------------    
class FieldInspector(QTreeWidget):
    
    mouse_click  = pyqtSignal([str])
    data_changed = pyqtSignal()
    
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
    class FieldInspectorItemsDelegate(QStyledItemDelegate):

        TEXT_DELEGATE = 0
        CBOX_DELEGATE = 1
        #----------------------------------------------------------------
        def __init__(self, parent):
            super().__init__(parent)
            self.editors = {}
        #----------------------------------------------------------------
        def clear_editor_data(self):
            self.editors = {}
        #----------------------------------------------------------------
        def add_editor_data(self, name, editor_type, editor_data = []):
            self.editors[name] = [editor_type, editor_data]
        #----------------------------------------------------------------
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
        #----------------------------------------------------------------
        def setEditorData(self, editor, idx):
            #print(editor.metaObject().className() )
            name = idx.sibling(idx.row(), 0).data()
            if self.editors[name][0] == self.TEXT_DELEGATE:
                QStyledItemDelegate.setEditorData(self, editor, idx)
            else:
                value = idx.model().data(idx, Qt.EditRole)
                editor.set_index(value)
        #----------------------------------------------------------------
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
        #----------------------------------------------------------------        
        def paint(self, painter, option, idx):
            painter.save()

            # set background color
            painter.setPen(QPen(Qt.NoPen))

            if idx.column() == 0:
                ccode = 245
                painter.setBrush(QBrush(QColor(ccode, ccode, ccode)))
            else:
                painter.setBrush(QBrush(Qt.transparent))

            if not idx.parent().isValid():
                painter.setBrush(QBrush(QColor(0xFF, 0xDC, 0xA4) ) )

            painter.drawRect(option.rect)

            # draw the rest

            QStyledItemDelegate.paint(self, painter, option, idx)

            painter.restore()            
    #---------------------------------------------------------------------------
    #
    #              Title              Field Name         Delegate         Delegate Data
    #
    ItemsTable = [ ['X',                'X',           'TextItemDelegate', None],
                   ['Y',                'Y',           'TextItemDelegate', None],
                   ['Orientation',      'Orientation', 'CBoxItemDelegate', ['Horizontal', 'Vertical']],
                   ['Visible',          'Visible',     'CBoxItemDelegate', ['Yes',  'No']],
                   ['Horizontal Align', 'HJustify',    'CBoxItemDelegate', ['Left', 'Center', 'Right']],
                   ['Vertical Align',   'VJustify',    'CBoxItemDelegate', ['Top',  'Center', 'Bottom']],
                   ['Font Size',        'FontSize',    'TextItemDelegate', None],
                   ['Font Bold',        'FontBold',    'CBoxItemDelegate', ['Yes', 'No']],
                   ['Font Italic',      'FontItalic',  'CBoxItemDelegate', ['Yes', 'No']] ]
    
    ItemsParamNameMap =\
    {
        'X'                : [ 'X'                                         ],
        'Y'                : [ 'Y'                                         ], 
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
        
        self.field_items = self.addParent(self, 0, 'Field Parameters', '')
    
        for idx, i in enumerate(self.ItemsTable):
            self.addChild(self.field_items, i[0], '')
            
        self.ItemsDelegate = self.FieldInspectorItemsDelegate(self)
        self.setItemDelegate(self.ItemsDelegate)
                
        self.itemClicked.connect(self.item_clicked)
        self.itemPressed.connect(self.item_pressed)
        self.itemChanged.connect(self.item_changed)
        self.currentItemChanged.connect(self.curr_item_changed)
        self.itemActivated.connect(self.item_activated)
    
        self.field = None
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
    def item_changed(self, item, col):
        if self.load_field_sem:
            return

        self.save_fields()
        self.data_changed.emit()    
    #---------------------------------------------------------------------------    
    def curr_item_changed(self, item, prev):
        
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
            self.field.X = item.data(colDATA, Qt.DisplayRole)

        if item.data(colNAME, Qt.DisplayRole) == 'Y':
            self.field.Y = item.data(colDATA, Qt.DisplayRole)
    #---------------------------------------------------------------------------    
    def finish_edit(self):
        idx    = self.indexFromItem(self.currentItem(), colDATA)
        editor = self.indexWidget(idx)

        if editor:
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
            vals.append( getattr(f, fparam_name) )
                
        vals = self.reduce_list(vals)
                     
        if len( self.ItemsParamNameMap[item_name] ) == 1:
            if len(vals) == 1:
                self.ItemsDelegate.add_editor_data(item_name, self.FieldInspectorItemsDelegate.TEXT_DELEGATE)
            else:
                vals.insert(0, MULTIVALUE)
                self.ItemsDelegate.add_editor_data(item_name, self.FieldInspectorItemsDelegate.CBOX_DELEGATE, vals)
                
            data_val = vals[0]
        else:
            data_val = vals[0]
            if len(vals) > 1:
                vals = [MULTIVALUE] + self.ItemsParamNameMap[item_name][1] 
                data_val = vals[0]
            else:
                vals = self.ItemsParamNameMap[item_name][1] 

            self.ItemsDelegate.add_editor_data(item_name, self.FieldInspectorItemsDelegate.CBOX_DELEGATE, vals)
            
        item.setData(colDATA, Qt.DisplayRole, data_val)
    #---------------------------------------------------------------------------    
    def load_field(self):
        
        self.load_field_sem = True
        
        NO_FIELD_PARAMS = ['LibRef', 'X', 'Y', 'Timestamp']

        comps = self.comps
        param = self.param
        
        if (param in NO_FIELD_PARAMS) or (len(comps) == 0):
            for i in range( self.topLevelItem(0).childCount() ):
                item = self.topLevelItem(0).child(i)
                item.setData(colDATA, Qt.DisplayRole, '')
                if hasattr(self, 'field_list'):
                    delattr(self, 'field_list')
                    
            self.load_field_sem = False
            return
        
        flist = []
        for c in comps:
            flist.append( c.field(param) )
                        
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)
            self.prepare_item(item, flist)
        
        self.field_list = flist
        self.load_field_sem = False
    #---------------------------------------------------------------------------    
    def save_fields(self):
        print('FieldInspector::save_fields')
          
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

