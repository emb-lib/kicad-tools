#!/usr/bin/python3
# coding: utf-8


import sys
import os
import re
import shutil

sys.path.append(os.path.join( os.getcwd(), 'scmgr' ) )
                
from inspector import *
from selector  import *
from cmptable  import *
from utils     import *
from cmpmgr    import *

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QGroupBox, QAction, QComboBox,
                             QTextEdit, QVBoxLayout,QHBoxLayout, QGridLayout, QSplitter, QStyledItemDelegate,
                             QAbstractItemDelegate, 
                             QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
                             QAbstractItemView, QHeaderView, QMainWindow, QApplication, QCommonStyle,
                             QDialog, QFileDialog, QInputDialog, QMessageBox, QTabWidget, QDialogButtonBox)

from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent, QModelIndex, QItemSelectionModel
from PyQt5.QtCore import QT_VERSION_STR
                                        
#-------------------------------------------------------------------------------
class TSettingsDialog(QDialog):
    
    #-----------------------------------------------------------------
    class TCmpViewTable(QTableWidget):
        #---------------------------------------------------
        class EventFilter(QObject):
            def __init__(self, parent):
                super().__init__(parent)
                self.Parent = parent

            def eventFilter(self, obj, e):
                if e.type() == QEvent.KeyPress:
                    if e.key() == Qt.Key_Delete:
                        curr_row = self.Parent.currentRow()
                        self.Parent.removeRow(curr_row)
                        self.Parent.selectRow(curr_row)
                        return True
                
                return False        
        #-------------------------------------------------------------
        def __init__(self, parent, data_dict):
            super().__init__(0, 2, parent)
            
            self.installEventFilter(self.EventFilter(self))
        
            self.setSelectionBehavior(QAbstractItemView.SelectRows)  # select whole row
            self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
            self.horizontalHeader().setStretchLastSection(True)
            self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.verticalHeader().setDefaultSectionSize(20)
            self.setHorizontalHeaderLabels( ('Ref Base', 'Property Pattern') )
            
            keys = list( data_dict.keys() )
            keys.sort()    

            self.setRowCount(64)

            for idx, k in enumerate( keys ):
                RefBase = QTableWidgetItem(k)
                Pattern = QTableWidgetItem(data_dict[k])
                self.setItem(idx, 0, RefBase)
                self.setItem(idx, 1, Pattern)

            self.selectRow(0)
        #-------------------------------------------------------------
        def data_dict(self):
            res = {}
            for row in range(self.rowCount()):
                if self.item(row, 0):
                    res[self.item(row, 0).data(Qt.DisplayRole)] = self.item(row, 1).data(Qt.DisplayRole)
                    
            return res
            
    #-----------------------------------------------------------------        
    class TIgnoreCmpList(QListWidget):
        #---------------------------------------------------
        class EventFilter(QObject):
            def __init__(self, parent):
                super().__init__(parent)
                self.Parent = parent

            def eventFilter(self, obj, e):
                if e.type() == QEvent.KeyPress:
                    if e.key() == Qt.Key_Insert:
                        print('insert item')
                        self.Parent.add_item()
                        
                        return True

                    if e.key() == Qt.Key_Delete:
                        self.Parent.remove_item()
                        return True

                return False        
        #---------------------------------------------------
        def __init__(self, parent, data_list):
            super().__init__(parent)
            self.installEventFilter(self.EventFilter(self))
            
            data_list.sort()
            self.addItems( data_list )
            self.setAlternatingRowColors(True)
            for row in range(self.count()):
                item = self.item(row)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            
            #self.setEnabled(True)
            #self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        #---------------------------------------------------
        def add_item(self):
            text, ok = QInputDialog.getText(self, 'Add Component Reference', 'Enter Component Reference Pattern')
            if ok:
                self.addItem(text)
                print(self.count())
                
            print(self.data_list())
        #---------------------------------------------------
        def remove_item(self):
            curr_row = self.currentRow()
            self.takeItem(curr_row)
            
        #---------------------------------------------------
        def data_list(self):
            res = []
            for row in range(self.count()):
                res.append(self.item(row).data(Qt.DisplayRole))
                
            res.sort()
            return res
    #-----------------------------------------------------------------
    def __init__(self, parent):
        
        #---------------------------------------------------
        super().__init__(parent)
        self.Parent = parent
        #---------------------------------------------------
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        if Settings.contains('component-view'):
            CmpViewDict = Settings.value('component-view')
        else:
            CmpViewDict = { 'C' : '$Value, $Footprint', 
                            'D' : '$LibRef', 
                            'R' : '$Value, $Footprint' }
            
        if Settings.contains('component-ignore'):
            IgnoreCmpRefsList = Settings.value('component-ignore')
        else:
            IgnoreCmpRefsList = []

        #---------------------------------------------------
        self.CmpViewTable  = self.TCmpViewTable(self, CmpViewDict)
        self.IgnoreCmpList = self.TIgnoreCmpList(self, IgnoreCmpRefsList)
        #---------------------------------------------------
        self.Tabs = QTabWidget(self)
        self.Tabs.addTab(self.CmpViewTable, 'Component View')
        self.Tabs.addTab(self.IgnoreCmpList, 'Ignore Component List')
        #---------------------------------------------------
        self.ButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ButtonBox.accepted.connect(self.save_settings)
        self.ButtonBox.rejected.connect(self.cancel)
        #---------------------------------------------------
        self.Layout = QVBoxLayout(self)
        self.Layout.addWidget(self.Tabs)
        self.Layout.addWidget(self.ButtonBox)
        #---------------------------------------------------
        self.setWindowTitle('Settings')
        self.setModal(True)
    #-----------------------------------------------------------------    
    def save_settings(self):
        print('save settings')
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        Settings.setValue('component-view', self.CmpViewTable.data_dict())
        Settings.setValue('component-ignore', self.IgnoreCmpList.data_list())

        curr_file = CmpMgr.curr_file_path()
        self.Parent.CmpTable.reload_file(curr_file)
        
        self.close()
    #-----------------------------------------------------------------        
    def cancel(self):
        print('close settings dialog')
        self.close()
        
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

    #--------------------------------------------------------------------------------
    class EventFilter(QObject):
        def __init__(self, parent):
            super().__init__(parent)

        def eventFilter(self, obj, e):
            if e.type() == QEvent.KeyPress or e.type() == QEvent.ShortcutOverride:
                key = e.key()
                mod = e.modifiers()

                #print(obj.focusWidget().metaObject().className())

            return False
    #--------------------------------------------------------------------------------
    def scroll_left(self):
        print('alt-left')
        if self.ToolIndex == 3 or self.ToolIndex == 2:
            self.ToolList[self.ToolIndex].finish_edit()
            
        self.ToolIndex -= 1
        if self.ToolIndex < 0:
            self.ToolIndex = len(self.ToolList) - 1
            
        print('Tool Index: ' + str(self.ToolIndex))
        self.ToolList[self.ToolIndex].setFocus()
    #--------------------------------------------------------------------------------    
    def scroll_right(self):
        print('alt-right')
        if self.ToolIndex == 3 or self.ToolIndex == 2:
            self.ToolList[self.ToolIndex].finish_edit()
            
        self.ToolIndex += 1
        if self.ToolIndex == len(self.ToolList):
            self.ToolIndex = 0

        print('Tool Index: ' + str(self.ToolIndex))
        self.ToolList[self.ToolIndex].setFocus()
    #--------------------------------------------------------------------------------    
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
            self.ToolList[3].finish_edit()  # save field properties when leave field inspector
    #--------------------------------------------------------------------------------    
    def add_user_property(self):
        self.Inspector.save_cmps()
        self.FieldInspector.save_fields()
        
        self.Inspector.add_property()
    #--------------------------------------------------------------------------------
    def remove_user_property(self):
        self.Inspector.save_cmps()
        self.FieldInspector.save_fields()

        self.Inspector.remove_property()
    #--------------------------------------------------------------------------------        
    def rename_user_property(self):
        self.Inspector.save_cmps()
        self.FieldInspector.save_fields()
                    
        self.Inspector.rename_property()
    #--------------------------------------------------------------------------------    
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
        #   Application Hotkeys
        #
        self.shortcutLeft  = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Left), self)
        self.shortcutRight = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Right), self)
        self.shortcutLeft.setContext(Qt.ApplicationShortcut)
        self.shortcutRight.setContext(Qt.ApplicationShortcut)
        self.shortcutLeft.activated.connect(self.scroll_left)
        self.shortcutRight.activated.connect(self.scroll_right)
    #--------------------------------------------------------------------------------    
    def initUI(self):
        
        #----------------------------------------------------
        #
        #    Main Window
        #
        work_zone = QWidget(self)
        Layout    = QHBoxLayout(work_zone)
        self.setCentralWidget(work_zone)
        
        openAction = QAction(QIcon( os.path.join('scmgr', 'open24.png') ), 'Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open Schematic File')
        openAction.triggered.connect(self.open_file)
        
        saveAction = QAction(QIcon( os.path.join('scmgr', 'save24.png') ), 'Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save Schematic File')
        saveAction.triggered.connect(self.save_file)
                
        saveAsAction = QAction(QIcon( os.path.join('scmgr', 'save-as24.png') ), 'Save As...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.setStatusTip('Save Schematic File As...')
        saveAsAction.triggered.connect(self.save_file_as)
        
                        
        exitAction = QAction(QIcon( os.path.join('scmgr', 'exit24.png') ), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        
        settingsAction = QAction(QIcon( os.path.join('scmgr', 'settings24.png') ), 'Settings', self)
        settingsAction.setShortcut('Alt+S')
        settingsAction.setStatusTip('Edit settings')
        settingsAction.triggered.connect(self.edit_settings)
        
        self.statusBar().showMessage('Ready')

        #--------------------------------------------
        #
        #    Main Menu
        #
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(exitAction)

        #--------------------------------------------
        #
        #    Options Menu
        #
        optionsMenu = menubar.addMenu('&Options')
        optionsMenu.addAction(settingsAction)
        
        #--------------------------------------------
        #
        #    Toolbar
        #
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(openAction)        
        toolbar.addAction(saveAction)        
        toolbar.addAction(saveAsAction)        
        toolbar.addAction(exitAction)        
        toolbar.addAction(settingsAction)        
        
                
        self.CmpTabBox    = QGroupBox('Components', self)
        self.CmpTabLayout = QVBoxLayout(self.CmpTabBox)
        self.CmpTabLayout.setContentsMargins(4,10,4,4)
        self.CmpTabLayout.setSpacing(10)
        
        self.CmpTabLayout.setSizeConstraint(QVBoxLayout.SetMaximumSize)
        
        #----------------------------------------------------
        #
        #    Settings Dialog
        #
        
        #----------------------------------------------------
        #
        #    Components Table
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
        self.AddUserProperty    = QPushButton('Add Property', self)
        self.DeleteUserProperty = QPushButton('Delete Property', self)
        self.RenameUserProperty = QPushButton('Rename Property', self)
        
        self.InspectorBox    = QGroupBox('Inspector', self)
        self.InspectorSplit  = QSplitter(Qt.Vertical, self)
        self.InspectorLayout = QVBoxLayout(self.InspectorBox)
        self.InspectorLayout.setContentsMargins(4,10,4,4)
        self.InspectorLayout.setSpacing(2)
        
        
        self.InspectorSplit.addWidget(self.Inspector)
        self.InspectorSplit.addWidget(self.FieldInspector)
        self.InspectorLayout.addWidget(self.InspectorSplit)
        self.InspectorLayout.addWidget(self.AddUserProperty)
        self.InspectorLayout.addWidget(self.DeleteUserProperty)
        self.InspectorLayout.addWidget(self.RenameUserProperty)
                
        #----------------------------------------------------

        self.Splitter = QSplitter(self)
        self.Splitter.addWidget(self.CmpTabBox)
        self.Splitter.addWidget(self.Selector)   
        self.Splitter.addWidget(self.InspectorBox) 
                 
        self.centralWidget().layout().addWidget(self.Splitter)
        
        
        #----------------------------------------------------
        #
        #     Signals and Slots connections
        #
        self.CmpTable.cells_chosen.connect(self.Inspector.load_cmp)
        self.Inspector.load_field.connect(self.FieldInspector.load_field_slot)
        
        self.CmpTable.mouse_click.connect(self.mouse_change_tool)
        self.Inspector.mouse_click.connect(self.mouse_change_tool)
        self.FieldInspector.mouse_click.connect(self.mouse_change_tool)

        self.Inspector.header().sectionResized.connect(self.FieldInspector.column_resize)
        
        self.AddUserProperty.clicked.connect(self.add_user_property)
        self.DeleteUserProperty.clicked.connect(self.remove_user_property)
        self.RenameUserProperty.clicked.connect(self.rename_user_property)
        
        #----------------------------------------------------
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
        

    #---------------------------------------------------------------------------
    def open_file(self):
        #filename = QFileDialog.getOpenFileName(self, 'Open schematic file', '/opt/cad/kicad', 'KiCad Schematic Files (*.sch)')
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('KiCad Schematic Files (*.sch)')
        
        filenames = []
        if dialog.exec_():
            filenames = dialog.selectedFiles()
        
        CmpMgr.set_curr_file_path( filenames[0] )
        self.CmpTable.load_file( filenames[0] )
            
    #---------------------------------------------------------------------------
    def save_file(self):
        self.Inspector.save_cmps()
        self.FieldInspector.save_fields()
        
        curr_file = CmpMgr.curr_file_path()
        print('Save File "' + curr_file + '"')
        
        CmpMgr.save_file(curr_file)

    #---------------------------------------------------------------------------
    def save_file_as(self):
        self.Inspector.save_cmps()
        self.FieldInspector.save_fields()
        
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter('KiCad Schematic Files (*.sch)')

        filenames = []
        if dialog.exec_():
            filenames = dialog.selectedFiles()

            
        if len(filenames) == 0:
            return
            
        print('Save File As "' + filenames[0] + '"')
        CmpMgr.save_file(filenames[0])
        CmpMgr.set_curr_file_path( filenames[0] )
                                     
    #---------------------------------------------------------------------------
    def edit_settings(self):
        print('edit settings')
        SettingsDialog = TSettingsDialog(self)
        SettingsDialog.resize(400, 400)
        SettingsDialog.Tabs.setMinimumWidth(800)
        SettingsDialog.show()
        
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    print('Qt Version: ' + QT_VERSION_STR)
    
    app  = QApplication(sys.argv)
    
    with open( os.path.join('scmgr', 'scmgr.qss'), 'rb') as fqss:
        qss = fqss.read().decode()
        qss = re.sub(os.linesep, '', qss )
    app.setStyleSheet(qss)
    
    mwin = MainWindow()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


