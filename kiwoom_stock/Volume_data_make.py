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
from tqdm import tqdm

class Datamaker(QMainWindow):
    def __init__(self):    
        super().__init__()
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr_data)
        self.ocx.OnReceiveChejanData.connect(self._handler_chejan_data)


        self.account = ""

        self.login_event_loop = QEventLoop()
        
        self.CommConnect()          # 로그인이 될 때까지 대기
        self.run()


    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec()

    def run(self):
        # kospi = self.ocx.GetCodeListByMarket('0')
        # kospi = kospi.split(';')
        kosdaq = self.ocx.GetCodeListByMarket('10')
        kosdaq = kosdaq.split(';')

        # codes = kospi + kosdaq
        codes = kosdaq
        for num, code in enumerate(tqdm(codes)):
            self.request_opt10080(code)
            time.sleep(3.7)

        exit()
        
    def GetLoginInfo(self, tag):
        data = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return data

    def _handler_login(self, err_code):
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

        elif rqname == "분봉데이터":
            code = self.GetCommData(trcode, rqname, 0, "종목코드")
            amount = []
            trade_time = []
            for i in range(6,35,7):
                amount.append(self.GetCommData(trcode, rqname, i, "거래량"))
                trade_time.append(self.GetCommData(trcode, rqname, i, "체결시간"))

            if code != '':
                df = pd.DataFrame({'col1':trade_time, 'col2':amount})
                path = "volume_data/{}.csv".format(code)
                df.to_csv(path, index = False) 


        elif rqname == "예수금조회":
            available = self.GetCommData(trcode, rqname, 0, "주문가능금액")
            available = int(available)
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
        self.SetInputValue("종목코드",code)
        self.SetInputValue("틱범위",60)
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


    def _handler_chejan_data(self, gubun, item_cnt, fid_list):
        if 'gubun' == '1':      # 잔고통보
            예수금 = self.GetChejanData('951')
            예수금 = int(예수금)
            self.amount = int(예수금 * 0.2)
            self.plain_text_edit.appendPlainText(f"투자금액 업데이트 됨: {self.amount}")


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Datamaker()
    app.exec_()
