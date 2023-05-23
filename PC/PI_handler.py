import paramiko
import netifaces
from project_config import *
from project_config import RP_IP
import getmac
import nmap
import socket
import logging


def log_message(logger, log_level, message_to_log):
    if log_level == 'NOTICE':
        logger.log(logging.NOTICE, message_to_log)
    elif log_level == 'WARNING':
        logger.log(logging.WARNING, message_to_log)
    elif log_level == 'ERROR':
        logger.log(logging.ERROR, message_to_log)
    elif log_level == 'CRITICAL':
        logger.log(logging.CRITICAL, message_to_log)


def get_PI_IP_by_hostname(hostname):
    logger = logging.getLogger()
    try:
        pi_ip = socket.gethostbyname(hostname)
        log_message(logger, "NOTICE", f"Successfully retrieved IP from hostname: {pi_ip}")
        return pi_ip

    except socket.gaierror:
        log_message(logger, "NOTICE", "Cannot get IP from hostname!" +
                    "\nYou will have to set in manually in project_config or retry later (10 seconds)" +
                    "\nInside RP type: ip-a to get ip" + "PI might also be turned off")
    return None


# def get_pi_ip():
#     nm = nmap.PortScanner()
#     nm.scan(hosts='192.168.1.0/24', arguments='-sn')
#
#     pi_mac_address = '20:0d:b0:4b:c9:8e' # Replace with your Pi's MAC address
#     pi_ip_addresses = []
#
#     for host in nm.all_hosts():
#         if 'mac' in nm[host]['addresses']:
#             mac_address = nm[host]['addresses']['mac']
#             if mac_address.startswith(pi_mac_address):
#                 pi_ip_addresses.append(nm[host]['addresses']['ipv4'])
#
#     return pi_ip_addresses
#
#
# def get_RP_IP():
#     # Get a list of all network interfaces
#     interfaces = netifaces.interfaces()
#
#     # Look for the interface that is currently connected to your Raspberry Pi
#     for interface in interfaces:
#         addrs = netifaces.ifaddresses(interface)
#         if netifaces.AF_INET in addrs:
#             for addr in addrs[netifaces.AF_INET]:
#                 if addr['addr'].startswith('192.168.1.'):
#                     pi_ip = addr['addr']
#                     print(f"Found Raspberry Pi at {pi_ip}")
#                     break
#             else:
#                 continue
#             break
#     else:
#         print("Could not find Raspberry Pi on network")


def transfer_script_to_PI(RP_ip, RP_username, RP_password, script_name):
    # Set up the SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the Raspberry Pi
        ssh.connect(RP_ip, username=RP_username, password=RP_password)

        # Set up the SFTP client
        sftp = ssh.open_sftp()

        # Transfer the Python script to the Raspberry Pi
        local_path = r'C:\Users\Jakob\PycharmProjects\Raspberry_PI/ForRaspberryPI.py'
        # local_path = r'C:\Users\Jakob\PycharmProjects\Raspberry_PI/arduinoTest.py'

        remote_path = f"/home/pi/python/{script_name}"
        sftp.put(local_path, remote_path)

        # Close the SFTP connection
        sftp.close()

        print("File transfer successful!")

    except Exception as e:
        print(f"File transfer failed: {e}")

    finally:
        # Close the SSH connection
        ssh.close()
        print("SSH connection closed")


def reset_PI(RP_ip, RP_username, RP_password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the Raspberry Pi
        ssh.connect(RP_ip, username=RP_username, password=RP_password)
        print("Connection successful!")

        # Execute the Python script on the Raspberry Pi
        stdin, stdout, stderr = ssh.exec_command('sudo shutdown -r now')

        # Print the output of the script
        print(stdout.read().decode())
        print("RP has shutdown")

        # Close the SSH connection
        ssh.close()

    except Exception as e:
        print(f"Connection failed: {e}")

    finally:
        # Close the SSH connection
        ssh.close()
        print("SSH connection closed")


def run_PI_script(RP_ip, RP_username, RP_password, script_name):
    logger = logging.getLogger()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    status = False
    try:
        # Connect to the Raspberry Pi
        ssh.connect(RP_ip, username=RP_username, password=RP_password)
        log_message(logger, "NOTICE", "SSH connection successful!")

        # Execute the Python script on the Raspberry Pi
        ssh.exec_command(f"python3 /home/pi/python/{script_name} &")
        # ssh.exec_command("nohup python3 /home/pi/python/{script_name} &")
        # Print the output of the script
        # print(stdout.read().decode())
        log_message(logger, "NOTICE", "Python script on RP is now running!")
        status = True

    except Exception as e:
        log_message(logger, "CRITICAL", f"SSH connection failed: {e}")
    finally:
        # Close the SSH connection
        ssh.close()
        log_message(logger, "NOTICE", "SSH connection closed\n")
        return status


def stop_PI_scripts(RP_ip, RP_username, RP_password, script_name):
    logger = logging.getLogger()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    status = False
    try:
        # Connect to the Raspberry Pi
        ssh.connect(RP_ip, username=RP_username, password=RP_password)
        log_message(logger, "NOTICE", "SSH connection successful!")

        # Send the stop command to the script
        stdin, stdout, stderr = ssh.exec_command(f"pkill -f {script_name}")

        # Print the output of the command
        #print(stdout.read().decode())
        log_message(logger, "NOTICE", f"All scripts with name: {script_name} have been terminated!")
        status = True

    except Exception as e:
        log_message(logger, "CRITICAL", f"SSH connection failed: {e}")

    finally:
        # Close the SSH connection
        ssh.close()
        log_message(logger, "NOTICE", "SSH connection closed\n")
        return status


def check_SSH_connection(RP_ip, RP_username, RP_password):
    logger = logging.getLogger()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    status = False
    try:
        # Connect to the Raspberry Pi
        ssh.connect(RP_ip, username=RP_username, password=RP_password)
        log_message(logger, "NOTICE", "SSH connection successful!")
        status = True

    except Exception as e:
        log_message(logger, "CRITICAL", f"SSH connection failed: {e}")

    finally:
        # Close the SSH connection
        ssh.close()
        log_message(logger, "NOTICE", "SSH connection closed\n")
        return status


def start_broker(RP_ip, RP_username, RP_password):
    logger = logging.getLogger()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    status = False
    try:
        # Connect to the Raspberry Pi
        ssh.connect(RP_ip, username=RP_username, password=RP_password)
        log_message(logger, "NOTICE", "SSH connection successful!")

        ssh.exec_command("sudo systemctl enable mosquitto.service")
        ssh.exec_command("/etc/init.d/mosquitto start")
        log_message(logger, "NOTICE", "MQTT broker should be operational...")
    except Exception as e:
        log_message(logger, "CRITICAL", f"SSH connection failed: {e}")

    finally:
        # Close the SSH connection
        ssh.close()
        log_message(logger, "NOTICE", "SSH connection closed\n")
        return status


def check_broker_status(RP_ip, RP_username, RP_password):
    logger = logging.getLogger()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    status = False
    try:
        # Connect to the Raspberry Pi
        ssh.connect(RP_ip, username=RP_username, password=RP_password)
        log_message(logger, "NOTICE", "SSH connection successful!")

        # Check if the MQTT broker is running
        stdin, stdout, stderr = ssh.exec_command("systemctl status mosquitto")
        output = stdout.read().decode()

        if "Active: active (running)" in output:
            log_message(logger, "NOTICE", "MQTT broker is running")
            status = True
        else:
            log_message(logger, "ERROR", "MQTT broker is NOT running")

    except Exception as e:
        log_message(logger, "CRITICAL", f"SSH connection failed: {e}")

    finally:
        # Close the SSH connection
        ssh.close()
        log_message(logger, "NOTICE", "SSH connection closed\n")
        return status


def check_script_running(ip, username, password, script_name):
    logger = logging.getLogger()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    status = False
    try:
        ssh.connect(ip, username=username, password=password)
        log_message(logger, "NOTICE", "SSH connection successful!")
        stdin, stdout, stderr = ssh.exec_command(f"pgrep -f {script_name}")
        pid = stdout.read().decode().strip()
        if pid:
            status = True
            log_message(logger, "NOTICE", "PI script is running!")
    except Exception as e:
        print(f"Error: {e}")
        log_message(logger, "NOTICE", "PI script is not running!")
    finally:
        ssh.close()
        log_message(logger, "NOTICE", "SSH connection closed\n")
        return status


if __name__ == '__main__':
    # Get the IP address of the Raspberry Pi and set it

    logging.NOTICE = 25
    logging.basicConfig(filename='log.log', level=logging.WARNING,
                        format='%(asctime)s %(levelname)s: %(message)s')
    logging.addLevelName(logging.NOTICE, "NOTICE")
    logging.getLogger().setLevel(logging.NOTICE)

    global RP_IP
    ip = get_PI_IP_by_hostname(RP_HOSTNAME)
    if ip:
        print(ip)
        RP_IP = ip

    # Make sure there are none scripts active
    stop_PI_scripts(RP_IP, RP_USERNAME, RP_PASSWORD, SCRIPT_NAME)

    # SCRIPT_NAME = 'arduinoTest.py'

    # Transfer file to PI over SSH
    transfer_script_to_PI(RP_IP, RP_USERNAME, RP_PASSWORD, SCRIPT_NAME)

    # Run Python script on PI using terminal and SSH
    # run_PI_script(RP_IP, RP_USERNAME, RP_PASSWORD, SCRIPT_NAME)

    # Stop Python script on PI using terminal and SSH
    # stop_PI_scripts(RP_IP, RP_USERNAME, RP_PASSWORD, SCRIPT_NAME)

