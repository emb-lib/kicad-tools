#!/usr/bin/python3
# coding: utf-8


import sys
import os
import re
import yaml
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction, QComboBox,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, QSplitter, QStyledItemDelegate,
                             QTableWidget, QTableWidgetItem, QCommonStyle, QTreeWidget, QTreeWidgetItem,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication)

from PyQt5.QtGui  import  QIcon, QBrush, QColor
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent

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
        self.setColumnCount(3)
        self.header().resizeSection(2, 10)
        self.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.header().setSectionResizeMode(2, QHeaderView.Fixed)
        #self.header().setStretchLastSection(False)
        self.setHeaderLabels( ('Property', 'Value', 'Edit') );
        self.std_items   = self.addParent(self, 0, 'Standard', 'slon')
        self.usr_items   = self.addParent(self, 0, 'User Defined', 'mamont')
        
        self.addChild(self.std_items, 'Ref',       '?')
        self.addChild(self.std_items, 'Lib Name',  '~')
        self.addChild(self.std_items, 'Value',     '~', Qt.ItemIsEditable)
        self.addChild(self.std_items, 'Footprint', '~', Qt.ItemIsEditable)
        self.addChild(self.std_items, 'Doc Sheet', '~', Qt.ItemIsEditable)
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
        item.setData(1, Qt.DisplayRole, data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | flags)
        
        if flags & Qt.ItemIsEditable:
            item.setCheckState (2, Qt.Checked)
        else:
            item.setCheckState (2, Qt.Unchecked)
        return item
            
    #---------------------------------------------------------------------------    
    def item_clicked(self, item, col):
        if item.checkState(2) == Qt.Checked:
            item.setFlags( item.flags() | Qt.ItemIsEditable)
        else:
            item.setFlags( item.flags() & (-Qt.ItemIsEditable - 1) )
        
        param = item.data(0, Qt.DisplayRole)
        comp = self.comps[0]
        if item.parent() == self.topLevelItem(0):
            self.load_field.emit([comp, param])
                
        if item.parent() == self.topLevelItem(1):
            print('user defined')
            
    #---------------------------------------------------------------------------    
    def item_changed(self, item, prev):
        self.item_clicked(item, 0)
                
    #---------------------------------------------------------------------------    
    def item_activated(self, item, col):
        self.editItem(item, 1)
            
    #---------------------------------------------------------------------------    
    def load_cmp(self, refs):
        
        self.comps = refs[0]
        comp = self.comps[0]
        
        print( (comp.__dict__) )
        #print(self.topLevelItem(0).childCount())
        
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)

            if item.data(0, Qt.DisplayRole) == 'Ref':
                item.setData(1, Qt.DisplayRole, comp.Ref)
                
            if item.data(0, Qt.DisplayRole) == 'Lib Name':
                item.setData(1, Qt.DisplayRole, comp.LibName)
                
            if item.data(0, Qt.DisplayRole) == 'Value':
                item.setData(1, Qt.DisplayRole, comp.Fields[1].Text)
                
            if item.data(0, Qt.DisplayRole) == 'Footprint':
                item.setData(1, Qt.EditRole, comp.Fields[2].Text)
                
            if item.data(0, Qt.DisplayRole) == 'Doc Sheet':
                item.setData(1, Qt.DisplayRole, comp.Fields[3].Text)
                
            if item.data(0, Qt.DisplayRole) == 'X':
                item.setData(1, Qt.DisplayRole, comp.PosX)
                                
            if item.data(0, Qt.DisplayRole) == 'Y':
                item.setData(1, Qt.DisplayRole, comp.PosY)
                
            if item.data(0, Qt.DisplayRole) == 'Timestamp':
                item.setData(1, Qt.DisplayRole, comp.Timestamp)
        
        self.topLevelItem(1).takeChildren()
                        
        for f in comp.Fields[4:]:
            print( f.InnerCode )
            self.addChild(self.usr_items, f.Name, f.Text, Qt.ItemIsEditable)
        
            
#-------------------------------------------------------------------------------    
class TComboBox(QComboBox):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        print('TComboBox')

    def keyPressEvent(self, e):
        print( e.key() )
        if e.key() == Qt.Key_Down or e.key() == Qt.Key_Up:
            print('Up/Down')
            print(type(self.parent()))
            QApplication.sendEvent( self.parent(), e ) 
            #self.parent().keyPressEvent(e)
            return
            
        QComboBox.keyPressEvent(self, e)

        #return e
        
#-------------------------------------------------------------------------------    
class FieldInspector(QTreeWidget):

    #---------------------------------------------------------------------------    
    class ItemDelegate(QStyledItemDelegate):

        def __init__(self, parent):
            super().__init__(parent)

        def createEditor(self, parent, option, idx):
            if idx.column() == 1:
                print( idx.column() )
                return QStyledItemDelegate.createEditor(self, parent, option, idx)

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
                print('Key Press')
                
                if e.key() == Qt.Key_Down or e.key() == Qt.Key_Up:
                    action = QAbstractItemView.MoveDown if e.key() == Qt.Key_Down else QAbstractItemView.MoveUp
                    print('Down') if e.key() == Qt.Key_Down else print('Up')
                    idx = obj.moveCursor(action, Qt.NoModifier)
                    item = obj.itemFromIndex(idx)
                    obj.setCurrentItem(item)
                    return True
                
                
#               if type(obj.itemWidget(obj.currentItem(), 1) ) is TComboBox:
#                   print('Combo')
#                   return True

            return False

    #-------------------------------------------------------------------------------    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.installEventFilter(self.EventFilter(self))
        
        self.setIndentation(16)
        self.setColumnCount(3)
        self.header().resizeSection(2, 10)
        self.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.header().setSectionResizeMode(2, QHeaderView.Fixed)
        self.setHeaderLabels( ('Field Name', 'Value', 'Edit') );
        self.setHeaderHidden(True)
        
        self.field_items = self.addParent(self, 0, 'Field Details', '')
    
        self.addChild(self.field_items, 'X',                  '')
        self.addChild(self.field_items, 'Y',                  '')
        self.addChild(self.field_items, 'Orientation',        '')
        self.addChild(self.field_items, 'Visible',            '')
        self.addChild(self.field_items, 'Horizontal Justify', '')
        self.addChild(self.field_items, 'Vertical Justify',   '')
        self.addChild(self.field_items, 'Font Size',          '')
        self.addChild(self.field_items, 'Font Bold',          '')
        self.addChild(self.field_items, 'Font Italic',        '')
    
        self.itemClicked.connect(self.item_clicked)
        self.currentItemChanged.connect(self.item_changed)
        self.itemActivated.connect(self.item_activated)
    
        self.setItemDelegate(self.ItemDelegate(self))
    
    #---------------------------------------------------------------------------    
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        #item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        item.setExpanded (True)
        item.setFlags(Qt.ItemIsEnabled)
        return item
    
    #---------------------------------------------------------------------------    
    def addChild(self, parent, title, data, flags=Qt.NoItemFlags):
        item = self.TreeWidgetItem(parent, [title])
        item.setData(1, Qt.DisplayRole, data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | flags)
    
        if flags & Qt.ItemIsEditable:
            item.setCheckState (2, Qt.Checked)
        else:
            item.setCheckState (2, Qt.Unchecked)
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
        if item.checkState(2) == Qt.Checked:
            item.setFlags( item.flags() | Qt.ItemIsEditable)
        else:
            item.setFlags( item.flags() & (-Qt.ItemIsEditable - 1) )
   
        if type(self.itemWidget(item, 1) ) is TComboBox:
            self.cb.setEnabled( item.checkState(2) == Qt.Checked )
            
       # self.view_field()
            
    #---------------------------------------------------------------------------    
    def item_changed(self, item, prev):
        
        print('Curr: ' + item.data(0, Qt.DisplayRole))
        if prev:
            print('Prev: ' + prev.data(0, Qt.DisplayRole))
            #self.closePersistentEditor(prev, 1)
        
        self.editItem(item, 1)
        self.handle_item(item)    
        self.setCurrentItem(item, 0)
    #    self.item_clicked(item, 0)
    
    #---------------------------------------------------------------------------    
    def item_activated(self, item, col):
        self.editItem(item, 1)
    
    #---------------------------------------------------------------------------    
    def load_field_slot(self, d):
        self.comp  = d[0]
        self.param = d[1]
        
        self.view_field()
        
    #---------------------------------------------------------------------------    
    def handle_item(self, item):
        if item.data(0, Qt.DisplayRole) == 'X':
            self.field.PosX = item.data(1, Qt.DisplayRole)
            print('X: ' + str(self.field.PosX))

        if item.data(0, Qt.DisplayRole) == 'Y':
            self.field.PosY = item.data(1, Qt.DisplayRole)
            print('Y: ' + str(self.field.PosY))

        if item.data(0, Qt.DisplayRole) == 'Orientation':
            self.cb.setEnabled( item.checkState(2) == Qt.Checked )
            print('Combo: ' + str(item.checkState(2)))
            self.field.Orientation = 'H' if self.cb.currentIndex() == 0 else 'V'
            if self.cb:
                print('Orient: ' + str(self.cb.currentIndex()) )

#       if item.data(0, Qt.DisplayRole) == 'Visible':
#           item.setData(1, Qt.DisplayRole, str(f.Visible) if f else '')
#
#       if item.data(0, Qt.DisplayRole) == 'HJustify':
#           item.setData(1, Qt.DisplayRole, f.HJustify if f else '')
#
#       if item.data(0, Qt.DisplayRole) == 'VJustify':
#           item.setData(1, Qt.DisplayRole, f.VJustify if f else '')
#
#       if item.data(0, Qt.DisplayRole) == 'Font Size':
#           item.setData(1, Qt.DisplayRole, f.FontSize if f else '')
#
#       if item.data(0, Qt.DisplayRole) == 'Font Bold':
#           item.setData(1, Qt.DisplayRole, f.FontBold if f else '')
#
#       if item.data(0, Qt.DisplayRole) == 'Font Italic':
#           item.setData(1, Qt.DisplayRole, f.FontItalic if f else '')
        
    #---------------------------------------------------------------------------    
    def view_field(self):
        
        comp  = self.comp
        param = self.param
        
        if param == 'Ref':
            f = self.comp.Fields[0]
        elif param == 'Value':
            f = self.comp.Fields[1]
        elif param == 'Footprint':
            f =  self.comp.Fields[2]
        elif param == 'Doc Sheet':
            f = self.comp.Fields[3]
        else:
            f = None
            
        self.field = f
            
        for i in range( self.topLevelItem(0).childCount() ):
            item = self.topLevelItem(0).child(i)
    
            if item.data(0, Qt.DisplayRole) == 'X':
                item.setData(1, Qt.DisplayRole, f.PosX if f else '')
    
            if item.data(0, Qt.DisplayRole) == 'Y':
                item.setData(1, Qt.DisplayRole, f.PosY if f else '')
    
            if item.data(0, Qt.DisplayRole) == 'Orientation':
    
                self.cb = TComboBox(self)
                if f:
                    self.cb.setEnabled( item.checkState(2) == Qt.Checked )
                    self.cb.addItems( ['Horizontal', 'Vertical'] )
                    self.cb.setCurrentIndex( 0 if f.Orientation == 'H' else 1 ) 
                    self.setItemWidget(item, 1, self.cb)
                else:
                    self.removeItemWidget(item, 1)
#               if self.cb:
#                   print(self.cb.currentIndex())
    
            if item.data(0, Qt.DisplayRole) == 'Visible':
                item.setData(1, Qt.DisplayRole, str(f.Visible) if f else '')
    
            if item.data(0, Qt.DisplayRole) == 'HJustify':
                item.setData(1, Qt.DisplayRole, f.HJustify if f else '')
    
            if item.data(0, Qt.DisplayRole) == 'VJustify':
                item.setData(1, Qt.DisplayRole, f.VJustify if f else '')
    
            if item.data(0, Qt.DisplayRole) == 'Font Size':
                item.setData(1, Qt.DisplayRole, f.FontSize if f else '')
    
            if item.data(0, Qt.DisplayRole) == 'Font Bold':
                item.setData(1, Qt.DisplayRole, f.FontBold if f else '')
    
            if item.data(0, Qt.DisplayRole) == 'Font Italic':
                item.setData(1, Qt.DisplayRole, f.FontItalic if f else '')
    
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
        self.Orientation = rec[2]
        self.PosX        = rec[3]
        self.PosY        = rec[4]
        self.FontSize    = rec[5]
        self.Visible     = True if int(rec[6]) == 0 else False
        self.HJustify    = rec[7]
        self.VJustify    = rec[8]
        self.FontItalic  = rec[9]
        self.FontBold    = rec[10]
    
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
                           show-decoration-selected: 1;\
                        }\
                        FieldInspector::item {\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-bottom-color: transparent;\
                        }\
                        FieldInspector::item:has-children {\
                           left: 18px;\
                           background-color: #21E96C;\
                           border: 1px solid #d9d9d9;\
                           border-top-color: #d9d9d9;\
                           border-left-color: transparent;\
                           border-right-color: transparent;\
                           border-bottom-color: transparent;\
                        }\
                        QTreeWidget::item:selected {\
                            border: 1px solid #567dbc;\
                        }\
                        QTreeWidget::item:selected:active{\
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);\
                        }\
                        QTreeWidget::item:selected:!active {\
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);\
                        }\
                        QTreeWidget::item:hover {\
                           background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);\
                           border: 1px solid #bfcde4;\
                        }\
                        QComboBox {\
                            border: 1px solid gray;\
                            border-radius: 1px;\
                            padding: 1px 18px 1px 3px;\
                            min-width: 6em;\
                        }\
                      '
                      )
    
    
        
    
     #background-color: #fffff0;\
    #                           border-top-color: transparent;\
    #                           border-bottom-color: transparent;\
    
    mwin = MainWindow()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


