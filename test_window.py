from PyQt5.QtWidgets import QApplication
# from PyQt5.QtUiTools import QUiLoader
from PyQt5 import uic
from lib.share import SI


class Win_Test:

    def __init__(self):
        # self.ui = QUiLoader().load('ui/ma_filter.ui')
        self.ui = uic.loadUi('ui/test_window.ui')


if __name__ == '__main__':
    app = QApplication([])
    SI.mainWin = Win_Test()
    SI.mainWin.ui.show()
    app.exec_()