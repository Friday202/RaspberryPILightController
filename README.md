# Raspberry PI Light Controller

This project implements a Graphical User Interface (GUI) in Python using the tkinter library for controlling and monitoring light panels connected to Raspberry Pi via Arduinos. The Raspberry Pi communicates with three Arduino boards via serial communication to set PWM signals for light control and retrieve status information for temperature and PWM values. The communication between the PC and Raspberry Pi is achieved using MQTT, with message integrity ensured through hashing. Additionally, multithreading is implemented on the Raspberry Pi to handle communication tasks, along with three separate threads for each Arduino to read data. MQTT comunication is kept in check via PI to PC pinging. 

## Features 

- GUI Interface: The project provides a user-friendly GUI for setting four light values on each light panel (far infrared, near infrared, visible, and ultraviolet) through sliders.
- Light Panel Status: The GUI displays the current status of the three light panels, including temperature and PWM values retrieved from the Arduinos.
- Scheduled Light Control: Users can schedule light values in advance, which are then sent to the Raspberry Pi which handles scheduler execution its own thread.
- Serial Communication: The Raspberry Pi communicates with the three Arduino boards via serial communication.
- MQTT Communication: The PC and Raspberry Pi exchange messages using MQTT, providing a reliable and efficient communication channel.
  
## Final GUI
![Screenshot 2023-05-25 133526](https://github.com/Friday202/RaspberryPILightController/assets/122792037/c713ae6c-08ef-4b28-bc67-659cb555493c)



Project example. PLease note that temperature sensor is not connected in the image below. 

![IMG_2966](https://github.com/Friday202/RaspberryPILightController/assets/122792037/f70ead7c-4fc4-4ec8-b696-d8c35a887b2e)
