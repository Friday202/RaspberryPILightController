import tkinter as tk
import PI_handler
import Client
from project_config import MQTT_PASSWORD, MQTT_USERNAME
import logging
import time
from scheduler import Scheduler
import hashlib


class GUI:
    def __init__(self, master, rp_ip, rp_username, rp_password, rp_hostname, rp_script, mqtt_name):
        # Initial setup
        self.master = master
        master.title("Light Controller")
        master.geometry("950x800")

        self.logger = logging.getLogger()

        # Set RP input arguments
        self.rp_ip = rp_ip
        self.rp_username = rp_username
        self.rp_password = rp_password
        self.rp_hostname = rp_hostname
        self.rp_script = rp_script

        # Setup PC client
        self.pc_client = Client.Client(mqtt_name, MQTT_USERNAME, MQTT_PASSWORD)

        # Button variables
        self.l1_switch_state = False
        self.l2_switch_state = False
        self.l3_switch_state = False

        # Handle UI elements
        self.set_up_UI_elements()

        # Error handling
        self.error_code = 0

        # Scheduler
        self.slots_light1 = []
        self.slots_light2 = []
        self.slots_light3 = []

        # Timer to keep connection alive
        self.timer = 0

    def exit_clicked(self):
        # Instead of stopping script when we connect we check if on PI the script is running!
        self.pc_client.purpose_disconnect()
        self.master.destroy()

    def get_RP_IP(self):
        # Attempt to get rp_ip by hostname
        pi_ip = PI_handler.get_PI_IP_by_hostname(self.rp_hostname)
        if pi_ip:
            self.rp_ip = pi_ip
            self.log_message("NOTICE", "IP set from hostname")
        else:
            self.log_message("WARNING", "IP set from Project Config")

    def start_and_setup_PI(self):
        # Terminate all active scripts and start RP script
        return PI_handler.stop_PI_scripts(self.rp_ip, self.rp_username, self.rp_password, self.rp_script) and \
               PI_handler.run_PI_script(self.rp_ip, self.rp_username, self.rp_password, self.rp_script)

    def connect_clicked(self):
        # User can keep clicking button and nothing happens
        if self.pc_client.is_connected():
            return

        # Try to get PI IP by hostname
        self.get_RP_IP()

        # First check if on PI the script is already running
        if not PI_handler.check_script_running(self.rp_ip, self.rp_username, self.rp_password, self.rp_script):
            self.resolve(0)
            return

        # If succeeded attempt to connect to MQTT broker directly
        if not self.pc_client.connect(self.rp_ip):
            self.resolve(1)
            return

        # Start timer
        self.master.after(0, self.update_timer)

        # Subscribe on channel pi-to-pc and bind callback function
        self.pc_client.subscribe_to_topic("pi_to_pc")
        self.pc_client.client.message_callback_add("pi_to_pc", self.on_message_received_from_PI)

        # Button handling:
        self.change_button_state_to_all_buttons("normal")

    def resolve(self, error_num):
        # Try to get IP again
        self.get_RP_IP()

        if error_num == 0:
            if not PI_handler.check_SSH_connection(self.rp_ip, self.rp_username, self.rp_password):
                self.log_message("CRITICAL", "Fatal error you must restart PI power and restart program!" +
                                 "\nMake sure IP is correct and PI is operational. If problem persists contact support.")
                self.master.destroy()
                exit(1)
                return
            self.start_and_setup_PI()

        if error_num == 1:
            if not PI_handler.check_broker_status(self.rp_ip, self.rp_username, self.rp_password):
                self.log_message("ERROR", "Broker not running!")
                self.log_message("NOTICE", "Attempting to restart MQTT broker...")
                PI_handler.start_broker(self.rp_ip, self.rp_username, self.rp_password)

                time.sleep(2)

                if not PI_handler.check_broker_status(self.rp_ip, self.rp_username, self.rp_password):
                    self.log_message("CRITICAL", "Fatal error MQTT broker does not seem to turn on..." +
                                     "\nIf problem persists contact support.")
                    self.master.destroy()
                    exit(2)
                    return
                else:
                    self.log_message("NOTICE", "MQTT broker is operational! Retrying connection.")

        if error_num == 2:
            # If this isn't accepted by PC then it means that PI has either lost connection to broker and can't
            # reconnect,completely lost connection, broker is not operational, script encountered a runtime error and
            # closed or PI lost power keep in mind as SSH connection might fail due to IP change, if you get is
            # successfully from hostname then SSH must work and therefore problems lay somewhere else

            # 1. Check SSH communication and IP
            if not PI_handler.check_SSH_connection(self.rp_ip, self.rp_username, self.rp_password):
                self.log_message("CRITICAL", "Fatal error you must restart PI power and restart program!" +
                                 "\nMake sure IP is correct and PI is operational. If problem persists contact support.")
                self.master.destroy()
                exit(1)
                return

            # 2. Check broker status
            if not PI_handler.check_broker_status(self.rp_ip, self.rp_username, self.rp_password):
                self.log_message("ERROR", "Broker not running!")
                self.log_message("NOTICE", "Attempting to restart MQTT broker...")
                PI_handler.start_broker(self.rp_ip, self.rp_username, self.rp_password)

                time.sleep(2)

                if not PI_handler.check_broker_status(self.rp_ip, self.rp_username, self.rp_password):
                    self.log_message("CRITICAL", "Fatal error MQTT broker does not seem to turn on..." +
                                     "\nIf problem persists contact support.")
                    self.master.destroy()
                    exit(2)
                    return
                else:
                    self.log_message("NOTICE", "MQTT broker is operational! Retrying connection.")

            # 3. Must likely a runtime error on PI script terminate and restart it
            self.log_message("CRITICAL", "Most likely a runtime error on PI. Restarting script!")
            self.start_and_setup_PI()
            time.sleep(3)
            # Check for active script again
            if not PI_handler.check_script_running(self.rp_ip, self.rp_username, self.rp_password, self.rp_script):
                # Script cannot be run attempting complete PI restart is needed
                self.log_message("CRITICAL", "Script cannot be run. Restarting PI!")
                PI_handler.reset_PI(self.rp_ip, self.rp_username, self.rp_password)
                # Waiting for PI to reboot
                time.sleep(30)

        if error_num == 3:
            # PI is not operational, resetting in effect
            # NOTE all scheduler content is LOST
            self.log_message("CRITICAL", "Script cannot be run. Restarting PI!")
            PI_handler.reset_PI(self.rp_ip, self.rp_username, self.rp_password)
            time.sleep(30)

        # Retry connection
        self.connect_clicked()

    def change_button_state_to_all_buttons(self, new_state):
        self.change_button_state(self.button3, new_state)
        self.change_button_state(self.button4, new_state)
        self.change_button_state(self.button5, new_state)

        self.change_button_state(self.button6, new_state)
        self.change_button_state(self.button7, new_state)
        self.change_button_state(self.button8, new_state)

        self.change_button_state(self.l1_switch, new_state)
        self.change_button_state(self.l2_switch, new_state)
        self.change_button_state(self.l3_switch, new_state)

    def change_button_state(self, button, new_state):
        button.config(state=new_state)

    def update_label(self, label, type_, value):
        label.config(text=f"{type_}: {value}%")

    def update_label_temp(self, label, value):
        label.config(text=f"{value}°C")

    def confirm_clicked(self, panel_number):
        # If not connected do not send anything
        if not self.pc_client.is_connected():
            return

        if panel_number == 1:
            nir = self.scale_panel_1_NIR.get()
            fir = self.scale_panel_1_FIR.get()
            vis = self.scale_panel_1_VIS.get()
            uv = self.scale_panel_1_UV.get()
        elif panel_number == 2:
            nir = self.scale_panel_2_NIR.get()
            fir = self.scale_panel_2_FIR.get()
            vis = self.scale_panel_2_VIS.get()
            uv = self.scale_panel_2_UV.get()
        elif panel_number == 3:
            nir = self.scale_panel_3_NIR.get()
            fir = self.scale_panel_3_FIR.get()
            vis = self.scale_panel_3_VIS.get()
            uv = self.scale_panel_3_UV.get()
        else:
            print("Internal error!")
            return

        self.pc_client.publish_message("pc_to_pi", f"set,{panel_number},{nir},{fir},{vis},{uv},")

    def status_clicked(self, panel_number):
        if not self.pc_client.is_connected():
            return
        self.pc_client.publish_message("pc_to_pi", f"status,{panel_number},")

    def update_timer(self):
        self.timer += 1
        if self.timer == 7:
            self.resolve(2)
        if self.timer > 8:
            self.resolve(3)

        # Update timer every 10 seconds
        self.master.after(10000, self.update_timer)

    def restart_timer(self):
        self.timer = 0

    def validate_message(self, components):
        # No matter what restart timer as connection seems to be alive
        self.restart_timer()
        if components[0] == "echo":
            # It is just echo we don't need to process the message
            return False
        # Recreate sent message and compare hashes
        received_hash = components[-1]
        original_message = ','.join(components[:-1]) + ','
        generated_hash = self.generate_hash(original_message)

        if received_hash != generated_hash:
            # TODO: Hash mismatch handling. For now we don't do anything and disregard message
            self.log_message("CRITICAL", "Hashes do not match, therefore received message was not received properly. "
                                         "Likely lost data. Disregarding message...")
            return False
        return True

    def on_message_received_from_PI(self, client, userdata, message):
        # 1.Decode message
        message = message.payload.decode()

        # 2. Log the message regardless of what happens
        self.log_message("NOTICE", "Received message on PC: " + message)

        # 3. Split message by comma
        components = message.split(",")

        # 4. Check message validity
        if not self.validate_message(components):
            return

        # 5. Hashes match so we can now decide what do to
        content = components[1:-1]

        if "check" in message:
            self.restart_timer()

        elif "status" in message:
            try:
                integers = [int(c) for c in content]
                self.set_status_labels(integers[0], integers[1], integers[2], integers[3], integers[4],
                                       integers[5], integers[6], integers[7])
            except:
                pass

    def set_status_labels(self, panel_number, fir, nir, vis, uv, temp1, temp2, temp3):
        self.update_label(self.panel_labels[panel_number-1][0], "F-IR", fir)
        self.update_label(self.panel_labels[panel_number - 1][1], "N-IR", nir)
        self.update_label(self.panel_labels[panel_number-1][2], "VIS", vis)
        self.update_label(self.panel_labels[panel_number-1][3], "UV", uv)
        self.update_label_temp(self.panel_labels[panel_number-1][4], temp1)
        self.update_label_temp(self.panel_labels[panel_number - 1][5], temp2)
        self.update_label_temp(self.panel_labels[panel_number - 1][6], temp3)

    # Scheduler code

    def toggle(self, panel_number):
        if not self.pc_client.is_connected():
            return

        # TODO: add read from file

        contents = self.get_scheduler_contents(panel_number)

        if panel_number == 1:
            self.l1_switch_state = not self.l1_switch_state

            if self.l1_switch_state:
                self.label_light_1.config(foreground="green", text="ACTIVE")
                self.change_button_state(self.button3, "disabled")
                # self.change_button_state(self.button_sch_1, "disabled")

                self.pc_client.publish_message("pc_to_pi", f"ON,{panel_number},{contents}")
            else:
                self.label_light_1.config(foreground="red", text="INACTIVE")
                self.change_button_state(self.button3, "normal")
                self.change_button_state(self.button_sch_1, "normal")

                self.pc_client.publish_message("pc_to_pi", f"OFF,{panel_number},")

        elif panel_number == 2:
            self.l2_switch_state = not self.l2_switch_state

            if self.l2_switch_state:
                self.label_light_2.config(foreground="green", text="ACTIVE")
                self.change_button_state(self.button4, "disabled")
                # self.change_button_state(self.button_sch_2, "disabled")

                self.pc_client.publish_message("pc_to_pi", f"ON,{panel_number},{contents}")
            else:
                self.label_light_2.config(foreground="red", text="INACTIVE")
                self.change_button_state(self.button4, "normal")
                self.change_button_state(self.button_sch_2, "normal")

                self.pc_client.publish_message("pc_to_pi", f"OFF,{panel_number},")

        elif panel_number == 3:
            self.l3_switch_state = not self.l3_switch_state

            if self.l3_switch_state:
                self.label_light_3.config(foreground="green", text="ACTIVE")
                self.change_button_state(self.button5, "disabled")
                # self.change_button_state(self.button_sch_3, "disabled")

                self.pc_client.publish_message("pc_to_pi", f"ON,{panel_number},{contents}")
            else:
                self.label_light_3.config(foreground="red", text="INACTIVE")
                self.change_button_state(self.button5, "normal")
                self.change_button_state(self.button_sch_3, "normal")

                self.pc_client.publish_message("pc_to_pi", f"OFF,{panel_number},")

    def get_scheduler_contents(self, panel_number):
        string_representation = ""
        if panel_number == 1:
            for slot in self.slots_light1:
                string_representation += f"{slot[0]};{slot[1]};{';'.join(str(i) for i in slot[2])},"
        elif panel_number == 2:
            for slot in self.slots_light2:
                string_representation += f"{slot[0]};{slot[1]};{';'.join(str(i) for i in slot[2])},"
        elif panel_number == 3:
            for slot in self.slots_light3:
                string_representation += f"{slot[0]};{slot[1]};{';'.join(str(i) for i in slot[2])},"
        return string_representation

    def clear_log(self):
        with open("log.log", "w"):
            pass

    def open_scheduler(self, panel_number):
        # Disable scheduler button
        current_slots = []
        if panel_number == 1:
            self.change_button_state(self.button_sch_1, "disabled")
            self.change_button_state(self.l1_switch, "disabled")

            current_slots = self.slots_light1
        elif panel_number == 2:
            self.change_button_state(self.button_sch_2, "disabled")
            self.change_button_state(self.l2_switch, "disabled")

            current_slots = self.slots_light2
        elif panel_number == 3:
            self.change_button_state(self.button_sch_3, "disabled")
            self.change_button_state(self.l3_switch, "disabled")

            current_slots = self.slots_light3

        popup = tk.Toplevel()
        scheduler = Scheduler(popup, current_slots)
        popup.wm_protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(scheduler, popup, panel_number))

    def on_popup_close(self, scheduler, popup, panel_number):
        if panel_number == 1:
            self.change_button_state(self.button_sch_1, "normal")
            if self.pc_client.is_connected():
                self.change_button_state(self.l1_switch, "normal")

            self.slots_light1 = scheduler.get_slots()
        elif panel_number == 2:
            self.change_button_state(self.button_sch_2, "normal")
            if self.pc_client.is_connected():
                self.change_button_state(self.l2_switch, "normal")

            self.slots_light2 = scheduler.get_slots()
        elif panel_number == 3:
            self.change_button_state(self.button_sch_3, "normal")
            if self.pc_client.is_connected():
                self.change_button_state(self.l3_switch, "normal")

            self.slots_light3 = scheduler.get_slots()

        # Garbage collection
        for child_popup in scheduler.get_child_popups():
            child_popup.destroy()
        print("Popup window closed")
        popup.destroy()

    # CODE END -------------------------------------------------------------------
    # CODE END -------------------------------------------------------------------
    # CODE END -------------------------------------------------------------------

    def set_up_UI_elements(self):
        tk.Label(self.master, text="LIGHT CONTROLLER:", font=("Arial", 26)).place(x=20, y=20)

        self.connect_button = tk.Button(self.master, text="Connect", command=self.connect_clicked)
        self.connect_button.place(x=20, y=70)

        self.exit_button = tk.Button(self.master, text="Exit", command=self.exit_clicked)
        self.exit_button.place(x=60+80, y=70)

        padding = 20
        down = 50

        # Frames ------------------------------------------------------------
        tk.Frame(self.master, width=295, height=580, relief='solid', borderwidth=3).place(x=padding, y=150)
        tk.Frame(self.master, width=295, height=580, relief='solid', borderwidth=3).place(x=2*padding+240+45, y=150)
        tk.Frame(self.master, width=295, height=580, relief='solid', borderwidth=3).place(x=3*padding+480+2*45, y=150)

        # Frames labels -----------------------------------------------------
        tk.Label(self.master, text="PANEL 1:", font=("Arial", 20)).place(x=padding, y=110)
        tk.Label(self.master, text="PANEL 2:", font=("Arial", 20)).place(x=2 * padding + 240 + 45, y=110)
        tk.Label(self.master, text="PANEL 3:", font=("Arial", 20)).place(x=3 * padding + 480 + 2 * 45, y=110)

        # Sliders for panels ------------------------------------------------
        tk.Label(self.master, text="F-IR:", font=("Arial", 18)).place(x=padding + 20, y=150 + 22)
        self.scale_panel_1_FIR = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_1_FIR.place(x=padding + 90, y=150+10)

        tk.Label(self.master, text="N-IR:", font=("Arial", 18)).place(x=padding + 20, y=150 + 22 + down)
        self.scale_panel_1_NIR = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_1_NIR.place(x=padding + 90, y=150 + 10 + down)

        tk.Label(self.master, text="VIS:", font=("Arial", 18)).place(x=padding + 20, y=150 + 22 + 2*down)
        self.scale_panel_1_VIS = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_1_VIS.place(x=padding + 90, y=150 + 10 + 2*down)

        tk.Label(self.master, text="UV:", font=("Arial", 18)).place(x=padding + 20, y=150 + 22 + 3*down)
        self.scale_panel_1_UV = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_1_UV.place(x=padding + 90, y=150 + 10 + 3*down)

        # ------------------------------------------
        tk.Label(self.master, text="F-IR:", font=("Arial", 18)).place(x=2*padding+240+20 + 45, y=150 + 22)
        self.scale_panel_2_FIR = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_2_FIR.place(x=2*padding+240+90+ 45, y=150 + 10)

        tk.Label(self.master, text="N-IR:", font=("Arial", 18)).place(x=2 * padding + 240 + 20+ 45, y=150 + 22 + down)
        self.scale_panel_2_NIR = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_2_NIR.place(x=2 * padding + 240 + 90+ 45, y=150 + 10 + down)

        tk.Label(self.master, text="VIS:", font=("Arial", 18)).place(x=2*padding+240+20+ 45, y=150 + 22 + 2*down)
        self.scale_panel_2_VIS = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_2_VIS.place(x=2*padding+240+90+ 45, y=150 + 10 + 2*down)

        tk.Label(self.master, text="UV:", font=("Arial", 18)).place(x=2*padding+240+20+ 45, y=150 + 22 + 3 * down)
        self.scale_panel_2_UV = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_2_UV.place(x=2*padding+240+90+ 45, y=150 + 10 + 3 * down)

        # ------------------------------------------
        tk.Label(self.master, text="F-IR:", font=("Arial", 18)).place(x=3 * padding + 2*240 + 20 + 2 * 45, y=150 + 22)
        self.scale_panel_3_FIR = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_3_FIR.place(x=3 * padding + 2*240 + 90+ 2 * 45, y=150 + 10)

        tk.Label(self.master, text="N-IR:", font=("Arial", 18)).place(x=3 * padding + 2 * 240 + 20+ 2 * 45, y=150 + 22+down)
        self.scale_panel_3_NIR = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_3_NIR.place(x=3 * padding + 2 * 240 + 90+ 2 * 45, y=150 + 10+down)

        tk.Label(self.master, text="VIS:", font=("Arial", 18)).place(x=3 * padding + 2*240 + 20+ 2 * 45, y=150 + 22 + 2*down)
        self.scale_panel_3_VIS = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_3_VIS.place(x=3 * padding + 2*240 + 90+ 2 * 45, y=150 + 10 + 2*down)

        tk.Label(self.master, text="UV:", font=("Arial", 18)).place(x=3 * padding + 2*240 + 20+ 2 * 45, y=150 + 22 + 3 * down)
        self.scale_panel_3_UV = tk.Scale(self.master, from_=0, to=100, orient="horizontal", length=170)
        self.scale_panel_3_UV.place(x=3 * padding + 2*240 + 90+ 2 * 45, y=150 + 10 + 3 * down)

        # Buttons for panels ------------------------------------------------
        self.button3 = tk.Button(self.master, text="Confirm", command=lambda: self.confirm_clicked(1))
        self.button3.place(x=padding + 80+10 +30, y=150 + 30 + 3.65 * down)
        self.change_button_state(self.button3, "disabled")

        self.button4 = tk.Button(self.master, text="Confirm", command=lambda: self.confirm_clicked(2))
        self.button4.place(x=2*padding + 240+80+10+75, y=150 + 30 + 3.65 * down)
        self.change_button_state(self.button4, "disabled")

        self.button5 = tk.Button(self.master, text="Confirm", command=lambda: self.confirm_clicked(3))
        self.button5.place(x=3*padding + 2*240+80+130, y=150 + 30 + 3.65 * down)
        self.change_button_state(self.button5, "disabled")

        # Line separation --------------------------------------------------
        tk.Frame(self.master, width=260, height=2, bg='black').place(x=3*padding + 2*240+15+2*45, y=150 + 30 + 3 * down+70)
        tk.Frame(self.master, width=260, height=2, bg='black').place(x=2 * padding + 240 + 15+45, y=150 + 30 + 3 * down + 70)
        tk.Frame(self.master, width=260, height=2, bg='black').place(x= padding + 15, y=150 + 30 + 3 * down + 70)

        tk.Frame(self.master, width=260, height=2, bg='black').place(x=3 * padding + 2 * 240 + 15 + 2 * 45, y=150 +475)
        tk.Frame(self.master, width=260, height=2, bg='black').place(x=2 * padding + 240 + 15 + 45, y=150 + 475)
        tk.Frame(self.master, width=260, height=2, bg='black').place(x=padding + 15, y=150 + 475)

        # Labels for status ------------------------------------------------
        self.panel_labels = []

        label13 = tk.Label(self.master, text="", font=("Arial", 18))
        label13.place(x=3 * padding + 2*240 + 20+90, y=415)

        label133 = tk.Label(self.master, text="", font=("Arial", 18))
        label133.place(x=3 * padding + 2 * 240 + 20 +130+100, y=415)

        label14 = tk.Label(self.master, text="", font=("Arial", 18))
        label14.place(x=3 * padding + 2 * 240 + 20+90, y=415+40)

        label15 = tk.Label(self.master, text="", font=("Arial", 18))
        label15.place(x=3 * padding + 2 * 240 + 20 +130+100, y=415+40)

        label16 = tk.Label(self.master, text="", font=("Arial", 18))
        label16.place(x=3 * padding + 2 * 240 + 20 + 90+ 80, y=400 + 80 + 40)

        label161 = tk.Label(self.master, text="", font=("Arial", 18))
        label161.place(x=3 * padding + 2 * 240 + 20 + 90 +80+100, y=400 + 80 + 40)

        label162 = tk.Label(self.master, text="", font=("Arial", 18))
        label162.place(x=3 * padding + 2 * 240 + 20 + 90 + 80, y=400 + 80 + 40 + 30)

        # ------------------------------------------
        label17 = tk.Label(self.master, text="", font=("Arial", 18))
        label17.place(x=2 * padding +  240 + 20+ 45, y=415)

        label177 = tk.Label(self.master, text="", font=("Arial", 18))
        label177.place(x=2 * padding + 240 + 20 + 130+ 50, y=415)

        label18 = tk.Label(self.master, text="", font=("Arial", 18))
        label18.place(x=2 * padding +  240 + 20+ 45, y=415+40)

        label19 = tk.Label(self.master, text="", font=("Arial", 18))
        label19.place(x=2 * padding + 240 + 20 + 130+ 50, y=415+40)

        label20 = tk.Label(self.master, text="", font=("Arial", 18))
        label20.place(x=2 * padding + 240 + 20 + 45 + 80, y=400 + 80 + 40)

        label201 = tk.Label(self.master, text="", font=("Arial", 18))
        label201.place(x=2 * padding + 240 + 20 + 45+ 170, y=400 + 80 + 40)

        label202 = tk.Label(self.master, text="", font=("Arial", 18))
        label202.place(x=2 * padding + 240 + 20 + 45 + 80, y=400 + 80 + 40+30)

        # ------------------------------------------
        label21 = tk.Label(self.master, text="", font=("Arial", 18))
        label21.place(x=padding + 20, y=415)

        label211 = tk.Label(self.master, text="", font=("Arial", 18))
        label211.place(x=padding + 20 + 135, y=415)

        label22 = tk.Label(self.master, text="", font=("Arial", 18))
        label22.place(x=padding + 20, y=415 + 40)

        label23 = tk.Label(self.master, text="", font=("Arial", 18))
        label23.place(x=padding + 20 + 135, y=415 + 40)

        label24 = tk.Label(self.master, text="", font=("Arial", 18))
        label24.place(x=padding + 20+80, y=400 + 80 + 40)

        label25 = tk.Label(self.master, text="", font=("Arial", 18))
        label25.place(x=padding + 20+80, y=400 + 80 + 40+30)

        label26 = tk.Label(self.master, text="", font=("Arial", 18))
        label26.place(x=padding + 190, y=400 + 80 + 40)

        self.panel_labels.append([label21, label211, label22, label23, label24, label25, label26])
        self.panel_labels.append([label17, label177, label18, label19, label20, label201, label202])
        self.panel_labels.append([label13, label133, label14, label15, label16, label161, label162])

        # Initialize label values
        for i in range(3):
            self.set_status_labels(i, 0, 0, 0, 0, 0, 0, 0)

        # Temperature labels:
        tk.Label(self.master, text="Temp:", font=("Arial", 18)).place(x=padding + 20, y=400 + 80 + 40)
        tk.Label(self.master, text="Temp:", font=("Arial", 18)).place(x=2 * padding + 240 + 20 + 45, y=400 + 80 + 40)
        tk.Label(self.master, text="Temp:", font=("Arial", 18)).place(x=3 * padding + 2 * 240 + 20 + 90, y=400 + 80 + 40)

        # Scheduler labels:
        tk.Label(self.master, text="Scheduler:", font=("Arial", 18)).place(x=padding + 20, y=640)
        tk.Label(self.master, text="Scheduler:", font=("Arial", 18)).place(x=2 * padding + 240 + 20 + 45, y=640)
        tk.Label(self.master, text="Scheduler:", font=("Arial", 18)).place(x=3 * padding + 2 * 240 + 20 + 90, y=640)

        # Buttons for panels2 ----------------------------------------------
        self.button6 = tk.Button(self.master, text="Status", command=lambda: self.status_clicked(1))
        self.button6.place(x=padding + 80+10 +30+5, y=150 + 30 + 3 * down+260)
        self.change_button_state(self.button6, "disabled")

        self.button7 = tk.Button(self.master, text="Status", command=lambda: self.status_clicked(2))
        self.button7.place(x=2*padding + 240+80+10+80, y=150 + 30 + 3 * down+260)
        self.change_button_state(self.button7, "disabled")

        self.button8 = tk.Button(self.master, text="Status", command=lambda: self.status_clicked(3))
        self.button8.place(x=3*padding + 2*240+80+135, y=150 + 30 + 3 * down +260)
        self.change_button_state(self.button8, "disabled")

        # Buttons for reseting logger --------------------------------------
        self.button9 = tk.Button(self.master, text="Delete log", command=self.clear_log)
        self.button9.place(x=padding + 80 + 10+100, y=70)

        # Buttons for schedulers -------------------------------------------
        self.button_sch_1 = tk.Button(self.master, text="Setup", command=lambda: self.open_scheduler(1))
        self.button_sch_1.place(x=padding + 20 + 80, y=690)

        self.button_sch_2 = tk.Button(self.master, text="Setup", command=lambda: self.open_scheduler(2))
        self.button_sch_2.place(x=2*padding+240+45 + 100, y=690)

        self.button_sch_3 = tk.Button(self.master, text="Setup", command=lambda: self.open_scheduler(3))
        self.button_sch_3.place(x=3*padding+480+2*45 + 100, y=690)

        # Buttons for ON/OFF -------------------------------------------
        self.l1_switch = tk.Checkbutton(command=lambda: self.toggle(1), text="ON/OFF")
        self.l1_switch.place(x=20+150, y=690)

        self.l2_switch = tk.Checkbutton(command=lambda: self.toggle(2), text="ON/OFF")
        self.l2_switch.place(x=2*padding+240+45  + 150, y=690)

        self.l3_switch = tk.Checkbutton(command=lambda: self.toggle(3), text="ON/OFF")
        self.l3_switch.place(x= 3*padding+480+2*45  + 150, y=690)

        self.change_button_state(self.l1_switch, "disabled")
        self.change_button_state(self.l2_switch, "disabled")
        self.change_button_state(self.l3_switch, "disabled")

        # Labels for ACTIVE scheduler ----------------------------------
        self.label_light_1 = tk.Label(self.master, text="INACTIVE", font=("Arial", 18), foreground="red")
        self.label_light_1.place(x=20+150, y=640)

        self.label_light_2 = tk.Label(self.master, text="INACTIVE", font=("Arial", 18), foreground="red")
        self.label_light_2.place(x=2*padding+240+45 + 150, y=640)

        self.label_light_3 = tk.Label(self.master, text="INACTIVE", font=("Arial", 18), foreground="red")
        self.label_light_3.place(x=3*padding+480+2*45 + 150, y=640)

    def log_message(self, log_level, message_to_log):
        if log_level == 'NOTICE':
            self.logger.log(logging.NOTICE, message_to_log)
        elif log_level == 'WARNING':
            self.logger.log(logging.WARNING, message_to_log)
        elif log_level == 'ERROR':
            self.logger.log(logging.ERROR, message_to_log)
        elif log_level == 'CRITICAL':
            self.logger.log(logging.CRITICAL, message_to_log)

    @staticmethod
    def generate_hash(message_to_hash):
        hash_object = hashlib.sha256(message_to_hash.encode())
        return hash_object.hexdigest()