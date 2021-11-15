from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QLabel
from lib.share import SI


class Label_draghere(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        #
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        # 限定文件类型（未解决：excel对应format）
        # if event.mimeData().hasFormat("text/uri-list"):
        if event.mimeData().hasUrls():
            # 接受
            event.acceptProposedAction()

    def dropEvent(self, event):
        lines = []
        for url in event.mimeData().urls():
            lines.append('dropped: %r' % url.toLocalFile())
        print(lines)


class Win_excelCheck:
    def __init__(self):
        # 读取界面
        self.ui = uic.loadUi('ui/excel_check_window.ui')
        self.ui.setAcceptDrops(True)
        self.ui.label_drag1.setText('aaa')
        self.ui.label_drag1 = Label_draghere(self.ui)


if __name__ == '__main__':
    app = QApplication([])
    SI.mainWin = Win_excelCheck()
    SI.mainWin.ui.show()
    app.exec_()