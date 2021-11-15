from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QMdiSubWindow
# from PySide2.QtUiTools import QUiLoader
from PyQt5 import uic
from PyQt5.QtCore import Qt

from lib.share import SI
from app_filter_sys_thread import Win_MAfilter
# from test_window import Win_Test
from app_excel_check import Win_excelCheck

# 啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊
class Win_Main:
    def __init__(self):
        # 读界面
        self.ui = uic.loadUi('ui/main_window.ui')
        # 退出
        self.ui.actionExit.triggered.connect(self.ui.close)
        # 独立窗口
        self.ui.actionPopUp.triggered.connect(self.onPopUpSubWin)
        # menu
        # self.ui.actionFilterAlertSys.triggered.connect(self.)

        # 树
        # 单击
        self.ui.opTree.itemClicked.connect(self.opTreeAction_MDI)
        # 双击
        self.ui.opTree.itemDoubleClicked.connect(self.opTreeAction_IndepWindow)

        # 操作树 界面表
        self.opTreeActionTable = {}
        # 载入树
        self.onTree()

    # 打开MDI子窗口
    def _openSubWin(self, FuncClass):
        def createSubWin():

            subWinFunc = FuncClass()
            subWin = QMdiSubWindow()

            # 将窗口存进MDI
            subWin.setWidget(subWinFunc.ui)
            subWin.setAttribute(Qt.WA_DeleteOnClose)
            self.ui.mdiArea.addSubWindow(subWin)
            # 存入表中，注意winFunc对象也要保存，不然对象没有引用，会销毁
            SI.subWinTable[str(FuncClass)] = {'subWin': subWin, 'subWinFunc': subWinFunc}
            subWin.show()
            # 子窗口提到最上层，并且最大化
            subWin.setWindowState(Qt.WindowActive | Qt.WindowMaximized)

        # 如果该功能类型 实例不存在
        if str(FuncClass) not in SI.subWinTable:
            # 创建实例
            createSubWin()
            return

        # 如果已经存在，直接show一下
        subWin = SI.subWinTable[str(FuncClass)]['subWin']
        try:
            subWin.show()
            # 子窗口提到最上层，并且最大化
            subWin.setWindowState(Qt.WindowActive | Qt.WindowMaximized)
        except:
            # show 异常原因肯定是用户手动关闭了该窗口，subWin对象已经不存在了
            createSubWin()

    def onPopUpSubWin(self):
        dic_convert_objname_class = {'MaFilterWin': Win_MAfilter,
                                     'testWin': Win_Test}
        try:
            act_window = self.ui.mdiArea.activeSubWindow()
            act_window_name = act_window.widget().objectName()
            print(act_window_name)
        except:
            return
        self.popupwindow = dic_convert_objname_class[act_window_name]().ui
        self.popupwindow.show()

    # 单击→MDI窗口
    def opTreeAction_MDI(self, item, column):
        # 点的哪个
        clickedText = item.text(column)
        # 点的是否有对应窗口，如果没有，则退出函数，不打开任何东西
        if clickedText not in self.opTreeActionTable:
            return

        # 否则，通过字典，获得所点击字符串所对应的窗口
        actionWinFunc = self.opTreeActionTable[clickedText]
        # 并在MDI中打开此窗口
        self._openSubWin(actionWinFunc)

    # 双击→独立窗口
    def opTreeAction_IndepWindow(self, item, column):
        """
        双击树打开独立窗口
        """
        # 点的哪个
        clickedText = item.text(column)

        # -------------------------
        # 1、判断点的节点是否定义了指向的窗口
        # 点的子节点是否有指向窗口（对应窗口在opTree中设置的），如果没有，则退出函数，不打开任何东西
        if clickedText not in self.opTreeActionTable:
            return
        # 否则，通过字典，获得所点击字符串所对应的窗口
        actionWinFunc = self.opTreeActionTable[clickedText]

        # -------------------------
        # 2、
        # 如果未被打开
        if str(actionWinFunc) not in SI.indeWinTable:
            # 创建一个独立窗口
            indeWinFunc = actionWinFunc()
            # 记录一下该窗口已打开
            SI.indeWinTable[str(actionWinFunc)] = {'indeWinFunc': indeWinFunc}
            # 保存成什么样子：
            # print(SI.indeWinTable)
            # {"<class 'filter_sys_thread.Win_MAfilter'>": {'indeWinFunc': <filter_sys_thread.Win_MAfilter object at 0x0000019D425A9490>}}
            # print(str(actionWinFunc))
            # <class 'filter_sys_thread.Win_MAfilter'>
        # 否则，直接打开
        # 在SI中添加此窗口信息
        indeWinFunc = SI.indeWinTable[str(actionWinFunc)]['indeWinFunc']
        try:
            # 显示
            indeWinFunc.ui.show()
            # bring the window to front
            indeWinFunc.ui.activateWindow()
        except:
            print('error: opTreeAction_IndepWindow()')

    # 设置树（树的内容、分级在此更改，每个分级对应什么窗口在此设置）
    def onTree(self):
        """
        逻辑：
        root里addChild(folderItem)是根节点；
        folderItem再addChild(leafItem)是子节点。

        :return:
        """
        # 可见
        self.ui.opTree.setVisible(True)
        # 先清空树节点
        self.ui.opTree.clear()

        # 下面要往root中添加根节点
        root = self.ui.opTree.invisibleRootItem()

        # ------------------------------
        # 此字典决定树目录内容（更改此处需同时更改此def最下面self.opTreeActionTable）
        dict_tree = {'后台': ['Excel核对'],
                     '测试': ['筛选预警系统']}
        # 创建第一级目录
        for key in dict_tree.keys():
            # 创建一个 目录节点
            folderItem = QTreeWidgetItem()
            # 设置该节点  “0”=第1个column 文本
            folderItem.setText(0, key)
            # 【添加】到树的不可见根节点下，就成为第一层节点
            root.addChild(folderItem)
            # 设置该节点为“展开”状态
            folderItem.setExpanded(True)

            # 创建第二集目录
            for item in dict_tree[key]:
                leafItem = QTreeWidgetItem()  # 叶子 节点
                leafItem.setText(0, item)  # 设置该节点  第1个column 文本
                folderItem.addChild(leafItem)  # 添加到目录节点中

        # 设置每个节点对应哪个窗口
        self.opTreeActionTable = {
            'Excel核对': Win_excelCheck,
            '筛选预警系统': Win_MAfilter,
        }


if __name__ == '__main__':
    # 报错时
    # https://blog.csdn.net/u011913417/article/details/106801203
    # dirname = os.path.dirname(PyQt5.__file__)
    # plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    # os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    app = QApplication([])
    SI.mainWin = Win_Main()
    SI.mainWin.ui.show()
    app.exec_()
