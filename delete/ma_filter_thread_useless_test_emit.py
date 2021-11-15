from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QMessageBox
# from PySide2.QtUiTools import QUiLoader
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject

from lib.share import SI, PandasModel
import pandas as pd
import requests
import datetime
from threading import Thread


def func_byChgPct_single_fut(fut_code, k, chgpct_thrshd, time_check):
    """

    :param fut_code: str
    :param k: str
    :param chgpct_thrshd: float
    :param time_check: boolean
    :return: dict
    """
    # 商品期货代码(commodity future) 51个品种
    df_com_code = pd.read_excel('期货品种列表.xlsx', sheet_name='商品期货')

    # 中金所(cffex)期货代码 6个品种
    df_cff_code = pd.read_excel('期货品种列表.xlsx', sheet_name='金融期货')

    # --------------------------------------------------
    # 判断输入变量line_intvl的值，生成一系列变量用来确定url。
    list_k = ['5min', '15min', '30min', '60min', '日']
    str_min_daily = ''
    str_intvl = ''
    param_min = 0
    if k in list_k:
        if k == '日':
            str_min_daily = 'Daily'
            str_intvl = ''
            str_intvl_text = '日'
        else:
            str_min_daily = 'Mini'
            str_intvl = k[:-2]
            str_intvl_text = k[:-3] + '分钟'
            param_min = int(k[:-3])
    else:
        print(f'【错误】：几分钟线变量输入错误（{k}）。')

    # --------------------------------------------------
    # 查找str_code是属于哪个交易所的代码
    url = ''
    if fut_code in df_com_code['代码'].values:
        fut_name = df_com_code[df_com_code['代码'] == fut_code]['简称'].item()

        # 商品期货 新浪API http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol=M0
        url = ('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFutures' + str_min_daily + 'KLine' + str_intvl + '?symbol=' + fut_code)

    elif fut_code in df_cff_code['代码'].values:
        fut_name = df_cff_code[df_cff_code['代码'] == fut_code]['简称'].item()
        # 股指期货 新浪API http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine?symbol=M0
        url = ('http://stock2.finance.sina.com.cn/futures/api/json.php/CffexFuturesService.getCffexFutures' + str_min_daily + 'KLine' + str_intvl + '?symbol=' + fut_code)

    else:
        print(f'【错误】：未找到{fut_code}属于哪个交易所。')

    # --------------------------------------------------
    # 提数据
    raw = requests.get(url)
    # 转为json
    json = raw.json()
    # 转为DataFrame
    df_data = pd.DataFrame(json, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    # print(df_data.head())
    # print(len(df_data))  # tst

    # 如果提取的数据为空
    if len(df_data) == 0:
        return

    # --------------------------------------------------
    # 时间
    datetime_new = df_data['date'].iloc[0]

    # 筛除数据不是实时的品种
    # 判断逻辑：
    # 假如是5分钟(param_min)数据，且输入参数time_check为True，则判断数据最后时间与此刻时间之差，是否小于5min
    if time_check is True:
        if k == '日':
            datetime_obj = datetime.datetime.strptime(datetime_new, '%Y-%m-%d')
        else:
            datetime_obj = datetime.datetime.strptime(datetime_new, '%Y-%m-%d %H:%M:%S')
        datetime_now = datetime.datetime.now()

        # 取绝对值abs原因：系统时间为9:47时，新浪最新数据的时间有可能是9:45，也有可能是9:50
        time_diff = abs(datetime_now - datetime_obj)

        # 如果相差大于5min，则退出函数
        if k == '日':
            if time_diff.days > 2:
                # print('tst:数据非当天')
                return
        else:
            if time_diff.seconds > param_min * 60:
                # print('tst:数据非实时')
                return

    # 最新价
    price_new = float(df_data['close'].iloc[0])

    # 上个收盘价
    price_last = float(df_data['close'].iloc[1])
    # 涨跌幅（以百分数显示，保留2位小数）
    price_change = round((price_new / price_last) - 1, 4)

    # --------------------------------------------------
    # 【涨跌幅筛选】
    # 如果涨跌幅绝对值>输入的阈值，则print
    if abs(price_change) >= chgpct_thrshd/100:
        # print('【{}{}】 涨跌幅超{}%；涨跌幅：{:.2%}; 价格：{}; （{} K线，{}）'
        #       .format(fut_code, fut_name, chgpct_thrshd, price_change, price_new, str_intvl_text, datetime_new))
        return {'code': fut_code, 'name': fut_name, 'chgpct_thrshd': chgpct_thrshd,
                'chgpct': price_change, 'price': price_new, 'kline': str_intvl_text, 'time': datetime_new}


class Win_MAfilter:

    def __init__(self):

        # self.ui = QUiLoader().load('ui/ma_filter.ui')
        self.ui = uic.loadUi('ui/ma_filter.ui')

        self.ui.btn_start.clicked.connect(self.onStartAlert)
        self.ui.btn_stop.clicked.connect(self.onStopAlert)
        self.ui.btn_stop.setEnabled(False)
        self.ui.btn_save.clicked.connect(self.onSave)
        # - - - - - - - - - - - - - - -
        # 操作树 界面表
        self.opTreeActionTable = {}

        # 载入树
        self.onTree()
        # - - - - - - - - - - - - - - -

        # 保存结果的DF
        self.df_result = pd.DataFrame(columns=['证券代码', '证券简称', '触发事件', '最新价',
                                               '涨跌幅', 'MA短', 'MA长', 'K线', '触发时间'])

        self.dict_tree_checked = {}

        self.len_progressbar = 0
        self.progressbar_count = 1
        self.ongoing = False

        self.so = SignalStore()
        # 连接信号到处理的slot函数
        self.so.progress_update.connect(self.setProgress)

    def onStartAlert(self):
        self.ui.btn_start.setEnabled(False)
        self.ui.btn_stop.setEnabled(True)
        self.onAlert()

        spinbox_refresh_intvl = self.ui.spinBox_refreshIntvl.value()

        # make QTimer
        self.qTimer = QTimer()
        # set interval to 1 s
        self.qTimer.setInterval(spinbox_refresh_intvl*60*1000)  # 1000 ms = 1 s
        # connect timeout signal to signal handler
        self.qTimer.timeout.connect(self.onAlert)
        # start timer
        self.qTimer.start()

        self.qTimerLabel = QTimer()
        # set interval to 1 s
        self.qTimerLabel.setInterval(1*1000)  # 1000 ms = 1 s
        # connect timeout signal to signal handler
        self.qTimerLabel.timeout.connect(self.onCountDown)
        # start timer
        self.qTimerLabel.start()

    def onCountDown(self):
        self.count_down = self.count_down - 1
        self.ui.label_CountDown.setText(f'下次刷新：{self.count_down} 秒后')

    def onAlert(self):

        # 读取参数--------------------------------------------------
        # K线
        self.combobox_k_line = self.ui.comboBox_Kline.currentText()  # str

        # 筛除非实时数据
        self.checkbox_real_time_data = self.ui.checkBox_RealTimeData.isChecked()  # boolean

        # 根据涨跌幅筛选
        checkbox_byChgPct = self.ui.checkBox_byChangePct.isChecked()  # boolean

        # 根据均线筛选
        checkbox_byMaMa = self.ui.checkBox_byMaMa.isChecked()  # boolean

        # 上穿功能
        # checkbox_byMaMa = self.ui.checkBox_upThr.isChecked()  # boolean
        # 下穿功能
        # checkbox_byMaMa = self.ui.checkBox_downThr.isChecked()  # boolean

        # 涨跌幅
        # spinbox_chgpct = self.ui.doubleSpinBox_ChgPct.value()

        # MA
        # spinbox_ma_short = self.ui.spinBox_ma_short.value()
        # spinbox_ma_long = self.ui.spinBox_ma_long.value()

        # 刷新间隔
        spinbox_refresh_intvl = self.ui.spinBox_refreshIntvl.value()
        self.count_down = spinbox_refresh_intvl * 60

        # 所有被选中的tree child
        self.dict_tree_checked = self.find_checked()
        # {'股票': [], '期货': ['商品期货', '金融期货']}
        # ------------------------------------------------------------

        def thread_start_alert(checkbox_byChgPct, checkbox_byMaMa):
            self.ongoing = True
            self.len_progressbar = 0
            self.progressbar_count = 1

            self.ui.btn_stop.setEnabled(False)

            self.df_result = pd.DataFrame(columns=['证券代码', '证券简称', '触发事件', '最新价',
                                                   '涨跌幅', 'MA短', 'MA长', 'K线', '触发时间'])

            if checkbox_byChgPct:
                self.func_byChgPct()

            if checkbox_byMaMa:
                pass

            # 显示到tableView
            model = PandasModel(self.df_result)
            self.ui.table_result.setModel(model)

            self.ui.btn_stop.setEnabled(True)

            self.ongoing = False

        if self.ongoing:
            # QMessageBox.warning(self.ui, '警告', '任务进行中，请等待完成')
            return

        thread = Thread(target=thread_start_alert,
                        args=(checkbox_byChgPct, checkbox_byMaMa))
        thread.start()

    def func_byChgPct(self):
        for fut_type in self.dict_tree_checked['期货']:
            df_code = pd.read_excel('期货品种列表.xlsx', sheet_name=fut_type)
            self.len_progressbar = self.len_progressbar + len(df_code)
        # print('len_progressbar = {}'.format(self.len_progressbar))
        self.ui.progressBar.setRange(0, self.len_progressbar)

        # fut_type = '商品期货' 和 '金融期货'
        for fut_type in self.dict_tree_checked['期货']:
            # 如果商品期货被勾选，则分析商品期货。如果金融期货被勾选，则分析金融期货。
            if fut_type in self.dict_tree_checked['期货']:

                df_code = pd.read_excel('期货品种列表.xlsx', sheet_name=fut_type)

                spinbox_chgpct = self.ui.doubleSpinBox_ChgPct.value()

                for code in df_code['代码'].values:

                    dict_result = func_byChgPct_single_fut(code, self.combobox_k_line, spinbox_chgpct, self.checkbox_real_time_data)

                    if dict_result is not None:
                        self.df_result = self.df_result.append({'证券代码': dict_result['code'],
                                                                '证券简称': dict_result['name'],
                                                                '触发事件': f'涨跌幅超{dict_result["chgpct_thrshd"]}%',
                                                                '最新价': dict_result['price'],
                                                                '涨跌幅': '{:.2%}'.format(dict_result['chgpct']),
                                                                'K线': dict_result['kline'],
                                                                '触发时间': dict_result['time']
                                                                }, ignore_index=True)
                    self.so.progress_update.emit(self.progressbar_count)
                    # #self.ui.progressBar.setValue(self.progressbar_count)
                    # print('progressbar_count = {}'.format(self.progressbar_count))

                    if self.progressbar_count < self.len_progressbar:
                        self.progressbar_count += 1
    # 处理进度的slot函数
    def setProgress(self,value):
        self.ui.progressBar.setValue(value)

    def find_checked(self):
        """
        get list of all checked in QTreeWidget
        :return: dict
        """
        checked = dict()
        root = self.ui.opTree.invisibleRootItem()
        signal_count = root.childCount()

        for i in range(signal_count):
            signal = root.child(i)
            checked_sweeps = list()
            num_children = signal.childCount()

            for n in range(num_children):
                child = signal.child(n)

                if child.checkState(0) == Qt.Checked:
                    checked_sweeps.append(child.text(0))

            checked[signal.text(0)] = checked_sweeps

        # print(checked)
        # {'股票': [], '期货': ['商品期货', '国债期货', '股指期货']}
        return checked

    def onTree(self):
        self.ui.opTree.setVisible(True)
        # 先清空树节点
        self.ui.opTree.clear()

        root = self.ui.opTree.invisibleRootItem()

        # ------------------------------
        # 此字典决定树目录内容
        dict_tree = {'股票': ['全部A股', '我的自选'],
                     '期货': ['商品期货', '金融期货']
                     }
        # 此dict决定树默认勾选的项
        opTreeCheckedTable = {'商品期货': {'ItemEnabled': True},
                              '金融期货': {'ItemEnabled': True}}
        # 创建第一级目录
        for key in dict_tree.keys():
            # 创建一个 目录节点
            folderItem = QTreeWidgetItem()
            # 设置该节点  第1个column 文本
            folderItem.setText(0, key)
            # 添加到树的不可见根节点下，就成为第一层节点
            root.addChild(folderItem)
            # 设置该节点为展开状态
            folderItem.setExpanded(True)
            # folderItem.setCheckState(0, Qt.Checked)

            # 创建第二集目录
            for item in dict_tree[key]:
                child2 = QTreeWidgetItem()  # 叶子 节点
                child2.setText(0, item)  # 设置该节点  第1个column 文本
                folderItem.addChild(child2)  # 添加到目录节点中
                child2.setCheckState(0, Qt.Checked if item in opTreeCheckedTable else Qt.Unchecked)

    def onStopAlert(self):
        self.qTimer.stop()
        self.qTimerLabel.stop()
        self.ui.btn_start.setEnabled(True)
        self.ui.btn_stop.setEnabled(False)
        self.ui.label_CountDown.setText('已停止')

    def onSave(self):
        if self.df_result is not None:
            pass


# 信号库
class SignalStore(QObject):
    # 定义一种信号
    progress_update = pyqtSignal(int)
    # 还可以定义其他作用的信号


if __name__ == '__main__':
    app = QApplication([])
    SI.mainWin = Win_MAfilter()
    SI.mainWin.ui.show()
    app.exec_()
