"""
Copyright (c) 2021-2024 LAAS-CNRS

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Lesser General Public License as published by
  the Free Software Foundation, either version 2.1 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: LGPL-2.1
"""

"""
@brief  file containing version to communicate with twist.

@author thomas.walter@laas.fr
"""


#Python modules import
import time, serial

class Twist_Device:
    def __init__(self, twist_port, baudrate = 115200, bytesize = 8, parity = "N", stopbits = 1, timeout_sec = 2, product_id = 0x0100, vendor_id = 0x2fe3):

        self.twist_serialObj = serial.Serial(port = twist_port)
        self.CommPortDescWithoutPort = "TWIST"
        self.baudRate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.Timeout_s = timeout_sec
        self.twist_pid = product_id
        self.twist_vid = vendor_id

        self.twist_serialObj.baudrate = baudrate
        self.twist_serialObj.bytesize = bytesize
        self.twist_serialObj.parity = parity
        self.twist_serialObj.stopbits = stopbits
        self.twist_serialObj.timeout = timeout_sec


        self.twist_message_index = {"D1": {"index": 0},
                                    "V1": {"index": 1},
                                    "I1": {"index": 2},
                                    "M1": {"index": 3},
                                    "D2": {"index": 4},
                                    "I2": {"index": 5},
                                    "V2": {"index": 6},
                                    "M2": {"index": 7},
                                    "VH": {"index": 8},
                                    "IH": {"index": 9},
                                    "AN": {"index": 10},
                                    "CE": {"index": 11},
                                    "CR": {"index": 12},
                                    "RS": {"index": 13}}


    def setSerialPort(self, port):
        self.CommPort = port

    def setVendorID(self, vendor_id):
        self.twist_pid = vendor_id

    def setProductID(self, product_id):
        self.twist_vid = product_id

    def getSerialObjID(self):
        return self.twist_serialObj


    def sendMessage(self,Message):
        """
        Send a message via serial communication.

        Args:
            SerialObj: The serial object used for communication.
            Message (str): The message to be sent.

        Returns:
            None
        """
        # Define the chunk size
        chunk_size = 10

        # Calculate the number of chunks
        num_chunks = (len(Message) + chunk_size - 1) // chunk_size

        # Send each chunk
        for i in range(num_chunks):
            # Calculate the start and end indices for the current chunk
            start_index = i * chunk_size
            end_index = min((i + 1) * chunk_size, len(Message))

            # Extract the current chunk
            chunk = Message[start_index:end_index]

            # Send the chunk via serial
            self.twist_serialObj.write(chunk.encode('utf-8'))

            # Wait for a short period
            time.sleep(0.1)

        # Send the end of line
        self.twist_serialObj.write(b'\r\n')


    def getMeasurement(self, measurement_type):
        """
        Retrieves the TWIST measurement value based on the measurement type.
        This MUST be called when the Twist is in POWER ON

        Parameters:
            - self: Instance of the class containing the measurement methods.
            - measurement_type (str): Type of measurement to retrieve.
              Supported types are 'V1', 'V2', 'VH', 'I1', 'I2', 'IH', 'M1', 'M2','CT'.

        Returns:
            - Measurement value corresponding to the specified measurement type.

        Raises:
            - ValueError: If an invalid measurement type is provided.
        """
        if measurement_type not in self.twist_message_index:
            raise ValueError("Invalid measurement type. Supported types are 'V1', 'V2', 'VH', 'I1', 'I2', 'IH', 'M1', 'M2','CT'.")

        # time.sleep(self.short_delay)
        index_meas = self.twist_message_index[measurement_type]["index"]

        self.twist_serialObj.reset_input_buffer()

        size_check = False
        while size_check == False:
            reading = self.get_TWIST_line()
            reading = [elem.replace('{', '').replace('}', '') for elem in reading] #eliminates curly brackets from the message
            if len(reading) == 14 : size_check = True               #14 is the length of the communication buffer

        return float(reading[index_meas])

    def getLine(self, split_character = ':'):
        """
        Retrieves the next serial line from the TWIST in the buffer and split it along the current characters.

        Parameters:
            - self: Instance of the class containing the measurement methods.
            - split_character: The character to be used to split the line. By default it is ':'.

        Returns:
            - The whole line split along the character.
        """
        reading = self.twist_serialObj.readline().decode('utf-8').split(split_character)

        return reading


    def sendCommand(self, action, *args, delay=0.2):
        """
        Generate and send a message to the Twist board based on the specified action and optional parameters.

        This method generates a message for the Twist board based on the provided action and optional arguments,
        and sends it via serial communication.

        Args:
            action (str): The action to perform. Supported actions include:
                - "IDLE": Puts the Twist board into an idle state.
                - "POWER_OFF": Turns off power to the Twist board.
                - "POWER_ON": Turns on power to the Twist board.
                - "LEG": Controls the state of a leg on the Twist board.
                - "CAPA": Controls the state of a capacitor on the Twist board.
                - "DRIVER": Controls the state of a driver on the Twist board.
                - "BUCK": Controls the state of a buck converter on the Twist board.
                - "BOOST": Controls the state of a boost converter on the Twist board.
                - "REFERENCE": Sets the reference value for a specific variable on the Twist board.
                - "DUTY": Sets the duty cycle value for a specific leg on the Twist board.
                - "CALIBRATE": Calibrates a specific variable on the Twist board.
            *args: Optional arguments corresponding to the action.
            delay (float, optional): The delay (in seconds) after sending the command. Default is 0.2 seconds.

        Returns:
            str: The generated message sent to the Twist board.

        Raises:
            ValueError: If an invalid action is provided.

        Example:
            To set leg A to ON:
            >>> sendCommand("LEG", "A", "ON")
        """

        action_types = ("LEG", "CAPA", "DRIVER", "BUCK", "BOOST", "REFERENCE", "DUTY", "PHASE_SHIFT", "DEAD_TIME_RISING", "DEAD_TIME_FALLING", "CALIBRATE")

        message_formats = {
            "IDLE": "d_i",
            "POWER_OFF": "d_f",
            "POWER_ON": "d_o",
            "LEG": lambda leg, state: f"s_{leg.upper()}_l_{state.lower()}",
            "CAPA": lambda leg, state: f"s_{leg.upper()}_c_{state.lower()}",
            "DRIVER": lambda leg, state: f"s_{leg.upper()}_v_{state.lower()}",
            "BUCK": lambda leg, state: f"s_{leg.upper()}_b_{state.lower()}",
            "BOOST": lambda leg, state: f"s_{leg.upper()}_t_{state.lower()}",
            "REFERENCE": lambda leg, variable, value: f"s_{leg.upper()}_r_{variable.upper()}_{value:.5f}",
            "PHASE_SHIFT": lambda leg, value: f"s_{leg.upper()}_p_.{value}",
            "DEAD_TIME_RISING": lambda leg, value: f"s_{leg.upper()}_x_.{value}",
            "DEAD_TIME_FALLING": lambda leg, value: f"s_{leg.upper()}_z_.{value}",
            "DUTY": lambda leg, value: f"s_{leg.upper()}_d_{value:.5f}",
            "CALIBRATE": lambda variable, gain, offset: f"k_{variable.upper()}_g_{gain:.8f}_o_{offset:.8f}",
            }

        # Check if action is valid
        if action not in message_formats:
            raise ValueError(f"Invalid action: {action}")

        # Generate message based on action and arguments
        message = message_formats[action](*args) if action in action_types else message_formats[action]

        # Send the generated message via serial communication
        self.sendMessage(message)
        time.sleep(delay)

        return message
