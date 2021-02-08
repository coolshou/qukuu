#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
try:
    from tqdm import tqdm
except ImportError as e:
    print("pip install tqdm")
    print("%s" % e)
    raise SystemExit
import requests
try:
    from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot, QThread)
except ImportError as e:
    print("pip install PyQt5")
    print("%s" % e)
    raise SystemExit


class DownloadTask(QObject):
    ''' DownloadTask '''
    # QThread moust run in QApplication
    sig_progress = pyqtSignal(int ,float)  #thread id,  signal progress %
    sig_finish = pyqtSignal(int)  # finish code: 0: ok, other:error

    def __init__(self, url, target_path, target_filename=None, parent=None):
        super(DownloadTask, self).__init__()
        # create thread
        self.th = QThread()
        self._threadId = int(self.th.currentThreadId())
        print("self._threadId : %s" % self._threadId)
        # create download item
        self.dl = DownloadItem(url, target_path, target_filename, parent)
        self.dl.sig_progress.connect(self.on_progress)
        self.dl.sig_finish.connect(self.on_finish)
        self.dl.moveToThread(self.th)
        self.th.started.connect(self.dl.get)
        self.th.finished.connect(self.dl.deleteLater)

    @pyqtSlot(int)
    def on_finish(self, iCode):
        if self.th:
            print("kill thread")
            self.th.exit()
        self.sig_finish.emit(iCode)

    @pyqtSlot(float)
    def on_progress(self, percent):
        self.sig_progress.emit(self._threadId, percent)

    def start(self):
        if self.th:
            print("start download...")
            self.th.start()

    def is_running(self):
        if self.th:
            return self.th.isRunning()
        return False

class DownloadItem(QObject):
    '''class to hold download item, should be run in thread'''

    sig_progress = pyqtSignal(float)  # signal progress %
    sig_finish = pyqtSignal(int)  # finish code: 0: ok, other:error

    def __init__(self, url, target_path, target_filename=None, parent=None):
        super(DownloadItem, self).__init__()
        # http://kernel.ubuntu.com/~kernel-ppa/mainline/index.html
        # https://kernel.ubuntu.com/~kernel-ppa/mainline/index.html
        self.url = url
        self.target_path = target_path
        if not os.path.exists(self.target_path):
            os.mkdir(self.target_path)
        if target_filename:
            self.target_filename = target_filename
        else:
            self.target_filename = os.path.basename(self.url)

        if not self.target_filename:
            self.target_filename = "dlfile"

        self.target_file = os.path.join(self.target_path, self.target_filename)

    def get(self):
        '''this should run in thread'''
        # target_file = os.path.join(self.target_path, self.target_file)
        # url = "http://www.ovh.net/files/10Mb.dat" #big file test
        # Streaming, so we can iterate over the response.
        response = requests.get(self.url, stream=True)
        iPogress = 0
        enc = response.headers.get('content-encoding', "")
        print("enc: %s" % enc)
        total_size_in_bytes= int(response.headers.get('content-length', 0))
        block_size = 1024 #1 Kibibyte
        if not enc:
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(self.target_file, 'wb') as file:
            for data in response.iter_content(block_size):
                if not enc:
                    iPogress = len(data)/total_size_in_bytes
                    self.progress(iPogress)
                    progress_bar.update(len(data))
                file.write(data)
        if not enc: # content is encodeed!! gzip compress
            progress_bar.close()
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                print("ERROR, something went wrong (dl:%s, expect: %s)" % (progress_bar.n, total_size_in_bytes))
                self.sig_finish.emit(-1)
                return False
        self.sig_finish.emit(0)
        return True

    def progress(self, percent):
        self.sig_progress.emit(percent)
