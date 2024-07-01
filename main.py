from sniffer.Sniffer import Sniffer
from Helper import *
from timeit import default_timer as timer
from threading import Thread

def action(p_id, msg):
    global isInWorkbench

    start = timer()
    print(msg)

    if p_id == OPEN_WORKBENCH and isWhiteListedJob(msg):
        print("---- In the workbench! ----")
        isInWorkbench = True
    elif p_id == CLOSE_TRADE:
        print("---- Out of the workbench ----")
        isInWorkbench = False
    elif isInWorkbench or isInWorkbench is None:                     # only read packets if in workbench
        if p_id == ITEM_PLACED:                                      # when an item is placed
            if not isRune(msg):
                check_item(msg)
            elif msg["object"]["objectGID"] != 7508:                 # if not signature rune
                check_rune(msg)
                time_stamp_rune_used = timer()
        elif p_id == FUSION_RESULT:
            craft_result(msg)

        elif p_id == INFORMATION_MESSAGE or p_id == SYSTEM_MESSAGE:  # auto close error windows
            msg_id = msg["msgId"]
            if msg_id == NON_EXISTENT_RECIPE or msg_id == NOT_ENOUGH_QUANTITY:
                print("---- START THREAD ----")
                t1 = Thread(target=auto_click_on_ok())
                t1.start()
                t1.join()

    print("$$$$ TIME TO COMPUTE =  : ", timer() - start, " $$$$$")


"""
Call main() from your program with your callback function as argument
"""


def main(callback=action):
    sniffer = Sniffer(concatMode=False)
    sniffer.run(callback=action)

    #interface = CustomThread.UI()
    #interface.runLongTask()


if __name__ == "__main__":
    main()
