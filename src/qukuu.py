#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 10:26:01 2020

@author: jimmy
"""
import sys
import os
import ctypes
try:
    from PyQt5.QtCore import (Qt, QSignalMapper, QFileInfo, QThread, pyqtSlot,
                              pyqtSignal, QModelIndex, QProcess, QMutex,
                              QEvent, QEventLoop)
    from PyQt5.QtGui import (QIcon, QKeySequence, QPixmap, QColor)
    from PyQt5.QtWidgets import (QMainWindow, QFileDialog,
                                 QMessageBox, QApplication, QAction, QMenu,
                                 QShortcut, qApp, QDialog, QProgressBar,
                                 QLabel, QHBoxLayout, QWidget)
    from PyQt5.uic import loadUi
except ImportError as err:
    print("pip install PyQt5")
    print("%s" % err)
    raise SystemExit
from LinuxKernel import LinuxKernel

try:
    is_admin = os.getuid() == 0
except AttributeError:
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

if not is_admin:
    print("Please run as root")
    sys.exit(0)


class QUKUU(QMainWindow):
    '''  QUKUU class    '''
    __VERSION = "20201224"

    def __init__(self):
        super(QUKUU, self).__init__()
        if getattr(sys, 'frozen', False):
            # we are running in a |PyInstaller| bundle
            self._basedir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            self._basedir = os.path.dirname(__file__)
        loadUi(os.path.join(self._basedir, 'qukuu.ui'), self)
        # UI
        self.pb_reflash.clicked.connect(self.reflash)
        # UI: statusbar
        hstatusLayout = QHBoxLayout()
        hstatusLayout.setContentsMargins(0, 0, 0, 0)
        self.info = QLabel()
        hstatusLayout.addWidget(self.info)
        hstatusLayout.addStretch()
        hstatusLayout.addStretch()
        self.porgress = QProgressBar()
        hstatusLayout.addWidget(self.porgress)
        statusWidget = QWidget()
        statusWidget.setLayout(hstatusLayout)
        self.statusbar.addPermanentWidget(statusWidget, 1)
        #
        self.lk = LinuxKernel()
        self.lk.sig_progress.connect(self.on_progress)
        self.lk.sig_finish.connect(self.on_finish)
        self.lk.sig_msg.connect(self.on_log)
        # self.lk.load_index()
        # # show kernel list to UI
        # self.kern_ds = self.lk.get_kernel_dict()

        # for key in self.kern_ds:
        #     self.cb_group.addItem("%s" % key)
        #     # print("%s: %s" % (key, ds[key]))
        # #TODO: on change cb_group index, load detail kernel list
        # # select last kernel
        self.cb_group.currentIndexChanged.connect(self.on_cb_group_changed)
        self.log("Ready")
        self.reflash(False)
        
    def update_status(self, msg):
        # self.statusbar.showMessage(msg)
        self.info.setText(msg)

    def on_cb_group_changed(self, idx):
        if self.lk:
            key = self.cb_group.itemText(idx)
            ds = self.lk.get_kernel_dict()
            values = ds.get(key)
            if values:
                #print("values:%s" % values)
                self.lw_kernels.clear()
                for value in values:
                    # remote tail /
                    value = value.replace("/", "")
                    self.lw_kernels.insertItem(0, value)
            
    @pyqtSlot(bool)
    def reflash(self, chk=True):
        '''reflash packages list'''
        if chk:
            self.pb_reflash.setEnabled(False)
        if self.lk:
            if chk:
                self.lk.download_index()
            self.lk.load_index()
            self.kern_ds = self.lk.get_kernel_dict()
            self.cb_group.currentIndexChanged.disconnect(self.on_cb_group_changed)
            self.cb_group.clear()
            for key in self.kern_ds:
                self.cb_group.addItem("%s" % key)
            self.cb_group.currentIndexChanged.connect(self.on_cb_group_changed)
            self.cb_group.setCurrentIndex(self.cb_group.count()-1)


    def install(self, pkg):
        '''install package'''
        self.debug("TODO: install package")

    def remove(self, pkg):
        '''remove package'''
        self.debug("TODO: remove package")

    def purge(self, pkg):
        '''purge package'''
        self.debug("TODO: purge package")

    def show_setting(self, pkg):
        '''show setting'''
        self.debug("TODO: setting")

    def show_about(self, pkg):
        '''show about'''
        self.debug("TODO: about")

    @pyqtSlot(int)
    def on_finish(self, iCode):
        self.log("finish")
        self.pb_reflash.setEnabled(True)
        self.pb_reflash.setChecked(False)

    @pyqtSlot(int, float)
    def on_progress(self, idx, percent):
        self.log("%s progress %s" % (idx, percent))
        self.porgress.setValue(int(percent))
    @pyqtSlot(str)
    def on_log(self, msg):
        print("%s" % msg)
        self.update_status(msg)

    def log(self, msg):
        self.update_status(msg)

    def debug(self, msg):
        print(msg)


if __name__ == '__main__':
    APP = QApplication(sys.argv)
    MAINWIN = QUKUU()
    MAINWIN.show()
    sys.exit(APP.exec_())
