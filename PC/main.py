from GUI import GUI
import tkinter as tk
from project_config import *
import logging

if __name__ == '__main__':
    # Create logger and add custom level:
    logging.NOTICE = 25
    logging.basicConfig(filename='log.log', level=logging.WARNING,
                        format='%(asctime)s %(levelname)s: %(message)s')
    logging.addLevelName(logging.NOTICE, "NOTICE")
    logging.getLogger().setLevel(logging.NOTICE)

    # Start GUI
    logging.getLogger().log(logging.NOTICE, '====================== Program has started ======================')
    root = tk.Tk()
    gui = GUI(root, RP_IP, RP_USERNAME, RP_PASSWORD, RP_HOSTNAME, SCRIPT_NAME, "PC")
    root.mainloop()





