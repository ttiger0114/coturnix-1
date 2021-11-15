import sys
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import random
import datetime
import time
import threading
import numpy as np
import copy
from tqdm import tqdm
import LoopBackSocket as lb

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 1230, 1260)
        self.setWindowTitle("Coturnix")

        self.range = None
        self.target = None
        self.account = None
        self.available = 0
        self.amount = None
        self.profit_rate = 0.75

        self.previous_day_hold = False
        self.previous_day_quantity = False

        
        table_width = 1100
        table_height = 1000
        self.tableWidget = QTableWidget(self)
        self.tableWidget.move(10, 40)
        self.tableWidget.resize(table_width, table_height)
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setRowCount(30)
        column_headers = ['종목코드', '종목명', '시가','고가','저가','현재가','거래량']
        self.tableWidget.setHorizontalHeaderLabels(column_headers)

        style = "::section {""background-color: lightgray; }"
        self.tableWidget.horizontalHeader().setStyleSheet(style)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)


        self.tableWidget.doubleClicked.connect(self.table_double_clicked)

        sys_text_height = 300
        sys_text_width = 300
        self.sys_text_edit = QPlainTextEdit(self)
        self.sys_text_edit.setReadOnly(True)
        self.sys_text_edit.move(table_width+20, 10)
        self.sys_text_edit.resize(sys_text_width, sys_text_height)


        plain_text_height = 600
        plain_text_width = 300
        self.plain_text_edit = QPlainTextEdit(self)
        self.plain_text_edit.setReadOnly(True)
        self.plain_text_edit.move(table_width+20, sys_text_height+20)
        self.plain_text_edit.resize(plain_text_width, plain_text_height)

        self.account_text = QLineEdit(self)
        self.account_text.setReadOnly(True)
        self.account_text.move(10, 10)
        self.account_text.resize(210, 24)

        self.account_money_text = QLineEdit(self)
        self.account_money_text.setReadOnly(True)
        self.account_money_text.move(300, 10)
        self.account_money_text.resize(230, 24)
        
        self.setFixedSize(table_width+plain_text_width+30, plain_text_height+sys_text_height+40)

        
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr_data)
        self.ocx.OnReceiveRealData.connect(self._handler_real_data)
        self.ocx.OnReceiveChejanData.connect(self._handler_chejan_data)

        #####################
        self.ocx.OnReceiveConditionVer.connect(self.receiveConditionVer)
        self.ocx.OnReceiveTrCondition.connect(self.receiveTrCondition)
        self.ocx.OnReceiveRealCondition.connect(self.receiveRealCondition)
        ##################

        
        self.condition = {}
        self.codeList = []
        self.codeNum = 0

        ### DICTIONNARY
        self.DataDict = {}
        self.FirstReceiveFlag = {}
        self.InitialData = {}
        self.VolumeReference = {}
        self.TradingInfo = {}

        ####################
        ####### Socket #####
        self.client = lb.ClientSocket()


        self.view_num = 10

        self.login_event_loop = QEventLoop()
        self.CommConnect()          # 로그인이 될 때까지 대기
        self.run()

    def table_double_clicked(self):
        row = self.tableWidget.currentIndex().row()
        column = self.tableWidget.currentIndex().column()
        code = self.tableWidget.item(row,0).text()
        # self.tableWidget.setItem(row_num,0,QTableWidgetItem(f"{code}"))
        print(self.DataDict[code])
        # print(self.tableWidget.item(row,0).text())



    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec()


    def ConditionMethod(self):
        self.getConditionLoad()
        # condition_num = int(input("조건문 번호: ")) 
        condition_num = 0
        self.sendCondition("0156",self.condition[condition_num],condition_num,1)

        #### 조건문 결과 출력
        try:
            check_code_exist = kiwoom.codeList[0]
            codeList = kiwoom.codeList
        except:
            pass

    def run(self):
        
        ClientWaiting = threading.Thread(target = self.ClientWaiting)
        ClientWaiting.start()

        # self.client.SendData(np.array([1,2,3,4]))

        accounts = self.GetLoginInfo("ACCNO")
        self.account = accounts.split(';')[0]
        self.account_text.setText(f" 계좌번호: {self.account}")

        self.ConditionMethod()  

        self.DisConnectRealData('1')
        self.DisConnectRealData('2')
        
        # 사전 초기화
        self.InitializeDataDict(self.codeList)
        for code in self.codeList:
            self.InitializeVolumeReference(code)

        # self.SetRealReg('2', str(self.codeList[-1]), "20", 0)
        # TR 요청 

        for i,code in enumerate(tqdm(self.codeList[0:self.view_num])):
            time.sleep(0.3)
            self.request_opt10001(code)
            self.subscribe_stock_conclusion('2', code)        

        # for i in range(20):
        #     temp_color = random.randrange(1,100)
        #     self.tableWidget.item(i,1).setBackground(QColor(255,255-temp_color,255-temp_color))
        
        self.request_opw00001()
        THREAD_OPW00001 = self.AutoOPW00001(self)
        THREAD_OPW00001.start()
        # THREAD_OPW00001 = threading.Thread(target = self.AutoOPW00001) #예수금 자동조회
        self.request_opw00004()

        ## 주식 사전 기록
        AutoUpdate = threading.Thread(target = self.AutoUpdateDataDict)
        AutoUpdate.start()

        # 주식체결 (실시간)
        self.subscribe_market_time('1')
    
    class AutoOPW00001(QThread):
        def __init__(self, window, parent = None):
            super().__init__(parent)
        def run(self):
            while(True):
                time.sleep(10)
                window.request_opw00001()

    # def AutoOPW00001(self):
    #     while(True):
    #         time.sleep(10)
    #         print(autoaccount)
    #         self.request_opw00001()


    def GetLoginInfo(self, tag):
        data = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return data

    def _handler_login(self, err_code):
        if err_code == 0:
            self.sys_text_edit.appendPlainText("[LOGIN SUCCESS]")
        self.login_event_loop.exit()

    def _handler_tr_data(self, screen_no, rqname, trcode, record, next):
        if rqname == "주식기본정보":
            code = self.GetCommData(trcode, rqname, 0, "종목코드")
            name = self.GetCommData(trcode, rqname, 0, "종목명")
            start_price = self.GetCommData(trcode, rqname, 0, "시가")
            high_price = self.GetCommData(trcode, rqname, 0, "고가")
            low_price = self.GetCommData(trcode, rqname, 0, "저가")
            cur_price = self.GetCommData(trcode, rqname, 0, "현재가")
            amount = self.GetCommData(trcode, rqname, 0, "거래량")

            if code != '':
                row_num = self.codeList.index(code)

                self.tableWidget.setItem(row_num,0,QTableWidgetItem(f"{code}"))
                self.tableWidget.setItem(row_num,1,QTableWidgetItem(f"{name}"))
                self.tableWidget.setItem(row_num,2,QTableWidgetItem(f"{abs(int(start_price))}"))
                self.tableWidget.setItem(row_num,3,QTableWidgetItem(f"{abs(int(high_price))}"))
                self.tableWidget.setItem(row_num,4,QTableWidgetItem(f"{abs(int(low_price))}"))
                self.tableWidget.setItem(row_num,5,QTableWidgetItem(f"{abs(int(cur_price))}"))
                self.tableWidget.setItem(row_num,6,QTableWidgetItem(f"{amount}"))

                
                if int(start_price) > 0:
                    self.tableWidget.item(row_num,2).setForeground(QBrush(Qt.red))
                elif int(start_price) < 0:
                    self.tableWidget.item(row_num,2).setForeground(QBrush(Qt.blue))
                if int(high_price) > 0:
                    self.tableWidget.item(row_num,3).setForeground(QBrush(Qt.red))
                elif int(high_price) < 0:
                    self.tableWidget.item(row_num,3).setForeground(QBrush(Qt.blue))
                if int(low_price) > 0:
                    self.tableWidget.item(row_num,4).setForeground(QBrush(Qt.red))
                elif int(low_price) < 0:
                    self.tableWidget.item(row_num,4).setForeground(QBrush(Qt.blue))
                if int(cur_price) > 0:
                    self.tableWidget.item(row_num,5).setForeground(QBrush(Qt.red))
                elif int(cur_price) < 0:
                    self.tableWidget.item(row_num,5).setForeground(QBrush(Qt.blue))
                
                self.tableWidget.item(row_num,5).setBackground(QColor(235,255,255))

        elif rqname == "분봉데이터":
            code = self.GetCommData(trcode, rqname, 0, "종목코드")
            amount = []
            trade_time = []
            # rows = self.GetRepeatCnt(trcode, rqname)
            for i in range(6,35,7):
                amount.append(self.GetCommData(trcode, rqname, i, "거래량"))
                trade_time.append(self.GetCommData(trcode, rqname, i, "체결시간"))

            if code != '':
                df = pd.DataFrame({'col1':trade_time, 'col2':amount})
                path = "volume_data/{}.csv".format(code)
                # df.to_excel(path, mode = 'w', index = False) 
                df.to_csv(path, index = False) 

        elif rqname == "예수금조회":
            available = self.GetCommData(trcode, rqname, 0, "주문가능금액")
            available = int(available)
            self.available = available
            self.account_money_text.setText(f" 주문가능금액: {available}")

        elif rqname == "계좌평가현황":
            rows = self.GetRepeatCnt(trcode, rqname)
            for i in range(rows):
                종목코드 = self.GetCommData(trcode, rqname, i, "종목코드")
                보유수량 = self.GetCommData(trcode, rqname, i, "보유수량")

                if 종목코드[1:] == "229200":
                    self.previous_day_hold = True
                    self.previous_day_quantity = int(보유수량)

    def GetRepeatCnt(self, trcode, rqname):
        ret = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def request_opt10081(self, code):
        now = datetime.datetime.now()
        today = now.strftime("%Y%m%d")
        self.SetInputValue("종목코드",code)
        self.SetInputValue("기준일자", today)
        self.SetInputValue("수정주가구분", 1)
        self.CommRqData("일봉데이터", "opt10081", 0, "9000")

    def request_opt10080(self, code):
        now = datetime.datetime.now()
        today = now.strftime("%Y%m%d")
        self.SetInputValue("종목코드",code)
        self.SetInputValue("틱범위",60)
        # self.SetInputValue("기준일자", today)
        self.SetInputValue("수정주가구분", 1)
        self.CommRqData("분봉데이터", "opt10080", 0, "9003")

    def request_opt10001(self, code):
        self.SetInputValue("종목코드",code)
        self.CommRqData("주식기본정보", "opt10001", 0, "9001")


    def request_opw00001(self):
        self.SetInputValue("계좌번호", self.account)
        self.SetInputValue("비밀번호", "")
        self.SetInputValue("비밀번호입력매체구분", "00")
        self.SetInputValue("조회구분", 2)
        self.CommRqData("예수금조회", "opw00001", 0, "9002")

    def request_opw00004(self):
        self.SetInputValue("계좌번호", self.account)
        self.SetInputValue("비밀번호", "")
        self.SetInputValue("상장폐지조회구분", 0)
        self.SetInputValue("비밀번호입력매체구분", "00")
        self.CommRqData("계좌평가현황", "opw00004", 0, "9003")

    # 실시간 타입을 위한 메소드
    def SetRealReg(self, screen_no, code_list, fid_list, real_type):
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                              screen_no, code_list, fid_list, real_type)

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid) 
        return data

    def DisConnectRealData(self, screen_no):
        self.ocx.dynamicCall("DisConnectRealData(QString)", screen_no)

    ## 조건 검색    
    def receiveConditionVer(self, receive, msg):
        """
        getConditionLoad() 메서드의 조건식 목록 요청에 대한 응답 이벤트
        :param receive: int - 응답결과(1: 성공, 나머지 실패)
        :param msg: string - 메세지
        """
        # print("[receiveConditionVer]")
        self.sys_text_edit.appendPlainText("[ReceiveConditionVer]")
        try:
            if not receive:
                return
                
            self.condition = self.getConditionNameList()

            self.sys_text_edit.appendPlainText(f"[조건문 개수: {len(self.condition)}]")
            # print("Condition Number: ", len(self.condition))

            for key in self.condition.keys():
                # print("Condition: ", key, ": ", self.condition[key])
                self.sys_text_edit.appendPlainText(f"[검색 조건문: {self.condition[key]}]")
                # print("key type: ", type(key))

        except Exception as e:
            print(e)

        finally:
            self.conditionLoop.exit()

    def receiveTrCondition(self, screenNo, codes, conditionName, conditionIndex, inquiry):
        """
        (1회성, 실시간) 종목 조건검색 요청시 발생되는 이벤트
        :param screenNo: string
        :param codes: string - 종목코드 목록(각 종목은 세미콜론으로 구분됨)
        :param conditionName: string - 조건식 이름
        :param conditionIndex: int - 조건식 인덱스
        :param inquiry: int - 조회구분(0: 남은데이터 없음, 2: 남은데이터 있음)
        """

        # print("[receiveTrCondition], ")
        
        self.sys_text_edit.appendPlainText("[ReceiveTrCondition]")
        try:
            if codes == "":
                return

            codeList = codes.split(';')
            del codeList[-1]
            ### KOSDAQ Check ######################
            kosdaq_codeList = []
            kosdaq = self.ocx.GetCodeListByMarket('10')
            kosdaq = kosdaq.split(';')
            for code in codeList:
                if code in kosdaq:
                    kosdaq_codeList.append(code)
            #######################################
            self.codeList = kosdaq_codeList
            self.sys_text_edit.appendPlainText(f"[종목개수: {len(kosdaq_codeList)}]")
            
           
        finally:
            self.conditionLoop.exit()


    def receiveRealCondition(self, code, event, conditionName, conditionIndex):
        print("[receiveRealCondition]")
        """
        실시간 종목 조건검색 요청시 발생되는 이벤트
        :param code: string - 종목코드
        :param event: string - 이벤트종류("I": 종목편입, "D": 종목이탈)
        :param conditionName: string - 조건식 이름
        :param conditionIndex: string - 조건식 인덱스(여기서만 인덱스가 string 타입으로 전달됨)
        """

        # print("종목코드: {}, 종목명: {}".format(code, self.get_master_code_name(code)))
        
        # print("이벤트: ", "종목편입" if event == "I" else "종목이탈")
        
        # bot.sendMessage(chat_id=chat_id, text="종목코드: {} , {}".format(code, event))

    def getConditionLoad(self):
        self.sys_text_edit.appendPlainText("[GetConditionLoad]")
        """ 조건식 목록 요청 메서드 """

        isLoad = self.ocx.dynamicCall("GetConditionLoad()")
        # 요청 실패시
        if not isLoad:
            self.sys_text_edit.appendPlainText("[GetConditionLoad(): 조건식 요청 실패]")
        # receiveConditionVer() 이벤트 메서드에서 루프 종료
        self.conditionLoop = QEventLoop()
        self.conditionLoop.exec_()

    def getConditionNameList(self):
        self.sys_text_edit.appendPlainText("[GetConditionNameList]")
        """
        조건식 획득 메서드
        조건식을 딕셔너리 형태로 반환합니다.
        이 메서드는 반드시 receiveConditionVer() 이벤트 메서드안에서 사용해야 합니다.
        :return: dict - {인덱스:조건명, 인덱스:조건명, ...}
        """

        data = self.ocx.dynamicCall("GetConditionNameList()")

        if data == "":
            print("GetConditionNameList(): 사용자 조건식이 없습니다.")

        conditionList = data.split(';')
        del conditionList[-1]

        conditionDictionary = {}

        for condition in conditionList:
            key, value = condition.split('^')
            conditionDictionary[int(key)] = value

        return conditionDictionary

    def sendCondition(self, screenNo, conditionName, conditionIndex, isRealTime):
        self.sys_text_edit.appendPlainText("[SendCondition]")
        """
        종목 조건검색 요청 메서드
        이 메서드로 얻고자 하는 것은 해당 조건에 맞는 종목코드이다.
        해당 종목에 대한 상세정보는 setRealReg() 메서드로 요청할 수 있다.
        요청이 실패하는 경우는, 해당 조건식이 없거나, 조건명과 인덱스가 맞지 않거나, 조회 횟수를 초과하는 경우 발생한다.
        조건검색에 대한 결과는
        1회성 조회의 경우, receiveTrCondition() 이벤트로 결과값이 전달되며
        실시간 조회의 경우, receiveTrCondition()과 receiveRealCondition() 이벤트로 결과값이 전달된다.
        :param screenNo: string
        :param conditionName: string - 조건식 이름
        :param conditionIndex: int - 조건식 인덱스
        :param isRealTime: int - 조건검색 조회구분(0: 1회성 조회, 1: 실시간 조회)
        """


        isRequest = self.ocx.dynamicCall("SendCondition(QString, QString, int, int",
                                     screenNo, conditionName, conditionIndex, isRealTime)

        if not isRequest:
            print("sendCondition(): 조건검색 요청 실패")

        # receiveTrCondition() 이벤트 메서드에서 루프 종료
        self.conditionLoop = QEventLoop()
        self.conditionLoop.exec_()

    def sendConditionStop(self, screenNo, conditionName, conditionIndex):

        print("[SendConditionStop]")
        """ 종목 조건검색 중지 메서드 """

        self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", screenNo, conditionName, conditionIndex)


    ####################################
    # 실시간 이벤트 처리 핸들러 
    def _handler_real_data(self, code, real_type, real_data):
        if real_type == "장시작시간":
            장운영구분 = self.GetCommRealData(code, 215)
            if 장운영구분 == '3':
                if self.previous_day_hold:
                    self.previous_day_hold = False
                    # 매도 (시장가)
                    self.SendOrder("매도", "8001", self.account, 2, "229200", self.previous_day_quantity, 0, "03", "")
            elif 장운영구분 == '4':
                QCoreApplication.instance().quit()
                print("메인 윈도우 종료")

        elif real_type == "주식체결": 
            a0 = self.GetCommRealData(code,10) #현재가
            #a1 = self.GetCommRealData(code,11) #전일대비
            #a2 = self.GetCommRealData(code,12) #등락율
            #a3 = self.GetCommRealData(code,27) #매도호가
            #a4 = self.GetCommRealData(code,28) #매수호가
            a5 = self.GetCommRealData(code,13) #누적거래량
            #a6 = self.GetCommRealData(code,14) #누적거래대금
            a7 = self.GetCommRealData(code,16) #시가
            a8 = self.GetCommRealData(code,17) #고가
            a9 = self.GetCommRealData(code,18) #저가
            a10 = self.GetCommRealData(code,228) #체결강도

            ## 시가, 고가, 저가, 현재가, 누적거래량
            stock_realtime_data = [a7, a8, a9, a0, a5]
            abs_stock_realtime_data = stock_realtime_data
            for i in range(len(stock_realtime_data)):
                abs_stock_realtime_data[i] = abs(int(stock_realtime_data[i]))
            # print("abs_stock_realtime_data",code,abs_stock_realtime_data, stock_realtime_data)

            self.UpdateDataDict(code,abs_stock_realtime_data)
            row_num = self.codeList.index(code)

            ## 주식 매도
            if self.TradingInfo[code][1] > 0:  ## 매수한 주식 존재시
                current_price = abs_stock_realtime_data[3]
                target_price = float(self.TradingInfo[code][0])*(1 + self.profit_rate/100)
                low_price = float(self.TradingInfo[code][0])*(1 - self.profit_rate/100)
                quantity = self.TradingInfo[code][1]

                # print(f"target{target_price}, current{current_price}, low{low_price}, quan{quantity}")
                if current_price >= target_price or current_price <= low_price: # 조건 충족시 시장가 매도
                    self.SendOrder("매도", "8001", self.account, 2, code , quantity, 0, "03", "")


            ###############

            if row_num >= self.view_num:
                return

            self.tableWidget.setItem(row_num,2,QTableWidgetItem(f"{abs(int(a7))}"))
            self.tableWidget.setItem(row_num,3,QTableWidgetItem(f"{abs(int(a8))}"))
            self.tableWidget.setItem(row_num,4,QTableWidgetItem(f"{abs(int(a9))}"))
            self.tableWidget.setItem(row_num,5,QTableWidgetItem(f"{abs(int(a0))}"))
            self.tableWidget.setItem(row_num,6,QTableWidgetItem(f"{abs(int(a5))}"))


            if int(a7) > 0:
                self.tableWidget.item(row_num,2).setForeground(QBrush(Qt.red))
            elif int(a7) < 0:
                self.tableWidget.item(row_num,2).setForeground(QBrush(Qt.blue))
            if int(a8) > 0:
                self.tableWidget.item(row_num,3).setForeground(QBrush(Qt.red))
            elif int(a8) < 0:
                self.tableWidget.item(row_num,3).setForeground(QBrush(Qt.blue))
            if int(a9) > 0:
                self.tableWidget.item(row_num,4).setForeground(QBrush(Qt.red))
            elif int(a9) < 0:
                self.tableWidget.item(row_num,4).setForeground(QBrush(Qt.blue))
            if int(a0) > 0:
                self.tableWidget.item(row_num,5).setForeground(QBrush(Qt.red))
            elif int(a0) < 0:
                self.tableWidget.item(row_num,5).setForeground(QBrush(Qt.blue))

            self.tableWidget.item(row_num,5).setBackground(QColor(235,255,255))

            # # 현재가 
            # 현재가 = self.GetCommRealData(code, 10)
            # 현재가 = abs(int(현재가))          # +100, -100
            # 체결시간 = self.GetCommRealData(code, 20)

            # # 목표가 계산
            # # TR 요청을 통한 전일 range가 계산되었고 아직 당일 목표가가 계산되지 않았다면 
            # if self.range is not None and self.target is None:
            #     시가 = self.GetCommRealData(code, 16)
            #     시가 = abs(int(시가))          # +100, -100
            #     self.target = int(시가 + (self.range * 0.5))      
            #     self.plain_text_edit.appendPlainText(f"목표가 계산됨: {self.target}")

            # # 매수시도
            # # 당일 매수하지 않았고
            # # TR 요청과 Real을 통한 목표가가 설정되었고 
            # # TR 요청을 통해 잔고조회가 되었고 
            # # 현재가가 목표가가 이상이면
            # if self.hold is None and self.target is not None and self.amount is not None and 현재가 > self.target:
            #     self.hold = True 
            #     quantity = int(self.amount / 현재가)
                # self.SendOrder("매수", "8000", self.account, 1, "229200", quantity, 0, "03", "")
                # self.plain_text_edit.appendPlainText(f"시장가 매수 진행 수량: {quantity}")

            # # 로깅
            # self.plain_text_edit.appendPlainText(f"시간: {체결시간} 목표가: {self.target} 현재가: {현재가} 보유여부: {self.hold}")

    
    def DisConnectRealData(self, screen_no):
        self.ocx.dynamicCall("DisConnectRealData(QString)", screen_no)
        print("구독 해지 완료")

    def _handler_chejan_data(self, gubun, item_cnt, fid_list):
        if gubun == '0':  # 주식 매수 체결 완료
            trading_state = self.GetChejanData('913') ## 주문 상태
            trading_sort = self.GetChejanData('906') ## 매매 구분
            code =  self.GetChejanData('9001')
            code = code[1:7]
            name =  self.GetChejanData('302')
            trading_number = self.GetChejanData('911') # 체결 수량
            trading_price = self.GetChejanData('901') # 주문 가격

            ## 거래 정보 갱신
            if trading_state == '체결':
                self.TradingInfo[code][0] = trading_price
                now = datetime.datetime.now()
                current_time = now.strftime("%H:%M:%S")
                self.plain_text_edit.appendPlainText(f"[{current_time}] {name} {code} {trading_state} {trading_price} {trading_number}")
                # self.TradingInfo[code][1] = self.TradingInfo[code][1] + int(trading_number)
                print(f"[{current_time}] {name} {code}{trading_state} {trading_sort} {trading_price} {trading_number}")

        elif gubun == '1':      # 잔고통보
            code =  self.GetChejanData('9001')
            code = code[1:7]
            name =  self.GetChejanData('302')
            have_stock = self.GetChejanData('930') # 보유 수량
            self.TradingInfo[code][1] = int(have_stock)
            print("보유수량",have_stock)



    def subscribe_stock_conclusion(self, screen_no, code):
        self.SetRealReg(screen_no, str(code), "20", 1)
        self.sys_text_edit.appendPlainText(f"[{code} 주식체결 구독신청]")

    def subscribe_market_time(self, screen_no):
        self.SetRealReg(screen_no, "", "215", 0)
        self.sys_text_edit.appendPlainText("[장시작시간 구독신청]")

    # TR 요청을 위한 메소드
    def SetInputValue(self, id, value):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def CommRqData(self, rqname, trcode, next, screen_no):
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", 
                              rqname, trcode, next, screen_no)

    def GetCommData(self, trcode, rqname, index, item):
        data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                     trcode, rqname, index, item)
        return data.strip()

    def SendOrder(self, rqname, screen, accno, order_type, code, quantity, price, hoga, order_no):
        self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                             [rqname, screen, accno, order_type, code, quantity, price, hoga, order_no])

    def GetChejanData(self, fid):
        data = self.ocx.dynamicCall("GetChejanData(int)", fid)
        return data

    ############ Stock data dictionary #######
    def InitializeDataDict(self, codeList):
        for code in codeList:
            temp = [0,0,0,0,0]
            self.DataDict[code] = [temp]
            self.FirstReceiveFlag[code] = 0
            self.TradingInfo[code] = [0,0] # price, amount

    def AutoUpdateDataDict(self):
        while(True):
            time.sleep(60 - datetime.datetime.now().second)
            # time.sleep(2)

            Stacked_code = []
            Stacked_Stockdata = []

            for key, _ in self.DataDict.items():
                # print("[Autoupdate]",datetime.datetime.now(), key)
                data_len = len(self.DataDict[key])
                
                ### Preprocessed Data before sending ########
                # self.SendData(key,self.DataDict[key][data_len-1])
                len_limit = 7
                if data_len >= len_limit:
                    origin_data = np.array(self.DataDict[key][data_len-len_limit:data_len]).astype(float)
                    preprocessed_data = np.array(self.DataDict[key][data_len-len_limit+1:data_len]).astype(float)

                    ### Make volume amount to volume difference
                    for i in range(len_limit-1):
                        preprocessed_data[i,4] = origin_data[i+1,4] - origin_data[i,4]

                    # preprocessed_data[0:len_limit-1,0:4] = ((preprocessed_data[0:len_limit-1,0:4]/self.InitialData[key][0])-1)*100
                    # preprocessed_data[0:len_limit-1,4] = (preprocessed_data[0:len_limit-1,4]/self.VolumeReference[key])*0.1

                    # self.SendData(key,preprocessed_data)
                    Stacked_code.append(key)
                    Stacked_Stockdata.append(preprocessed_data)
                ######################################################

                ## Auto Update #########################
                if self.DataDict[key][data_len-1] != [0,0,0,0,0]:
                    data = copy.deepcopy(self.DataDict[key][data_len-1])
                    current_price = data[3]

                    ##이전 종가를 현재 시가로 자동업데이트
                    data[0] = current_price
                    data[1] = current_price
                    data[2] = current_price
                    self.DataDict[key] = self.DataDict[key] + [data]
                ################################

            ### Send Packet to AI model ########
            if Stacked_code != []:
                # self.SendData(Stacked_code, np.array(Stacked_Stockdata))
                self.client.SendData([Stacked_code, np.array(Stacked_Stockdata)])


            
    def UpdateDataDict(self, code, data):
        try:
            ## Recorde Initial Data ####
            if self.FirstReceiveFlag[code] == 0:
                self.InitialData[code] = data
                self.FirstReceiveFlag[code] = 1
            #############################
            
            data_len = len(self.DataDict[code])
            previous_data = self.DataDict[code][data_len-1]
            current_price = data[3]

            if data_len == 1:
                new_data = [0,0,0,0,0]
                new_data[0] = data[0]

                if previous_data[1] < current_price:
                    new_data[1] = current_price
                else:
                    new_data[1] = previous_data[1]

                if previous_data[2] > current_price:
                    new_data[2] = current_price
                else:
                    new_data[2] = previous_data[2]

                new_data[3] = data[3]   ## 현재가는 그대로
                new_data[4] = data[4]   ## 거래량도 그대로

                self.DataDict[code][data_len-1] = new_data
                # print(self.DataDict[code][data_len-1])

            elif data_len > 1:
                new_data = [0,0,0,0,0]
                new_data[0] = self.DataDict[code][data_len-2][3]  # 시가는 이전에 종가
                if previous_data[1] < current_price:
                    new_data[1] = current_price
                else:
                    new_data[1] = previous_data[1]

                if previous_data[2] > current_price:
                    new_data[2] = current_price
                else:
                    new_data[2] = previous_data[2]

                new_data[3] = data[3]   ## 현재가는 그대로
                new_data[4] = data[4]   ## 거래량도 그대로

                self.DataDict[code][data_len-1] = new_data
            
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M:%S")
            self.sys_text_edit.appendPlainText(f"[{current_time}] Update {code}")
        except:
            print("except")
            pass

    def InitializeVolumeReference(self, code):
        datapath = f"volume_data/{code}.csv"
        data = pd.read_csv(datapath)
        volume = data['col2'].sum()/300
        self.VolumeReference[code] = volume

    #### Auto Sell ##########################
    def AutoSell(self, waitingtime, code, quantity, price):
        time.sleep(waitingtime) ## 판매대기 후 매수 물량 매도
        if self.TradingInfo[code][1] >= quantity:
            self.SendOrder("매도", "8001", self.account, 2, code , quantity, 0, "03", "")
            print("AutoSell Ouccr")
        elif self.TradingInfo[code][1] > 0:
            self.SendOrder("매도", "8001", self.account, 2, code , self.TradingInfo[code][1], 0, "03", "")

        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self.plain_text_edit.appendPlainText(f"[{current_time}] Time Expired {code} {price} {quantity} ")
        print(f"[{current_time}] Time Expired {code} {price} {quantity} ")


    #############################################
    ### Send Packet to AI model ########
    def ClientWaiting(self):
        while(True):
            received_data = self.client.Waiting()
            if received_data[0] == 'buy':
                codelist = received_data[1]
                code_num = len(codelist)
                available = self.available/code_num/10

                for i, code in enumerate(codelist):
                    time.sleep(0.3)
                    ## 주문 요청
                    data_len = len(self.DataDict[code])
                    price = self.DataDict[code][data_len-2][3] 
                    quantity = int(available / price /10 )
                    if quantity >= 1 and self.TradingInfo[code][1] == 0:
                        self.SendOrder("매수", "8000", self.account, 1, code , quantity, price, "00", "") ## 지정가매수
                        # AutoSell(360, code, quantity, price)
                        self.AutoSell(10, code, quantity, price)
                        # now = datetime.datetime.now()
                        # current_time = now.strftime("%H:%M:%S")
                        # self.plain_text_edit.appendPlainText(f"[{current_time}] {code} {price} {quantity}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()

    app.exec_()