# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtCore import QIODevice, QFile
class ComplexDrag(QMainWindow):
    def __init__(self):
        super(ComplexDrag, self).__init__()
        self.setAcceptDrops(True)
        self.textEditor = None
        self.initUI()
    def initUI(self):
        self.textEditor = QTextEdit()
        self.setCentralWidget(self.textEditor)
        self.textEditor.setAcceptDrops(False)
        self.setAcceptDrops(True)
        self.setWindowTitle("拖拽")
    def dragEnterEvent(self, event):
        # if event.mimeData().hasFormat("application/vnd.ms-excel"):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    def dropEvent(self, event):
        # urls = event.mimeData().urls()
        lines = []
        for url in event.mimeData().urls():
            lines.append('dropped: %r' % url.toLocalFile())
        print(lines)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ComplexDrag()
    ex.show()
    app.exec_()
