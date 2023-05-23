import tkinter as tk
from tkinter import ttk


class Scheduler:
    def __init__(self, root, input_slots=None):
        if input_slots is None:
            input_slots = []
        self.root = root
        self.slots = input_slots
        self.child_popups = []

        # Create the main window
        self.root.title("Scheduler")
        self.root.geometry("400x400")

        self.last_slot = 0
        self.update_display()

    def get_slots(self):
        return self.slots

    def validate_number_hour(self, new_value):
        if new_value == '':
            return True
        if new_value.isdigit():
            value = int(new_value)
            if 0 <= value <= 24:
                return True
        return False

    def validate_number_minute(self, new_value):
        if new_value == '':
            return True
        if new_value.isdigit():
            value = int(new_value)
            if 0 <= value <= 59:
                return True
        return False

    def validate_number_lights(self, new_value):
        if new_value == '':
            return True
        if new_value.isdigit():
            value = int(new_value)
            if 0 <= value <= 100:
                return True
        return False

    def check_validation(self, start_h, start_min, end_h, end_min, values, popup):

        # Clock setting
        if start_h == "":
            start_h = 0
        if start_min == "":
            start_min = 0
        if end_h == "":
            end_h = 0
        if end_min == "":
            end_min = 0

        start_time_minutes = int(start_h) * 60 + int(start_min)
        end_time_minutes = int(end_h) * 60 + int(end_min)

        # check overlapping and duplicates
        for slot in self.slots:
            slot_start = slot[0]
            slot_end = slot[1]
            # Check duplicates
            if slot_start == start_time_minutes or slot_end == end_time_minutes:
                return
            # Check inside overlap
            if start_time_minutes > slot_start and end_time_minutes < slot_end:
                return
            # Check left overlap
            if slot_start < start_time_minutes < slot_end:
                return
            # Check right overlap
            if slot_start < end_time_minutes < slot_end:
                return
            # Eating a slot
            if start_time_minutes < slot_start and end_time_minutes > slot_end:
                return

        values_ints = []
        # Values check
        for value in values:
            if value == "":        # Empty is assumed zero
                value_int = 0
            else:
                value_int = int(value)
            if value_int < 0 or value_int > 100:
                print("Error when entering values. Try again!")
                return
            values_ints.append(value_int)

        # Clock check
        print(start_time_minutes, end_time_minutes)
        if end_time_minutes > start_time_minutes:
            popup.destroy()
            self.save_slot(start_time_minutes, end_time_minutes, values_ints)
            print("Success!")
        else:
            print("Error when entering values. Try again!")

    def get_child_popups(self):
        return self.child_popups

    def add_slot(self):
        # Create a popup window for entering the slot details
        popup = tk.Toplevel()
        popup.title("Add Slot")
        popup.geometry("220x250")
        self.child_popups.append(popup)

        vcmd = popup.register(self.validate_number_hour)
        vcmd3 = popup.register(self.validate_number_minute)
        pady=-10

        # ttk.Label(popup, text="Add to slot").place(x=120, y=10)
        ttk.Label(popup, text="TIME", font=("Ariel", 16)).place(x=10, y=10)
        ttk.Label(popup, text="Start time:").place(x=10, y=50 + pady)

        start_hour = ttk.Entry(popup, validate="key", validatecommand=(vcmd, '%P'), width=4)
        start_hour.place(x=70, y=50 + pady)

        ttk.Label(popup, text=":").place(x=100, y=50 + pady)

        start_minute = ttk.Entry(popup, validate="key", validatecommand=(vcmd3, '%P'), width=4)
        start_minute.place(x=107, y=50 + pady)

        ttk.Label(popup, text="End time:").place(x=10, y=80 + pady)
        end_hour = ttk.Entry(popup, validate="key", validatecommand=(vcmd, '%P'), width=4)
        end_hour.place(x=70, y=80 + pady)
        ttk.Label(popup, text=":").place(x=100, y=80 + pady)
        end_minute = ttk.Entry(popup, validate="key", validatecommand=(vcmd3, '%P'), width=4)
        end_minute.place(x=107, y=80 + pady)

        ttk.Label(popup, text="VALUES", font=("Ariel", 16)).place(x=10, y=100)
        ttk.Label(popup, text="F-IR:").place(x=10, y=130)
        ttk.Label(popup, text="N-IR:").place(x=10, y=160)
        ttk.Label(popup, text="VIS:").place(x=10, y=190)
        ttk.Label(popup, text="UV:").place(x=10, y=220)

        vcmd2 = popup.register(self.validate_number_lights)

        far_ir = ttk.Entry(popup, validate="key", validatecommand=(vcmd2, '%P'), width=4)
        far_ir.place(x=50, y=130)

        near_ir = ttk.Entry(popup, validate="key", validatecommand=(vcmd2, '%P'), width=4)
        near_ir.place(x=50, y=160)

        vis = ttk.Entry(popup, validate="key", validatecommand=(vcmd2, '%P'), width=4)
        vis.place(x=50, y=190)

        uv = ttk.Entry(popup, validate="key", validatecommand=(vcmd2, '%P'), width=4)
        uv.place(x=50, y=220)

        ttk.Label(popup, text="%").place(x=80, y=130)
        ttk.Label(popup, text="%").place(x=80, y=160)
        ttk.Label(popup, text="%").place(x=80, y=190)
        ttk.Label(popup, text="%").place(x=80, y=220)

        # Create a button for confirming the slot details
        confirm_button = ttk.Button(popup, text="Confirm", command=lambda: self.check_validation(start_hour.get(), start_minute.get(), end_hour.get(), end_minute.get(), [far_ir.get(), near_ir.get(), vis.get(), uv.get()], popup))
        confirm_button.place(x=130, y=190)

        cancel_button = ttk.Button(popup, text="Cancel", command=lambda: popup.destroy())
        cancel_button.place(x=130, y=220)

    def save_slot(self, start_time, end_time, values):
        # Add the slot details to the list of slots
        self.slots.append((start_time, end_time, values))

        # Update the display with the new slot
        self.update_display()

    def update_display(self):
        # Function call when new slot is added, deleted or edited!

        # Clear the existing display
        for widget in self.root.winfo_children():
            if widget != self.root:
                widget.destroy()

        # Create a label for the scheduler
        label = ttk.Label(self.root, text="Scheduler", font=("Ariel", 20), anchor="center")
        label.place(x=150, y=10)

        # Create a button for adding a slot
        add_button = ttk.Button(self.root, text="Add to schedule", command=self.add_slot)
        add_button.place(x=165, y=50)

        # Print information
        ttk.Label(self.root, text="Start time:").place(x=70, y=80)
        ttk.Label(self.root, text="End time:").place(x=150, y=80)
        ttk.Label(self.root, text="Light values:").place(x=250, y=80)
        ttk.Label(self.root, text="[F-IR, N-IR, VIS, UV]").place(x=230, y=100)

        tk.Frame(self.root, width=380, height=2, bg='black').place(x=10, y=122)

        self.slots = sorted(self.slots, key=lambda slot: slot[0])

        # Create a frame for each slot
        for i, slot in enumerate(self.slots):
            pady = 10
            # Create a label for the slot number
            number_label = ttk.Label(self.root, text=f"Slot {i+1}:")
            number_label.place(x=10, y=120 + i*25 +pady)

            # Create a label for the start time
            start_time = ttk.Label(self.root, text=self.convert_time(slot[0]))
            start_time.place(x=80, y=120 + i*25 +pady)

            # Create a label for the end time
            end_time = ttk.Label(self.root, text=self.convert_time(slot[1]))
            end_time.place(x=160, y=120 + i*25 +pady)

            # Create a label for the value
            value_label = ttk.Label(self.root, text=f"{slot[2]}")
            value_label.place(x=230, y=120 + i*25 +pady)

            delete_button = ttk.Button(self.root, text="X", width=2, command=lambda s=slot: self.delete_slot(s))
            delete_button.place(x=350, y=120 + i*25 +pady)

    def delete_slot(self, slot_to_delete):
        self.slots.remove(slot_to_delete)
        self.update_display()

    def convert_time(self, time_in_minutes):
        hours = time_in_minutes // 60
        minutes = time_in_minutes % 60
        return f"{hours:02}:{minutes:02}"


# Test only
# root = tk.Tk()
# app = Scheduler(root)
# root.mainloop()
