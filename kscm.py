#!/usr/bin/python3
# coding: utf-8


import sys
import os
import re
import yaml
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction, QComboBox,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, QSplitter, QStyledItemDelegate,
                             QAbstractItemDelegate, 
                             QTableWidget, QTableWidgetItem, QCommonStyle, QTreeWidget, QTreeWidgetItem,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication)

from PyQt5.QtGui  import  QIcon, QBrush, QColor
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent, QModelIndex, QItemSelectionModel

#-------------------------------------------------------------------------------
colEDIT = 0
colNAME = 0
colDATA = 1
#-------------------------------------------------------------------------------
class Inspector(QTreeWidget):
    
    
    load_field = pyqtSignal( [list], [str] )
    
        
    class ItemDelegate(QStyledItemDelegate):

        def __init__(self, parent):
            super().__init__(parent)
            
        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                print( idx.column() )
                return QStyledItemDelegate.createEditor(self, parent, option, idx)
    
        
    #---------------------------------------------------------------------------    
    def __init__(self, parent):
        super().__init__(parent)
        #self.setAlternatingRowColors(True)
        self.setIndentation(16)
        self.setColumnCount(2)
        self.header().resizeSection(2, 10)
        self.header().setSectionResizeMode(colNAME, QHeaderView.Interactive)
        #self.header().setStretchLastSection(False)
        #self.setHeaderLabels( ('Edit', 'Property', 'Value') );
        self.setHeaderLabels( ('Property', 'Value') );
        self.std_items   = self.addParent(self, 0, 'Standard', 'slon')
        self.usr_items   = self.addParent(self, 0, 'User Defined', 'mamont')
        
        self.addChild(self.std_items, 'Ref',       '?')
        self.addChild(self.std_items, 'Lib Name',  '~')
        self.addChild(self.std_items, 'Value',     '~')
        self.addChild(self.std_items, 'Footprint', '~')
        self.addChild(self.std_items, 'Doc Sheet', '~')
        self.addChild(self.std_items, 'X',         '~')
        self.addChild(self.std_items, 'Y',         '~')
        self.addChild(self.std_items, 'Timestamp', '~')
    
        self.addChild(self.usr_items, '<empty>', '')
            
        self.itemClicked.connect(self.item_clicked)
        self.currentItemChanged.connect(self.item_changed)
        self.itemActivated.connect(self.item_activated)
        
        self.setItemDelegate(self.ItemDelegate(self))
        
    #---------------------------------------------------------------------------    
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        item.setExpanded (True)
        item.setFlags(Qt.ItemIsEnabled)
        return item
        
    #---------------------------------------------------------------------------    
    def addChild(self, parent, title, data, flags=Qt.NoItemFlags):
        item = QTreeWidgetItem(parent, [title])
        item.setData(colDATA, Qt.DisplayRole, data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | flags)
        
#       if flags & Qt.ItemIsEditable:
#           item.setCheckState (colEDIT, Qt.Checked)
#       else:
#           item.setCheckState (colEDIT, Qt.Unchecked)
        return item
            
    #---------------------------------------------------------------------------    
    def item_clicked(self, item, col):
#       if item.checkState(colEDIT) == Qt.Checked:
#           item.setFlags( item.flags() | Qt.ItemIsEditable)
#       else:
#           item.setFlags( item.flags() & (-Qt.ItemIsEditable - 1) )
        
        param = item.data(colNAME, Qt.DisplayRole)
        comp = self.comps[0]
        if item.parent() == self.topLevelItem(0):
            self.load_field.emit([comp, param])
                
        if item.parent() == self.topLevelItem(1):
            print('user defined')
            
    #---------------------------------------------------------------------------    
    def item_changed(self, item, prev):
        self.item_clicked(item, colNAME)
                
    #---------------------------------------------------------------------------    
    def item_activated(self, item, col):
        self.editItem(item, colDATA)
            
    #---------------------------------------------------------------------------    
    def load_cmp(self, refs):
        
        self.comps = refs[0]
        comp = self.comps[0]
        
        #print( (comp.__dict__) )
        #print(self.topLevelItem(0).childCount())
        
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)

            if item.data(colNAME, Qt.DisplayRole) == 'Ref':
                item.setData(colDATA, Qt.DisplayRole, comp.Ref)
                
            if item.data(colNAME, Qt.DisplayRole) == 'Lib Name':
                item.setData(colDATA, Qt.DisplayRole, comp.LibName)
                
            if item.data(colNAME, Qt.DisplayRole) == 'Value':
                item.setData(colDATA, Qt.DisplayRole, comp.Fields[1].Text)
                
            if item.data(colNAME, Qt.DisplayRole) == 'Footprint':
                item.setData(colDATA, Qt.EditRole, comp.Fields[2].Text)
                
            if item.data(colNAME, Qt.DisplayRole) == 'Doc Sheet':
                item.setData(colDATA, Qt.DisplayRole, comp.Fields[3].Text)
                
            if item.data(colNAME, Qt.DisplayRole) == 'X':
                item.setData(colDATA, Qt.DisplayRole, comp.PosX)
                                
            if item.data(colNAME, Qt.DisplayRole) == 'Y':
                item.setData(colDATA, Qt.DisplayRole, comp.PosY)
                
            if item.data(colNAME, Qt.DisplayRole) == 'Timestamp':
                item.setData(colDATA, Qt.DisplayRole, comp.Timestamp)
        
        self.topLevelItem(1).takeChildren()
                        
        for f in comp.Fields[4:]:
            #print( f.InnerCode )
            self.addChild(self.usr_items, f.Name, f.Text, Qt.ItemIsEditable)
        
            
#-------------------------------------------------------------------------------    
class TComboBox(QComboBox):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        #print('TComboBox')

    def keyPressEvent(self, e):
        #print( e.key() )
        if e.key() == Qt.Key_Down or e.key() == Qt.Key_Up:
            #print('Up/Down')
            #print(type(self.parent()))
            QApplication.sendEvent( self.parent(), e ) 
            #self.parent().keyPressEvent(e)
            return
            
        QComboBox.keyPressEvent(self, e)

    def set_index(self, text):
        items = [self.itemText(i) for i in range(self.count()) ]
        self.setCurrentIndex( items.index(text) )
        
#-------------------------------------------------------------------------------    
class FieldInspector(QTreeWidget):
    
    class FieldParam:
    
        def __init__(self, name, title, editor, values):
            self.name   = name
            self.title  = title
            self.editor = editor
            self.values = values
    
    #---------------------------------------------------------------------------    
    class ItemDelegate(QStyledItemDelegate):

        params = {}
        
        def __init__(self, parent):
            super().__init__(parent)
            
            self.params['Orientation']      = [TComboBox, ['Horizontal', 'Vertical']]
            self.params['Visible']          = [TComboBox, ['Yes', 'No']]
            self.params['Horizontal Align'] = [TComboBox, ['Left', 'Center', 'Right']]
            self.params['Vertical Align']   = [TComboBox, ['Top', 'Center', 'Bottom']]

        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                param = idx.sibling(idx.row(), 0).data() 

                if param in self.params.keys():
                    #cb = TComboBox(parent.parent())
                    cb = self.params[param][0](parent.parent())
                    cb.setEnabled(True)
                    cb.addItems( self.params[param][1] )
                    cb.setCurrentIndex( 0 ) # if f.Orientation == 'H' else 1 )
                    f = parent.parent().field
                    print(eval('f.' + param) )
                    return cb

                return QStyledItemDelegate.createEditor(self, parent, option, idx)

        def setEditorData(self, editor, idx):
            print(editor.metaObject().className() )

    #---------------------------------------------------------------------------    
    class TextItemDelegate(QStyledItemDelegate):


        def __init__(self, parent, values):
            super().__init__(parent)

        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                return QStyledItemDelegate.createEditor(self, parent, option, idx)
    
    #---------------------------------------------------------------------------    
    class CBoxItemDelegate(QStyledItemDelegate):

        def __init__(self, parent, values):
            super().__init__(parent)
            self.values = values

        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                editor = TComboBox(parent.parent())
                editor.setEnabled(True)
                editor.addItems( self.values )
                return editor

        def setEditorData(self, editor, idx):
            #print(editor.metaObject().className() )
            value = idx.model().data(idx, Qt.EditRole)
            editor.set_index(value)
            
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
            print(event)
            
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

            return False

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
    def focusOutEvent(self, e):
        #self.selectionModel().setCurrentIndex(self.currentIndex(), QItemSelectionModel.Deselect)
        print('focusOutEvent')
        self.clearSelection()
        
    #---------------------------------------------------------------------------    
    def item_clicked(self, item, col):
        print('item_clicked')
        self.select_item(item)            
        
    #---------------------------------------------------------------------------    
    def item_pressed(self, item, col):
        print('item_pressed')
        print(item)
        print(col)
        self.select_item(item)
        
    #---------------------------------------------------------------------------    
    def item_changed(self, item, prev):
        
        if not self.field:
            return 
                
        idx = self.indexFromItem(prev, colDATA)
        print('item_changed')
        editor = self.indexWidget(idx)
            
        if editor:
            self.commitData(editor)
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            
                        
        self.editItem(item, colDATA)
        self.handle_item(item)    
        self.item_clicked(item, colNAME)
        #self.select_item(item)
    
    #---------------------------------------------------------------------------    
    def item_activated(self, item, col):
        if not self.field:
            return 

        self.editItem(item, colDATA)
    
    #---------------------------------------------------------------------------    
    def select_item(self, item):
        pass
        self.setCurrentItem(item, colNAME)
        self.selectionModel().setCurrentIndex(self.currentIndex(), QItemSelectionModel.ClearAndSelect)
        
    #---------------------------------------------------------------------------    
    def load_field_slot(self, d):
        self.comp  = d[0]
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
    def load_field(self):
        
        comp  = self.comp
        param = self.param
        
        if param == 'Ref':
            f = self.comp.Fields[0]
        elif param == 'Value':
            f = self.comp.Fields[1]
        elif param == 'Footprint':
            f = self.comp.Fields[2]
        elif param == 'Doc Sheet':
            f = self.comp.Fields[3]
        else:
            f = None
            
        self.field = f
            
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)
            if f:
                item.setData( colDATA, Qt.DisplayRole, eval('f.' + self.ItemsTable[i][1]) )
            else:
                item.setData( colDATA, Qt.DisplayRole, '' )
                    
    
    #---------------------------------------------------------------------------    
    def column_resize(self, idx, osize, nsize):
        self.setColumnWidth(idx, nsize)
                    
                                    
#-------------------------------------------------------------------------------
class ComponentsTable(QTableWidget):
    
    cells_chosen = pyqtSignal([list])
    
    def __init__(self, parent):
        super().__init__(0, 2, parent)
        
        self.cellActivated.connect(self.cell_activated)

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
        
                
    #---------------------------------------------------------------------------    
    def cell_activated(self, row, col):
        items = self.selectedItems()
        refs = []
        for i in items:
            if i.column() == 0:
                refs.append( self.CmpDict[i.data(Qt.DisplayRole)] )
        
        print('emit "cells_chosen"')
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
        self.Splitter.addWidget(self.SelectView)   
        self.Splitter.addWidget(self.InspectorBox) 
                 
        self.centralWidget().layout().addWidget(self.Splitter)
        
        
        #----------------------------------------------------
        self.CmpTable.cells_chosen.connect(self.Inspector.load_cmp)
        self.Inspector.load_field.connect(self.FieldInspector.load_field_slot)

        self.Inspector.header().sectionResized.connect(self.FieldInspector.column_resize)
        
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
        print('close app')
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
        self.Orientation = 'Horizontal' if rec[2] == 'H' else 'Vertical'
        self.PosX        = rec[3]
        self.PosY        = rec[4]
        self.FontSize    = rec[5]
        self.Visible     = 'Yes'  if int(rec[6]) == 0 else 'No'
        self.HJustify    = 'Left' if rec[7]  == 'L' else 'Center' if rec[7] == 'C' else 'Right'
        self.VJustify    = 'Top'  if rec[8]  == 'T' else 'Center' if rec[8] == 'C' else 'Bottom'
        self.FontItalic  = 'Yes'  if rec[9]  == 'I' else 'No'
        self.FontBold    = 'Yes'  if rec[10] == 'B' else 'No'
    
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
    app.setStyleSheet( 'QGroupBox {\
                            border: 2px solid gray;\
                            border-radius: 4px;\
                            margin: 0px;\
                            margin-top: 1ex;\
                            padding: 0px;\
                            font-size: 12pt;\
                            font-weight: bold;\
                        }\
                        QGroupBox::title {\
                           subcontrol-origin: margin;\
                           subcontrol-position: top left;\
                           padding: 0px;\
                           left: 20px;\
                        }\
                        QTableWidget::item:selected {\
                            color: white;\
                            background-color: green;\
                            border: 1px solid #567dbc;\
                        }\
                        QTableWidget::item:selected:active{\
                            color: white;\
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);\
                            background: navy;\
                        }\
                        QTableWidget::item:selected:!active {\
                            color: black;\
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #BECFD5, stop: 1 #D8ECF3);\
                        }\
                        QLineEdit{\
                            color: white;\
                            selection-background-color: navy;\
                        }\
                        Inspector {\
                        alternate-background-color: #ffffd0;\
                        }\
                        Inspector {\
                           show-decoration-selected: 1;\
                        }\
                        Inspector::item {\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-bottom-color: transparent;\
                        }\
                        Inspector::item:has-children {\
                           left: 18px;\
                           background-color: #FFDCA4;\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-right-color: transparent;\
                           border-bottom-color: transparent;\
                        }\
                        FieldInspector {\
                        alternate-background-color: #ffffd0;\
                        }\
                        Inspector {\
                           show-decoration-selected: 0;\
                        }\
                        FieldInspector::item {\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-bottom-color: transparent;\
                        }\
                        FieldInspector::item:has-children {\
                           left: 18px;\
                           background-color: #96F9BB;\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-right-color: transparent;\
                           border-bottom-color: transparent;\
                        }\
                        QTreeWidget::item:selected {\
                            border: 1px solid #567dbc;\
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #C824CC);\
                        }\
                        QTreeWidget::item:selected:active{\
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);\
                            background: navy;\
                        }\
                        QTreeWidget::item:selected:!active {\
                            color: black;\
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #BECFD5, stop: 1 #D8ECF3);\
                        }\
                        QTreeWidget::branch {\
                            color: black;\
                            background: white;\
                        }\
                        QComboBox {\
                            border: 1px solid gray;\
                            border-radius: 1px;\
                            padding: 1px 18px 1px 3px;\
                            min-width: 6em;\
                            color: white;\
                            background: navy;\
                        }\
                       QComboBox QAbstractItemView{\
                           background: gray;\
                       }\
                      '
                      )
    
#   QComboBox:!editable:on{\
#       background: navy;\
#   }\

    
#   QTreeWidget::item:hover {\
#      background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);\
#      border: 1px solid #bfcde4;\
#   }\
        
    
     #background-color: #fffff0;\
    #                           border-top-color: transparent;\
    #                           border-bottom-color: transparent;\
    
    mwin = MainWindow()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


