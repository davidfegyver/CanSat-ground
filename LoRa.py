import serial
import serial.tools.list_ports
import time

class CanSat_LoRa:
    def __init__(self):
        self.serial = None

    def find_and_open(self, baudrate=115200):
        """
        Find the LoRa module and open a UART connection to it.

        :param baudrate: Communication speed (default: 115200 bps).
        """
        ports = self.get_ports()
        for port in ports:
            try:
                self.open(port.device, baudrate)
                print(f"Connected to {port.device}")

                ver = self.sys_get_version()

                if "WLR089" in ver:
                    print("Connected to LoRa module.")

                else:
                    print("Connected to unknown device.")
                    self.close()
                    self.serial = None
                    continue

                return
            except serial.SerialException:
                pass

        if self.serial is None:
            raise serial.SerialException("No LoRa module found.")

    def open(self, port, baudrate=115200):
        """
        Open a UART connection to the LoRa module.

        :param port: UART port to which the LoRa module is connected (e.g., 'COM3' or '/dev/ttyUSB0').
        :param baudrate: Communication speed (default: 115200 bps).
        """

        self.serial = serial.Serial(port, baudrate, timeout=0.5)
        self.serial.flush()

    def close(self):
        """
        Close the UART connection.
        """
        self.serial.close()

    def get_ports(self):
        """ 
        Get a list of available serial ports.
        """
        ports = serial.tools.list_ports.comports()

        return sorted(ports)

    def send_command(self, command):
        """
        Send a command to the LoRa module and return the response.

        :param command: Command string to send.
        :return: Response string from the module.
        """
        full_command = f"{command}\r\n"
        self.serial.write(full_command.encode())
        time.sleep(0.1)
        response = self.serial.read_all().decode().strip()
        return response

    """ 
        System Commands

        Provides system level behavior actions, gathers status information on the firmware and hardware version.
    """

    def sys_reset(self):
        """
        Resets and restarts the SAM R34/R35 devices including the WLR089U0 module.
        """

        return self.send_command("sys reset")
    
    def sys_sleep(self, mode, duration):
        """
        Puts the system in sleep for a finite number of milliseconds.

        :param mode: Sleep mode ('standby' or 'backup').
        :param duration: Sleep duration in milliseconds. The minimum sleep time for any of the sleep modes is 1000 ms.
        """

        if mode not in ["standby", "backup"]:
            raise ValueError("Mode must be 'standby' or 'backup'.")
        if duration < 1000:
            raise ValueError("Duration must be at least 1000 ms.")

        return self.send_command(f"sys sleep {mode} {duration}")

    def sys_factory_reset(self):
        """
        This command resets SAM R34/R35 devices, including the WLR089U0 module SiP internal configurations, to factory default values and restarts them. The user will lose all RF settings.
        """

        return self.send_command("sys factoryRESET")
    
    def sys_get_version(self):
        """
        This command returns the information related to the hardware platform, firmware version, release date and timestamp on firmware creation.
        """
        return self.send_command("sys get ver")

    """
        Transceiver Commands
        Provides radio specific configurations, directly accessing and updating the transceiver setup.
    """
    def radio_set_frequency(self, frequency):
        """
        This command changes the communication frequency of the radio transceiver.

        :param frequency:  Decimal representing the frequency, from 137000000 to 175000000 or from 410000000 to 525000000 or from 862000000 to 1020000000, in Hz.
        
        """

        if (frequency < 137_000_000 or frequency > 175_000_000) and (frequency < 410_000_000 or frequency > 525_000_000) and (frequency < 862_000_000 or frequency > 1_020_000_000):
            raise ValueError("Frequency out of range.")
        return self.send_command(f"radio set freq {frequency}")

    def radio_set_frequency_mhz(self, frequency_mhz):
        """
        This command changes the communication frequency of the radio transceiver.

        :param frequency_mhz: Decimal representing the frequency, from 137 to 175 or from 410 to 525 or from 862 to 1020, in MHz.
        """

        frequency_hz = int(frequency_mhz * 1_000_000)
        return self.radio_set_frequency(frequency_hz)

    def radio_set_paboost(self, state):
        """
        This command enables the PABOOST to use maximum power for radio operation.
        
        :param state: State of the PABOOST ('on' or 'off').
        """
        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'.")
        return self.send_command(f"radio set pa {state}")
    
    def radio_get_paboost(self):
        """
        This command returns the current state of the PABOOST.
        """
        return self.send_command("radio get pa")
    

    def radio_set_power(self, power):
        """
        This command changes the transceiver output power. It is possible to set the output power above the regulatory limits. This power setting allows some compensation on the cable or transmission line loss.

        :param power:  Signed decimal number representing the transceiver output power, from 2 to 20 or -4 to 15 depending on paboost “On” or “Off” state, respectively
        """
        if power < -4 or power > 20:
            raise ValueError("Power level must be between -4 and 20.")

        return self.send_command(f"radio set pwr {power}")
    def radio_set_modulation(self, mode):
        """
        This command changes the modulation method being used by the SiP. Altering the mode of operation does not affect previously set parameters, variables or registers. FSK mode also allows GFSK transmissions when data shaping is enabled

        :param mode: Modulation mode ('lora' or 'fsk').
        """

        if mode not in ["lora", "fsk"]:
            raise ValueError("Mode must be 'lora' or 'fsk'.")
        
        return self.send_command(f"radio set mod {mode}")
    def radio_set_crc(self, state):
        """
        This command enables or disables the CRC header for communications. 

        :param state: String representing the state of the CRC header, either on or off.
        """
        return self.send_command(f"radio set crc {state}")
    def radio_get_crc(self):
        """
        This command returns the current CRC header state.
        """
        return self.send_command("radio get crc")

    def radio_get_modulation(self):
        """
        This command returns the current modulation mode.
        """
        return self.send_command("radio get mod")
    
    def radio_get_frequency(self):
        """
        This command returns the current frequency.
        """
        return self.send_command("radio get freq")

    def radio_get_frequency_mhz(self):
        """
        This command returns the current frequency in MHz.
        """
        return int(self.get_radio_frequency()) / 1_000_000

    def radio_get_power(self):
        """
        This command returns the current power level.
        """
        return self.send_command("radio get pwr")
    
    def radio_get_power(self):
        """
        This command returns the current power level.
        """
        return self.send_command("radio get pwr")
    
    def radio_continous_reception(self, cb):
        """
        Miau! Végtelen ciklus!

        Continuous Reception mode is exited once a valid packet is received or if an rxstop command is issued or the Watchdog Timer expires
        
        :param cb: Callback function to call when a packet is received.
        """
        self.send_command("radio rx 0")

        while True: 
            response = self.serial.readline().decode().strip()

            if response.startswith("radio_rx"):
                data = response.split(" ")[1]
                data = bytes.fromhex(data).decode()
                cb(data)
        

            

    def radio_transmit(self, data, count=1):
        """
        Configures a simple radio packet transmission according to the prior configuration settings.

        :param data:  Hexadecimal value representing the data to be transmitted, from 0 to 255 bytes for LoRa modulation and from 0 to 64 bytes for FSK modulation.

        :param count: Decimal value representing the count of the data to transmitted multiple times from 0 to 65535 bytes for LoRa modulation and for FSK modulation.
        """
        data = "".join(f"{ord(c):02x}" for c in data)
        print(data)
        return self.send_command(f"radio tx {data} {count}")

    


    def radio_stop_reception(self):
        """
        Stop the receiver.
        """
        return self.send_command("radio rxstop")

    def radio_get_signal_noise_ratio(self):
        return self.send_command("radio get snr")

    def radio_get_packet_rssi(self):
        return self.send_command("radio get pktrssi")

    def radio_set_cw(self, state):
        """
        This command will enable or disable the CW mode on the SiP. CW mode allows the user to put the transceiver into
Transmission mode to observe the generated signal. By altering the radio settings, the user can observe the changes
in transmissions levels. 

        :param state: State of the CW mode ('on' or 'off').
"""

        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'.")
        return self.send_command(f"radio cw {state}")

    
    
    def set_listen_before_talk(self, scan_period, threshold, num_of_samples, transmit_on):
        """
            Set the Listen Before Talk (LBT) parameters.

        :param scan_period: Scan duration.
        :param threshold: RSSI threshold.
        :param num_of_samples: Number of samples.
        :param transmit_on: Whether to enable LBT-based transmission.
        """

        return self.send_command(f"radio set lbt {scan_period} {threshold} {num_of_samples} {transmit_on}")

    def get_listen_before_talk(self):
        return self.send_command("radio get lbt")


def main():
    lora = CanSat_LoRa()
    lora.find_and_open()

    print("Version:", lora.sys_get_version())
    print("Frequency:", lora.radio_get_frequency())
    print("Power:", lora.radio_get_power())
    print("Modulation:", lora.radio_get_modulation())
    print("CRC:", lora.radio_get_crc())
    print("LBT:", lora.get_listen_before_talk())
    print("SNR:", lora.radio_get_signal_noise_ratio())
    print("RSSI:", lora.radio_get_packet_rssi())
    print("PABOOST:", lora.radio_get_paboost())

    lora.radio_set_frequency_mhz(868.35)
    lora.radio_set_modulation("lora")
    lora.radio_set_paboost("on")
    lora.radio_set_power(20)

    time.sleep(1)

    print(lora.radio_transmit("Hello, world!"))

    #lora.radio_continous_reception(print)
    
    #lora.radio_continous_reception(print)




    lora.close()

if __name__ == "__main__":
    main()