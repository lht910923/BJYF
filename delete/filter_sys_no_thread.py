from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
# from PySide2.QtUiTools import QUiLoader
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor

from lib.share import SI, PandasModel

import pandas as pd
import requests
import datetime
import time
import os
from openpyxl import load_workbook


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
        # https://blog.csdn.net/dodo668/article/details/82382675
        # 商品期货 新浪API http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol=M0
        url = ('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFutures' + str_min_daily + 'KLine' + str_intvl + '?symbol=' + fut_code)

    elif fut_code in df_cff_code['代码'].values:
        fut_name = df_cff_code[df_cff_code['代码'] == fut_code]['简称'].item()
        # 股指期货 新浪API http://stock2.finance.sina.com.cn/futures/api/json.php/CffexFuturesService.getCffexFuturesMiniKLine5m?symbol=IF1306
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

        # 停止按钮
        self.ui.btn_stop.clicked.connect(self.onStopAlert)
        self.ui.btn_stop.setEnabled(False)

        # 保存结果按钮
        self.ui.btn_save.clicked.connect(self.onSave)
        self.ui.btn_save.setEnabled(False)

        # 调整字号按钮
        self.ui.btn_font_larger.clicked.connect(self.onFontLarger)
        self.ui.btn_font_smaller.clicked.connect(self.onFontSmaller)

        # - - - - - - - - - - - - - - -
        # 操作树 界面表 初始化
        self.opTreeActionTable = {}
        # 载入树
        self.onTree()
        # - - - - - - - - - - - - - - -

        # 结果的DF
        self.df_result = None

        # 记录tree中哪项被勾选
        self.dict_tree_checked = {}

        #
        self.len_progressbar = None
        self.progressbar_count = None

        # 字号，在此基础上加减
        self.fontSize = 9

        # 默认有品种被选中，
        # self.no_product_checked = False

    def onStartAlert(self):
        self.ui.btn_start.setEnabled(False)
        self.ui.btn_stop.setEnabled(True)
        self.ui.btn_save.setEnabled(False)

        self.onAlert()

        # 如果勾选了品种
        if not self.no_product_checked:
            spinbox_refresh_intvl = self.ui.spinBox_refreshIntvl.value()

            # - - - - - - - - - - - - - - - - - - - - - - - - -
            # make QTimer
            self.qTimer = QTimer()
            # set interval to 1 s
            self.qTimer.setInterval(spinbox_refresh_intvl*60*1000)  # 1000 ms = 1 s
            # connect timeout signal to signal handler
            self.qTimer.timeout.connect(self.onAlert)
            # start timer
            self.qTimer.start()

            # - - - - - - - - - - - - - - - - - - - - - - - - -
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
        checkbox_upThr = self.ui.checkBox_upThr.isChecked()  # boolean
        # 下穿功能
        checkbox_downThr = self.ui.checkBox_downThr.isChecked()  # boolean

        # 涨跌幅
        # spinbox_chgpct = self.ui.doubleSpinBox_ChgPct.value()

        # MA
        # spinbox_ma_short = self.ui.spinBox_ma_short.value()
        # spinbox_ma_long = self.ui.spinBox_ma_long.value()

        # 刷新间隔
        spinbox_refresh_intvl = self.ui.spinBox_refreshIntvl.value()
        self.count_down = spinbox_refresh_intvl * 60

        # 所有被选中的tree child
        self.dict_tree_checked = self._find_checked_tree()
        # {'股票': [], '期货': ['商品期货', '金融期货']}

        # 每次刷新需重置progress bar的长度和计数
        self.len_progressbar = 0
        self.progressbar_count = 1

        # progress bar的长度 = len(df_code_商品期货) + len(df_code_金融期货) + len(df_code_股票) + ...
        for fut_type in self.dict_tree_checked['期货']:
            df_code = pd.read_excel('期货品种列表.xlsx', sheet_name=fut_type)
            self.len_progressbar = self.len_progressbar + len(df_code)
        # for stock_type in self.dict_tree_checked['股票']
        #     df_code = tushare...
        #     self.len_progressbar = self.len_progressbar + len(df_code)
        # ------------------------------------------------------------

        self.ui.btn_stop.setEnabled(False)
        # 每次刷新，取消保存结果按钮上绿对勾icon
        self.ui.btn_save.setIcon(QIcon())

        # 每次刷新，重置df_result
        self.df_result = pd.DataFrame(columns=['证券代码', '证券简称', '触发事件', '最新价',
                                               '涨跌幅', 'MA短', 'MA长', 'K线', '触发时间'])

        # 如果树'期货'下品种勾选不为空
        if self.dict_tree_checked['期货']:

            # 如果勾选了'根据涨跌幅筛选'功能
            if checkbox_byChgPct:
                self._func_byChgPct_fut()
            # 如果勾选了'根据MA筛选'功能
            if checkbox_byMaMa:
                # 如果勾选了'上穿'功能
                if checkbox_upThr:
                    pass
                # 如果勾选了'下穿'功能
                if checkbox_downThr:
                    pass
                # 如果'上穿'、'下穿'都未勾选
                if not checkbox_upThr and not checkbox_downThr:
                    pass

        # # 如果树'股票'下品种勾选不为空
        if self.dict_tree_checked['股票']:
            print('w')
            # 如果勾选了'根据涨跌幅筛选'功能
            if checkbox_byChgPct:
                # self._func_byChgPct_Stock()
                pass
            if checkbox_byMaMa:
                # 如果勾选了'上穿'功能
                if checkbox_upThr:
                    pass
                # 如果勾选了'下穿'功能
                if checkbox_downThr:
                    pass
                # 如果'上穿'、'下穿'都未勾选
                if not checkbox_upThr and not checkbox_downThr:
                    pass

        # 没选择任何品种
        if not self.dict_tree_checked['股票'] and not self.dict_tree_checked['期货']:
            print('u')
            self.no_product_checked = True
            self.ui.btn_start.setEnabled(True)
            self.ui.btn_stop.setEnabled(False)
            self.ui.statusbar.showMessage('请选择品种')
            try:
                #
                self.onStopAlert()
            except:
                return
        else:

            # 显示到tableView
            model = PandasModel(self.df_result)
            self.ui.table_result.setModel(model)

            # 没选品种后运行，no_product_checked会变为True，这里设为False是为了onStartAlert()下if not self.no_product_checked:可通过
            self.no_product_checked = False
            # 保证'请选择品种'或'保存结果'后的文字被清空
            self.ui.statusbar.clearMessage()
            # 开始自动刷新以后，停止按钮可用
            self.ui.btn_stop.setEnabled(True)
            # 有结果后，保存按钮可用
            self.ui.btn_save.setEnabled(True)



    def _func_byChgPct_fut(self):

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
                    # so.progress_update.emit(self.progressbar_count)
                    self.ui.progressBar.setValue(self.progressbar_count)
                    # print('progressbar_count = {}'.format(self.progressbar_count))

                    if self.progressbar_count < self.len_progressbar:
                        self.progressbar_count += 1

    def _find_checked_tree(self):
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
        """
        生成树
        :return:
        """
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
        opTreeCheckedTable = {'商品期货': {'ItemEnabled': True}}
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
        if self.df_result is not None and len(self.df_result) != 0:
            # 保存结果
            date_today = time.strftime("%Y%m%d", time.localtime())
            time_currt = time.strftime("%H'%M'%S", time.localtime())

            # create new folder 新建文件夹
            newpath = r'保存结果/筛选系统/{}'.format(date_today)
            if not os.path.exists(newpath):
                os.makedirs(newpath)

            path = r'保存结果/筛选系统/{}/筛选结果{}.xlsx'.format(date_today, date_today)
            # 如果该excel存在，则打开，继续写入sheet，否则新建excel
            if os.path.isfile(path):
                book = load_workbook(path)
                writer = pd.ExcelWriter(path, engine='openpyxl')
                writer.book = book
            else:
                writer = pd.ExcelWriter(path)

            self.df_result.to_excel(writer, f'{time_currt}', index=False, startrow=0, startcol=0)
            writer.save()

            self.ui.statusbar.showMessage(f'保存成功："{path}" 中的 Sheet("{time_currt}")')
            self.ui.btn_save.setIcon(QIcon('../ui/icon/checkmark.png'))
        else:
            self.ui.statusbar.showMessage(f'无可保存结果')

    def onFontLarger(self):
        self.fontSize += 2
        self.ui.table_result.setFont(QFont('微软雅黑', self.fontSize))
        self.ui.table_result.resizeColumnsToContents()
        self.ui.table_result.resizeRowsToContents()

    def onFontSmaller(self):
        self.fontSize -= 2
        self.ui.table_result.setFont(QFont('微软雅黑', self.fontSize))
        self.ui.table_result.resizeColumnsToContents()
        self.ui.table_result.resizeRowsToContents()


if __name__ == '__main__':
    app = QApplication([])
    SI.mainWin = Win_MAfilter()
    SI.mainWin.ui.show()
    app.exec_()
    # dict_re = func_byChgPct_single('CU0', '5min', 0.02, False)
