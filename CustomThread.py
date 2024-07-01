
import threading
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow
from fontTools.merge import timer

from Helper import *
from sniffer.Sniffer import Sniffer


class Worker(QObject):

    packets_whitelist = [3319, 6660, 3145, 5388, 1038, 3007, 269, 57, 5821]
    finished = pyqtSignal()
    progress = pyqtSignal(list)
    sniffer = Sniffer(concatMode=False)

    def run(self):
        self.sniffer.run(callback=self.emit_packet, whitelist=self.packets_whitelist)


    def emit_packet(self, p_id, msg):
        print("1")
        self.progress.emit([str(p_id), str(msg)])
        print("3")


class UI(QMainWindow):

    @staticmethod
    def action(values):
        print("2")
        global isInWorkbench
        p_id = int(values[0])
        msg = json.loads(values[1])
        print(msg)
        start = timer()
        if p_id == OPEN_WORKBENCH and isWhiteListedJob(msg):
            print("---- In the workbench! ----")
            isInWorkbench = True
        elif p_id == CLOSE_TRADE:
            print("---- Out of the workbench ----")
            isInWorkbench = False
        elif isInWorkbench or isInWorkbench is None:  # only read packets if in workbench
            if p_id == ITEM_PLACED:  # when an item is placed
                if not isRune(msg):
                    check_item(msg)
                elif msg["object"]["objectGID"] != 7508:  # if not signature rune
                    check_rune(msg)
                    time_stamp_rune_used = timer()
            elif p_id == FUSION_RESULT:
                craft_result(msg)
            elif p_id == INFORMATION_MESSAGE or p_id == SYSTEM_MESSAGE:  # auto close error windows
                msg_id = msg["msgId"]
                if msg_id == NON_EXISTENT_RECIPE or msg_id == NOT_ENOUGH_QUANTITY:
                    print("---- START THREAD ----")
                    t1 = threading.Thread(target=auto_click_on_ok())
                    t1.start()
                    t1.join()
        print("$$$$ TIME TO COMPUTE =  : ", timer() - start, " $$$$$")

    def runLongTask(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.action)
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self.longRunningBtn.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Long-Running Step: 0")
        )



