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
        if self.serial:
            self.serial.close()

    def get_ports(self):
        """ 
        Get a list of available serial ports.
        """
        return sorted(serial.tools.list_ports.comports())

    def send_command(self, command):
        """
        Send a command to the LoRa module and return the response.

        :param command: Command string to send.
        :return: Response string from the module.
        """
        full_command = f"{command}\r\n"
        self.serial.write(full_command.encode())
        time.sleep(0.1)
        return self.serial.read_all().decode().strip()

    # System Commands
    def sys_reset(self):
        """Resets and restarts the module."""
        return self.send_command("sys reset")

    def sys_sleep(self, mode, duration):
        """
        Puts the system in sleep for a finite number of milliseconds.

        :param mode: Sleep mode ('standby' or 'backup').
        :param duration: Sleep duration in milliseconds. The minimum sleep time is 1000 ms.
        """
        if mode not in ["standby", "backup"]:
            raise ValueError("Mode must be 'standby' or 'backup'.")
        if duration < 1000:
            raise ValueError("Duration must be at least 1000 ms.")

        return self.send_command(f"sys sleep {mode} {duration}")

    def sys_factory_reset(self):
        """Resets the module to factory default values."""
        return self.send_command("sys factoryRESET")

    def sys_get_version(self):
        """Returns hardware and firmware version information."""
        return self.send_command("sys get ver")

    # Transceiver Commands
    def radio_set_frequency(self, frequency):
        """
        Changes the communication frequency of the radio transceiver.

        :param frequency: Frequency in Hz.
        """
        if not (137_000_000 <= frequency <= 175_000_000 or \
                410_000_000 <= frequency <= 525_000_000 or \
                862_000_000 <= frequency <= 1_020_000_000):
            raise ValueError("Frequency out of range.")
        return self.send_command(f"radio set freq {frequency}")

    def radio_set_frequency_mhz(self, frequency_mhz):
        """
        Changes the communication frequency in MHz.

        :param frequency_mhz: Frequency in MHz.
        """
        frequency_hz = int(frequency_mhz * 1_000_000)
        return self.radio_set_frequency(frequency_hz)

    def radio_set_paboost(self, state):
        """
        Enables or disables the PABOOST.

        :param state: 'on' or 'off'.
        """
        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'.")
        return self.send_command(f"radio set pa {state}")

    def radio_set_power(self, power):
        """
        Sets the transceiver output power.

        :param power: Power level (-4 to 20).
        """
        if not (-4 <= power <= 20):
            raise ValueError("Power level must be between -4 and 20.")
        return self.send_command(f"radio set pwr {power}")

    def radio_set_modulation(self, mode):
        """
        Sets the modulation method ('lora' or 'fsk').

        :param mode: Modulation mode.
        """
        if mode not in ["lora", "fsk"]:
            raise ValueError("Mode must be 'lora' or 'fsk'.")
        return self.send_command(f"radio set mod {mode}")

    def radio_set_crc(self, state):
        """
        Enables or disables the CRC header.

        :param state: 'on' or 'off'.
        """
        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'.")
        return self.send_command(f"radio set crc {state}")

    def radio_get_crc(self):
        """Returns the current CRC header state."""
        return self.send_command("radio get crc")

    def radio_get_modulation(self):
        """Returns the current modulation mode."""
        return self.send_command("radio get mod")

    def radio_get_frequency(self):
        """Returns the current frequency in Hz."""
        return self.send_command("radio get freq")

    def radio_get_frequency_mhz(self):
        """Returns the current frequency in MHz."""
        return int(self.radio_get_frequency()) / 1_000_000

    def radio_get_power(self):
        """Returns the current power level."""
        return self.send_command("radio get pwr")

    def radio_get_paboost(self):
        """Returns the current state of the PABOOST."""
        return self.send_command("radio get pa")


    def radio_continuous_reception(self, callback):
        """
        Miau! Végtelen ciklus!

        Starts continuous reception and calls the callback function when a packet is received.

        :param callback: Function to call on packet reception.
        """
        self.send_command("radio rx 0")
        while True:
            response = self.serial.readline().decode().strip()
            if response.startswith("radio_rx"):
                data = bytes.fromhex(response.split(" ")[1]).decode()
                callback(data)

    def radio_transmit(self, data, count=1):
        """
        Transmits data using the radio.

        :param data: Data to transmit.
        :param count: Number of transmissions.
        """
        hex_data = "".join(f"{ord(c):02x}" for c in data)
        return self.send_command(f"radio tx {hex_data} {count}")

    def radio_stop_reception(self):
        """Stops the receiver."""
        return self.send_command("radio rxstop")

    def radio_get_signal_noise_ratio(self):
        """Returns the Signal-to-Noise Ratio (SNR)."""
        return self.send_command("radio get snr")

    def radio_get_packet_rssi(self):
        """Returns the Received Signal Strength Indicator (RSSI) of the last packet."""
        return self.send_command("radio get pktrssi")

    def radio_set_cw(self, state):
        """
        Enables or disables Continuous Wave (CW) mode.

        :param state: 'on' or 'off'.
        """
        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'.")
        return self.send_command(f"radio cw {state}")

    def set_listen_before_talk(self, scan_period, threshold, num_of_samples, transmit_on):
        """
        Sets Listen Before Talk (LBT) parameters.

        :param scan_period: Scan duration.
        :param threshold: RSSI threshold.
        :param num_of_samples: Number of samples.
        :param transmit_on: Whether to enable LBT-based transmission.
        """
        return self.send_command(f"radio set lbt {scan_period} {threshold} {num_of_samples} {int(transmit_on)}")

    def get_listen_before_talk(self):
        """Returns the current LBT settings."""
        return self.send_command("radio get lbt")

    def radio_set_sf(self, spreading_factor):
        """
        Sets the spreading factor.

        :param spreading_factor: Spreading factor (7 to 12).
        """
        if not (7 <= spreading_factor <= 12):
            raise ValueError("Spreading factor must be between 7 and 12.")
        return self.send_command(f"radio set sf sf{spreading_factor}")

    def radio_get_sf(self):
        """Returns the current spreading factor."""
        return self.send_command("radio get sf")
    
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
    print("SF:", lora.radio_get_sf())

    lora.radio_set_frequency_mhz(868.35)
    lora.radio_set_modulation("lora")
    lora.radio_set_paboost("on")
    lora.radio_set_power(20)

    time.sleep(1)

    print(lora.radio_transmit("Hello, world!"))

    lora.close()

if __name__ == "__main__":
    main()
