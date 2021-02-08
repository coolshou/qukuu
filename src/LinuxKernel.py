#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import time
# import re
from bs4 import BeautifulSoup as BS
try:
    from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QObject,
                              QCoreApplication, QEventLoop)
    # from PyQt5.QtWidgets import (QWidget)
    # from PyQt5.QtGui import QIcon
    # from PyQt5.uic import loadUi
except ImportError as e:
    print("pip install PyQt5")
    print("%s" % e)
    raise SystemExit
from DownloadManager import DownloadTask

class LinuxKernel(QObject):
    # signal
    sig_msg = pyqtSignal(str)
    sig_error = pyqtSignal(str)
    #
    sig_progress = pyqtSignal(int ,float)  #thread id,  signal progress %
    sig_finish = pyqtSignal(int)  # finish code: 0: ok, other:error

    # vars
    name = ""
    version = ""
    version_main = ""
    version_extra = ""
    version_package = ""
    var_type = ""
    page_uri = ""

    version_maj = -1;
    version_min = -1;
    version_point = -1;
    #
    kern_dict = {}  # store kernel ver /path/files
    kern_rc_list = []
    #
    URI_KERNEL_UBUNTU_MAINLINE = "http://kernel.ubuntu.com/~kernel-ppa/mainline/"
    CACHE_DIR = "/var/cache/qukuu"
    NATIVE_ARCH = ""
    LINUX_DISTRO = ""
    RUNNING_KERNEL = ""
    KERNEL_TYPE = "generic"
    #KERNEL_TYPE = "lowlatency"
    CURRENT_USER = ""
    CURRENT_USER_HOME = ""

    # regx
    rex_header = None
    rex_header_all = None
    rex_image = None
    rex_image_extra = None
    rex_modules = None

    def __init__(self, parent=None):
        super(LinuxKernel, self).__init__(parent)
        self.dlmgr = {}  # hold download Manager
        self.wait = False
        self.LINUX_DISTRO = self.check_distribution()
        self.NATIVE_ARCH = self.check_package_architecture()
        self.RUNNING_KERNEL = self.check_running_kernel()
        self.initialize_regex()
        
        self.deb_list = {}

    def check_distribution(self):
        # dep on lsb_release
        rs = subprocess.check_output(["lsb_release","-sd"])
        return rs.decode()

    def check_package_architecture(self):
        uname = os.uname()
        if uname.machine in "x86_64":
            return "amd64"
        return uname.machine

    def check_running_kernel(self):
        uname = os.uname()
        return uname.release

    def initialize_regex(self):
        try:
            #//linux-headers-3.4.75-030475-generic_3.4.75-030475.201312201255_amd64.deb
            rex_header = "linux-headers-[a-zA-Z0-9.\-_]*generic_[a-zA-Z0-9.\-]*_%s.deb" % self.NATIVE_ARCH
            #//linux-headers-3.4.75-030475_3.4.75-030475.201312201255_all.deb
            rex_header_all = "linux-headers-[a-zA-Z0-9.\-_]*_all.deb"
            #//linux-image-3.4.75-030475-generic_3.4.75-030475.201312201255_amd64.deb
            rex_image = "linux-image-[a-zA-Z0-9.\-_]*generic_([a-zA-Z0-9.\-]*)_%s.deb" % self.NATIVE_ARCH
            #//linux-image-extra-3.4.75-030475-generic_3.4.75-030475.201312201255_amd64.deb
            rex_image_extra = "linux-image-extra-[a-zA-Z0-9.\-_]*generic_[a-zA-Z0-9.\-]*_%s.deb" % self.NATIVE_ARCH
            #//linux-image-extra-3.4.75-030475-generic_3.4.75-030475.201312201255_amd64.deb
            rex_modules = "linux-modules-[a-zA-Z0-9.\-_]*generic_[a-zA-Z0-9.\-]*_%s.deb" % self.NATIVE_ARCH
        except:
            pass

    def log_msg(self, msg):
        print("%s" % msg)
        self.sig_msg.emit(msg)

    def log_error(self, msg):
        print("ERROR: %s" % msg)
        self.sig_error.emit(msg)

    def check_if_initialized(self):
        ok = len(self.NATIVE_ARCH) > 0
        if (not ok):
            self.log_error("LinuxKernel: Class should be initialized before use!")
            return False
        return ok

    def index_page(self):
        return "%s/index.html" % (self.CACHE_DIR)

    def clean_cache(self):
        if (os.path.exists(self.CACHE_DIR)):
            for filename in os.listdir(self.CACHE_DIR):
                file_path = os.path.join(self.CACHE_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as err:
                    self.log_error('Failed to delete %s. Reason: %s' % (file_path, err))

    def download_index(self):
        self.check_if_initialized()
        #// fetch index.html --------------------------------------
        if not os.path.exists(self.CACHE_DIR):
            os.mkdir(self.CACHE_DIR)
        if (os.path.exists(self.index_page())):
            os.remove(self.index_page())

        # download index file
        # item = DownloadItem(self.URI_KERNEL_UBUNTU_MAINLINE,
        #                     self.CACHE_DIR, "index.html")
        mgr = DownloadTask(self.URI_KERNEL_UBUNTU_MAINLINE,
                           self.CACHE_DIR, "index.html")
        mgr.sig_progress.connect(self.on_progress)
        mgr.sig_finish.connect(self.on_finish)
        mgr.start()
        self.dlmgr[self.URI_KERNEL_UBUNTU_MAINLINE] = mgr
        # mgr.add_to_queue(item);
        # mgr.status_in_kb = true;
        # mgr.execute();

        # msg = _("Fetching index from kernel.ubuntu.com...")
        # log_msg(msg);
        # status_line = msg.strip();

        while (mgr.is_running()):
            QCoreApplication.processEvents(QEventLoop.AllEvents, 0.5)
            time.sleep(1)
            print(".")

    @pyqtSlot(int)
    def on_finish(self, iCode):
        self.sig_finish.emit(iCode)

    @pyqtSlot(int, float)
    def on_progress(self, idx, percent):
        self.sig_progress.emit(idx, percent)

    def load_index(self, file=None):
        # load index file
        if file:
            idx_file = file
        else:
            idx_file = self.index_page()
        if ( not os.path.exists(idx_file)):
            self.log_msg("index file not exist : %s" % idx_file)
            return
        # // parse index.html --------------------------
        soup = BS(open(self.index_page()), "html.parser")
        # print(soup.html)
        for link in soup.find_all('a'):
            url = link.get('href')
            if not url.startswith("v"):
                continue
            if "-rc" in url:
                self.kern_rc_list.append(url)
            else:
                ds = url.split(".")
                if len(ds)>=3:
                    key = ds[0]
                    # print("key: %s" % key)
                    try:
                        data = self.kern_dict.get(key)
                        if data is None:
                            self.kern_dict["%s" % key] = []
                        # print("key:%s = %s" % (key, data))
                    except KeyError:
                        self.kern_dict["%s" % key] = []
                    self.kern_dict["%s" % key].append(url)
                # print(url)

        # print(self.kern_dict)

    def get_kernel_dict(self):
        return self.kern_dict

    def download_kernels(self, selected_kernels):
        for kern in selected_kernels:
            self.download_packages(kern)
        return True
    
    def check_if_initialized(self):
        ok = len(self.NATIVE_ARCH) > 0
        if (not ok):
            self.log_error("LinuxKernel: Class should be initialized before use!")
            return False
        return ok
    
    def create_deb_list(self, kern):
        #self.deb_list[kern]["header"]
        #self.deb_list[kern]["header_all"]
        #self.deb_list[kern]["kernel"]
        #self.deb_list[kern]["module"]
        pass
        
    def download_packages(self, kern):
        ok = True
        self.check_if_initialized()
        # get deb files
        for file_name in deb_list.keys:
            file_path = "%s/%s/%s".printf(self.cache_subdir, self.NATIVE_ARCH, file_name)
            if (os.path.exists(file_path) and  not os.path.exists(file_path + ".aria2c")):
                continue
            os.mkdir(os.path.exists(file_path))
    
            stdout.printf("\n" + _("Downloading") + ": '%s'... \n".printf(file_name));
            stdout.flush();
            '''
            item = new DownloadItem(deb_list[file_name], file_parent(file_path), file_basename(file_path))
            mgr = new DownloadTask()
            mgr.add_to_queue(item)
            mgr.status_in_kb = True
            mgr.execute()
            while (mgr.is_running()):
        	time.sleep(1)
                stdout.printf("\r%-60s".printf(mgr.status_line.replace("\n","")))
        	stdout.flush()
	    if (file_exists(file_path)):
		stdout.printf("\r%-70s\n".printf(_("OK")))
		stdout.flush()
	    if (get_user_id_effective() == 0):
		chown(file_path, CURRENT_USER, CURRENT_USER)
		chmod(file_path, "a+rw")
	    else:
		stdout.printf("\r%-70s\n".printf(_("ERROR")))
		stdout.flush()
		ok = False
	    '''
        return ok