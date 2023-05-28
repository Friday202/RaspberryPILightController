import paho.mqtt.client as mqtt
import serial
import threading
import serial.tools.list_ports
import hashlib
import time


def validate_message(components):
    # Recreate sent message and compare hashes
    received_hash = components[-1]
    original_message = ','.join(components[:-1]) + ','
    generated_hash = generate_hash(original_message)
    if received_hash != generated_hash:
        return False
    return True


def get_Ardunio_ports():
    list = []
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "USB" in port.device:
            list.append(port.device)
    return list


def generate_hash(message_to_hash):
    hash_object = hashlib.sha256(message_to_hash.encode())
    return hash_object.hexdigest()


def publish_message(topic, message):
    client.publish(topic, message + generate_hash(message))


def ping_PC():
    # If this isn't accepted by PC then it means that PI has either lost connection to broker and can't reconnect,
    # completely lost connection, broker is not operational, script encountered a runtime error and closed or PI lost
    # power
    # keep in mind as SSH connection might fail due to IP change, if you get is successfully from hostname then SSH
    # must work and therefore problems lay somewhere else

    # All messages must end with comma and must be separated by comma and no whitespaces
    message = "check,"
    publish_message("pi_to_pc", message)


def start_threading_timer():
    ping_PC()
    threading.Timer(40.0, start_threading_timer).start()


def determine_Arduino_message(data):
    message = []
    print(data)
    if "NO" in data:
        return message
    message = data.split(",")
    # Remove start and end. Reminder should be numbers only
    message = message[1:-1]
    return message


def arduino_communication(arduino):
    # Arduino reading
    # When we receive something we send it to PC
    while True:
        data = arduino.readline().decode().rstrip()  # Read a line from the serial port
        if data:
            arduino_message = determine_Arduino_message(data)
            if len(arduino_message) == 8:
                publish_message("pi_to_pc", f"status,{arduino_message[0]},{arduino_message[1]},{arduino_message[2]},"
                                            f"{arduino_message[3]},{arduino_message[4]},{arduino_message[5]},"
                                            f"{arduino_message[6]},{arduino_message[7]},")


def send_message_to_arduinos(message_to_send):
    for arduino in arduinos:
        if arduino.isOpen():
            arduino.write(message_to_send.encode("utf-8"))


def check_scheduler():
    while True:
        current_time = time.localtime()
        time_minutes = current_time.tm_hour * 60 + current_time.tm_min

        for panel_number, schedule in enumerate(schedules):
            # Schedule is empty so leave it
            if len(schedule) == 0:
                continue
            for slot in schedule:
                start_minutes = int(slot[0])
                stop_minutes = int(slot[1])
                if start_minutes <= time_minutes <= stop_minutes:
                    # Get values from schedule
                    fir = slot[2]
                    nir = slot[3]
                    vis = slot[4]
                    uv = slot[5]

                    message = f"<set,{panel_number+1},{fir},{nir},{vis},{uv}>"
                    # Set PWM signals to Arduinos
                    send_message_to_arduinos(message)
                    # Remove this slot from scheduler as it has already been processed
                    schedule.remove(slot)
                    break

        time.sleep(5)


def on_message_received_from_PC(client, userdata, message):
    # 1.Decode message
    message = message.payload.decode()

    # 2. Send message back regardless of validity
    publish_message("pi_to_pc", "echo," + message)

    # 3. Split message by comma
    components = message.split(",")

    # 4. Check message validity
    if not validate_message(components):
        publish_message("pi_to_pc", "error,1,")
        return

    # 5. Hashes match so we can now decide what do to
    content = components[1:-1]

    if "status" in message:
        try:
            panel_number = int(content[0])

            # Get values from arduino
            message = f"<get,{panel_number}>"

            # Send message to ALL Arduinos, will send back when Arduino messages back
            send_message_to_arduinos(message)
        except:
            pass

    elif "set" in message:
        # Status is sent back to PC automatically
        try:
            integers = [int(c) for c in content]

            panel_number = integers[0]
            fir = integers[1]
            nir = integers[2]
            vis = integers[3]
            uv = integers[4]

            message = f"<set,{panel_number},{fir},{nir},{vis},{uv}>"

            # Set PWM signals to Arduinos
            send_message_to_arduinos(message)
        except:
            pass

    # Scheduler handling
    elif "ON" in message:
        try:
            panel_number = int(content[0])
            # Update Scheduler based on panel number
            schedules[panel_number - 1].clear()
            for slot in content[1:]:
                time_list = slot.split(";")
                schedules[panel_number - 1].append(time_list)
        except:
            pass

    elif "OFF" in message:
        try:
            # Clear scheduler, effectively turning it off
            panel_number = int(content[0])
            schedules[panel_number - 1].clear()
        except:
            pass

    else:
        # If message is valid but for some reason does not match with any order
        returning_message = "Received message from PC doesn't match any orders for PI!"
        publish_message("pi_to_pc", returning_message)


if __name__ == '__main__':

    MAX_TEMP = 80

    # Set up client and connect to broker
    client = mqtt.Client("R_PI")
    client.username_pw_set("jakob", "jakob")
    client.connect("localhost", 1883, 20)

    # Subscribe to topics
    client.subscribe("pc_to_pi")
    client.message_callback_add("pc_to_pi", on_message_received_from_PC)

    Arduino_ports = get_Ardunio_ports()

    if len(Arduino_ports) != 3:
        # Not enough arduinos!
        exit(1)

    # Engage serial communication
    arduino1 = serial.Serial(Arduino_ports[0], 9600)
    arduino2 = serial.Serial(Arduino_ports[1], 9600)
    arduino3 = serial.Serial(Arduino_ports[2], 9600)

    arduinos = [arduino1, arduino2, arduino3]

    # Start threads to listen for in serial communication
    for arduino in arduinos:
        thread = threading.Thread(target=arduino_communication, args=(arduino,))
        thread.start()

    # Start the timer for keeping MQTT communication in check. Ping every 40 seconds
    start_threading_timer()

    # Create list for holding schedules
    schedules = [[], [], []]

    # Create thread for scheduler checking. Interrupt happens 5 seconds
    scheduler_thread = threading.Thread(target=check_scheduler)
    scheduler_thread.start()

    client.loop_forever()

