# coding: utf-8


import sys
import os
import re
import shutil

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
    
    #-------------------------------------------------------------------------------    
    def __init__(self, parent):
        super().__init__(parent)

        self.setIndentation(16)
        self.setColumnCount(2)
        self.header().resizeSection(2, 10)
        #self.header().setSectionResizeMode(colNAME, QHeaderView.Interactive)
        self.setHeaderLabels( ('Parameter', 'Value' ) );
        
        self.model().setHeaderData(0, Qt.Horizontal, QColor('red'), Qt.BackgroundColorRole)
    

#-------------------------------------------------------------------------------

