#!/usr/bin/python3
# coding: utf-8


import sys
import os
import re
import shutil

run_path, filename = os.path.split(  os.path.abspath(__file__) )
resources_path = os.path.join( run_path, 'scmgr' )
sys.path.append( resources_path )
                
from inspector import *
from selector  import *
from cmptable  import *
from utils     import *
from cmpmgr    import *

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication,
                             QGroupBox,  QVBoxLayout,QHBoxLayout, QSplitter, 
                             QTextBrowser, QTableWidget, QTableWidgetItem, 
                             QListWidget, QListWidgetItem,QAbstractItemView, QHeaderView, 
                             QAction, QDialog, QFileDialog, QInputDialog, 
                             QTabWidget, QPushButton, QDialogButtonBox)


from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent, QFont
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent, QModelIndex, QItemSelectionModel, QUrl
from PyQt5.QtCore import QT_VERSION_STR
        
VERSION = '0.1.0'
                                
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
        #---------------------------------------------------
        self.shortcutHelp  = QShortcut(QKeySequence(Qt.Key_F1), self)
        self.shortcutHelp.activated.connect(self.show_help)

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
    #---------------------------------------------------------------------------
    def show_help(self):
        help = THelpForm(self, 'Settings Dialog', 'settings.html')
#-------------------------------------------------------------------------------
class THelpForm(QWidget):
    
    def __init__(self, parent, title, path):
        #super().__init__(parent, Qt.WA_DeleteOnClose )
        super().__init__(parent, Qt.Window)
        
        self.text_browser   = QTextBrowser(self)
        #self.text_browser  = QWebEngineView(self)
        self.back_button    = QPushButton('Back', self)
        self.forward_button = QPushButton('Forward', self)
        self.close_button   = QPushButton('Close', self)
        
        self.layout = QVBoxLayout(self)
        self.btn_widget = QWidget(self)
        self.btn_layout = QHBoxLayout(self.btn_widget)
        self.btn_layout.addWidget(self.back_button)
        self.btn_layout.addWidget(self.forward_button)
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.close_button)
        
        self.shortcutEscape  = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.shortcutEscape.activated.connect(self.close)
        
        self.layout.addWidget(self.btn_widget)
        self.layout.addWidget(self.text_browser)
        
        self.back_button.clicked.connect(self.text_browser.backward)
        self.forward_button.clicked.connect(self.text_browser.forward)
        self.close_button.clicked.connect(self.close)
        
        
        self.text_browser.setSearchPaths([os.path.join(resources_path, 'doc')])
        self.text_browser.setSource(QUrl(path))
#       f = QFont()
#       f.setPointSize(14)
#       self.text_browser.setFont(f)
        
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')

        if Settings.contains('help-window'):
            self.restoreGeometry(Settings.value('help-window'))
            #pos_x, pos_y, width, height = Settings.value('help-window')
        else:
            pos_x, pos_y, width, height = 0, 0, 640, 640
            self.setGeometry(pos_x, pos_y, width, height)
        
        self.window().setWindowTitle(title)
        self.show()
    #--------------------------------------------------------------------------------
    def closeEvent(self, event):
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        Settings.setValue( 'help-window', self.saveGeometry() )
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


    PROGRAM_NAME = 'KiCad Schematic Component Manager'

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
        #self.Inspector.save_cmps()
        self.FieldInspector.save_fields()

        self.Inspector.remove_property()
    #--------------------------------------------------------------------------------        
    def rename_user_property(self):
        #self.Inspector.save_cmps()
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
        
        openAction = QAction(QIcon( os.path.join(resources_path, 'open24.png') ), 'Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open Schematic File')
        openAction.triggered.connect(self.open_file)
        
        saveAction = QAction(QIcon( os.path.join(resources_path, 'save24.png') ), 'Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save Schematic File')
        saveAction.triggered.connect(self.save_file)
                
        saveAsAction = QAction(QIcon( os.path.join(resources_path, 'save-as24.png') ), 'Save As...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.setStatusTip('Save Schematic File As...')
        saveAsAction.triggered.connect(self.save_file_as)
        
                        
        exitAction = QAction(QIcon( os.path.join(resources_path, 'exit24.png') ), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        
        settingsAction = QAction(QIcon( os.path.join(resources_path, 'settings24.png') ), 'Settings', self)
        settingsAction.setShortcut('Ctrl+Alt+S')
        settingsAction.setStatusTip('Edit settings')
        settingsAction.triggered.connect(self.edit_settings)
        
        helpAction = QAction(QIcon( os.path.join(resources_path, 'help_book24.png') ), 'User\'s Manual', self)
        helpAction.setShortcut('F1')
        helpAction.setStatusTip('User\'s Manual')
        helpAction.triggered.connect(self.show_user_manual_slot)
        
        helpSDAction = QAction(QIcon( os.path.join(resources_path, 'gear24.png') ), 'Settings Dialog', self)
        helpSDAction.setShortcut('Ctrl+F1')
        helpSDAction.setStatusTip('Settings Dialog Help')
        helpSDAction.triggered.connect(self.show_setting_dialog_help_slot)
                
        helpHKAction = QAction(QIcon( os.path.join(resources_path, 'rocket24.png') ), 'Hotkeys', self)
        helpHKAction.setShortcut('Shift+F1')
        helpHKAction.setStatusTip('Hotkeys Help')
        helpHKAction.triggered.connect(self.show_hotkeys_help_slot)

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
        #    Help Menu
        #
        helpMenu = menubar.addMenu('&Help')
        helpMenu.addAction(helpAction)
        helpMenu.addAction(helpSDAction)
        helpMenu.addAction(helpHKAction)
                
        #--------------------------------------------
        #
        #    Toolbar
        #
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)        
        toolbar.addAction(openAction)        
        toolbar.addAction(saveAction)        
        toolbar.addAction(saveAsAction)        
        toolbar.addAction(settingsAction)        
        toolbar.addAction(helpAction)        
        
        #----------------------------------------------------
        #
        #    Settings Dialog
        #
        
        #----------------------------------------------------
        #
        #    Components Table
        #
        self.CmpTabBox    = QGroupBox('Components', self)
        self.CmpTabLayout = QVBoxLayout(self.CmpTabBox)
        self.CmpTabLayout.setContentsMargins(4,10,4,4)
        self.CmpTabLayout.setSpacing(10)

        self.CmpTabLayout.setSizeConstraint(QVBoxLayout.SetMaximumSize)

        self.CmpTable       = ComponentsTable(self) 
        #self.CmpChooseButton = QPushButton('Choose', self)
        
        self.CmpTabLayout.addWidget(self.CmpTable)
        #self.CmpTabLayout.addWidget(self.CmpChooseButton)
        
                
        #----------------------------------------------------
        #
        #    Selector
        #
        self.SelectorBox    = QGroupBox('Selector', self)
        self.SelectorLayout = QVBoxLayout(self.SelectorBox)
        self.SelectorLayout.setContentsMargins(4,10,4,4)
        self.SelectorLayout.setSpacing(2)
        
        self.SelectorBtnWidget = QWidget(self)
        self.SelectorBtnLayout = QHBoxLayout(self.SelectorBtnWidget)
        self.SelectorBtnLayout.setContentsMargins(4,10,4,4)
        self.SelectorBtnLayout.setSpacing(10)

        self.Selector = Selector(self)

        self.SelApplyButton = QPushButton('Apply', self)
        self.SelApplyButton.setToolTip('Alt+S: Apply selection patterns to components')

        self.SelClearButton = QPushButton('Clear', self)
        self.SelClearButton.setToolTip('Alt+C: Clear selection patterns')

        self.SelTemplateButton = QPushButton('Use Component', self)
        self.SelTemplateButton.setToolTip('Alt+T: Use Selected Component As Template')


        self.SelectorLayout.addWidget(self.Selector)
        self.SelectorBtnLayout.addWidget(self.SelTemplateButton)
        self.SelectorBtnLayout.addWidget(self.SelApplyButton)
        self.SelectorBtnLayout.addWidget(self.SelClearButton)
        self.SelectorLayout.addWidget(self.SelectorBtnWidget)
        
        self.shortcutSelApply = QShortcut(QKeySequence(Qt.ALT + Qt.Key_S), self)
        self.shortcutSelApply.activated.connect(self.Selector.apply_slot)
        
        self.shortcutSelClear = QShortcut(QKeySequence(Qt.ALT + Qt.Key_C), self)
        self.shortcutSelClear.activated.connect(self.Selector.clear_slot)
                
        self.shortcutSelTemplate = QShortcut(QKeySequence(Qt.ALT + Qt.Key_T), self)
        self.shortcutSelTemplate.activated.connect(self.Selector.use_comp_as_template_slot)
        
        #----------------------------------------------------
        #
        #    Inspector
        #
        self.Inspector       = Inspector(self)
        self.FieldInspector  = FieldInspector(self)

        self.InspectorBtnWidget = QWidget(self)
        self.InspectorBtnLayout = QHBoxLayout(self.InspectorBtnWidget)
        self.InspectorBtnLayout.setContentsMargins(4,10,4,4)
        self.InspectorBtnLayout.setSpacing(10)
        

        self.AddUserProperty    = QPushButton('Add Property', self)
        self.AddUserProperty.setToolTip('Alt+A: Add new user property')
        self.DeleteUserProperty = QPushButton('Delete Property', self)
        self.DeleteUserProperty.setToolTip('Alt+Delete: Delete user property')
        self.RenameUserProperty = QPushButton('Rename Property', self)
        self.RenameUserProperty.setToolTip('Alt+R: Rename user property')
        
        self.InspectorBox    = QGroupBox('Inspector', self)
        self.InspectorSplit  = QSplitter(Qt.Vertical, self)
        self.InspectorLayout = QVBoxLayout(self.InspectorBox)
        self.InspectorLayout.setContentsMargins(4,10,4,4)
        self.InspectorLayout.setSpacing(2)
        
        
        self.InspectorSplit.addWidget(self.Inspector)
        self.InspectorSplit.addWidget(self.FieldInspector)
        self.InspectorLayout.addWidget(self.InspectorSplit)
        
        self.InspectorBtnLayout.addWidget(self.AddUserProperty)
        self.InspectorBtnLayout.addWidget(self.DeleteUserProperty)
        self.InspectorBtnLayout.addWidget(self.RenameUserProperty)
                
        self.InspectorLayout.addWidget(self.InspectorBtnWidget)

        self.shortcutSelApply = QShortcut(QKeySequence(Qt.ALT + Qt.Key_A), self)
        self.shortcutSelApply.activated.connect(self.add_user_property)
        
        self.shortcutSelApply = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Delete), self)
        self.shortcutSelApply.activated.connect(self.remove_user_property)
        
        self.shortcutSelApply = QShortcut(QKeySequence(Qt.ALT + Qt.Key_R), self)
        self.shortcutSelApply.activated.connect(self.rename_user_property)
        
        #----------------------------------------------------

        self.Splitter = QSplitter(self)
        self.Splitter.addWidget(self.CmpTabBox)
        self.Splitter.addWidget(self.SelectorBox)   
        self.Splitter.addWidget(self.InspectorBox) 
                 
        self.centralWidget().layout().addWidget(self.Splitter)
        
        
        #----------------------------------------------------
        #
        #     Signals and Slots connections
        #
        self.CmpTable.cells_chosen.connect(self.Inspector.load_cmp)
        self.CmpTable.cells_chosen.connect(self.Selector.comp_template_slot)
        self.CmpTable.file_load.connect(self.file_loaded_slot)
        self.CmpTable.cmps_updated.connect(self.Selector.process_comps_slot)
        self.CmpTable.cmps_selected.connect(self.set_status_text_slot)

        self.SelApplyButton.clicked.connect(self.Selector.apply_slot)
        self.SelClearButton.clicked.connect(self.Selector.clear_slot)
        self.SelTemplateButton.clicked.connect(self.Selector.use_comp_as_template_slot)
        
        self.Selector.select_comps_signal.connect(self.CmpTable.select_comps_slot)

        self.Inspector.load_field.connect(self.FieldInspector.load_field_slot)
        #self.Inspector.data_changed.connect(self.data_changed_slot)
        self.Inspector.update_comps.connect(self.data_changed_slot)
        #self.Inspector.data_changed.connect(self.CmpTable.update_cmp_list_slot)
        self.Inspector.update_comps.connect(self.CmpTable.update_cmp_list_slot)
        self.FieldInspector.data_changed.connect(self.data_changed_slot)
        CmpMgr.file_saved.connect(self.file_saved_slot)
        
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
        self.setWindowTitle(self.PROGRAM_NAME)
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
            
        if Settings.contains('selector'):
            w0, w1 = Settings.value('selector')
            self.Selector.setColumnWidth( 0, int(w0) )
            self.Selector.setColumnWidth( 1, int(w1) )
                        
        if Settings.contains('inspector'):
            w0, w1 = Settings.value('inspector')
            self.Inspector.setColumnWidth( 0, int(w0) )
            self.Inspector.setColumnWidth( 1, int(w1) )
            self.FieldInspector.setColumnWidth( 0, int(w0) )
            self.FieldInspector.setColumnWidth( 1, int(w1) )
            #self.Inspector.setColumnWidth( 2, int(w2) )
            
        if Settings.contains('splitter'):
            self.Splitter.restoreState( Settings.value('splitter') )
            
        if Settings.contains('inssplitter'):
            self.InspectorSplit.restoreState( Settings.value('inssplitter') )
            
        #----------------------------------------------------
        #
        #    Process command line arguments
        #
        if len(sys.argv) > 1:
            fname = sys.argv[1]
            if os.path.exists(fname):
                self.CmpTable.load_file(fname)
            else:
                print('E: input file "' + fname + '"does not exist')
            
        self.show()
    #---------------------------------------------------------------------------
    def closeEvent(self, event):
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        Settings.setValue( 'geometry', self.saveGeometry() )
        Settings.setValue( 'cmptable',  [self.CmpTable.columnWidth(0), self.CmpTable.columnWidth(1)] )
        Settings.setValue( 'selector',  [self.Selector.columnWidth(0), self.Selector.columnWidth(1)] )
        Settings.setValue( 'inspector', [self.Inspector.columnWidth(0), self.Inspector.columnWidth(1)] )
        Settings.setValue( 'splitter', self.Splitter.saveState() )
        Settings.setValue( 'inssplitter', self.InspectorSplit.saveState() )
        QWidget.closeEvent(self, event)
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
        self.FieldInspector.save_fields()
        self.Inspector.save_cmps()
        
        curr_file = CmpMgr.curr_file_path()
        message = 'Save File "' + curr_file + '"'
        print(message)
        self.statusBar().showMessage(message)
        
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
    def file_loaded_slot(self):
        text = CmpMgr.curr_file_path()
        self.set_title(text)
    #---------------------------------------------------------------------------
    def data_changed_slot(self):
        text = CmpMgr.curr_file_path() + ' *'
        self.set_title(text)
    #---------------------------------------------------------------------------
    def file_saved_slot(self):
        text = CmpMgr.curr_file_path()
        self.set_title(text)
    #---------------------------------------------------------------------------
    def set_title(self, text = ''):
        text = ' - ' + text if len(text) > 0 else ''
        self.setWindowTitle(self.PROGRAM_NAME + ' v' + VERSION + text)
    #---------------------------------------------------------------------------
    def set_status_text_slot(self, text):
        self.statusBar().showMessage(text)
    #---------------------------------------------------------------------------
    def edit_settings(self):
        print('edit settings')
        SettingsDialog = TSettingsDialog(self)
        SettingsDialog.resize(400, 400)
        SettingsDialog.Tabs.setMinimumWidth(800)
        SettingsDialog.show()
    #---------------------------------------------------------------------------
    def show_user_manual_slot(self):
        help = THelpForm(self, 'User\'s Manual', 'main.html')
    #---------------------------------------------------------------------------
    def show_setting_dialog_help_slot(self):
        help = THelpForm(self, 'Settings Dialog', 'settings.html')
    #---------------------------------------------------------------------------
    def show_hotkeys_help_slot(self):
        help = THelpForm(self, 'Hotkeys', 'hotkeys.html')
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    print('Qt Version: ' + QT_VERSION_STR)
    
    app  = QApplication(sys.argv)
    
    with open( os.path.join(resources_path, 'scmgr.qss'), 'rb') as fqss:
        qss = fqss.read().decode()
        qss = re.sub(os.linesep, '', qss )
    app.setStyleSheet(qss)
    
    mwin = MainWindow()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------


