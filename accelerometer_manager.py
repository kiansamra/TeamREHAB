"""
--------------------------------------------------------------------------
Accelerometer Manager
--------------------------------------------------------------------------
License:   
Copyright 2021-2023 - Kian Samra

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this 
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors 
may be used to endorse or promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------

Accelerometer Manager

  This driver is built for an MPU-6050 accelerometer to initialize the
  accelerometer and allow it to gather acceleration data at 100hz
  
Software API

    __init__(bus_number, device_address)
        - Sets bus number and device address as the provided input values
        
    initialize()
      - Initializes MPU-6050 accelerometer and gyroscope
      - Prints confirmation statement to verify initialization
      
    readData()
      - Reads data from MPU-6050 accelerometer
      - Outputs x, y, and z accelerometer data as x,y,z
    

"""

import smbus2
import time
import csv

class AccelerometerManager:
    address = None
    bus = None
    
    def __init__(self, bus_number, device_address):
        self.bus = smbus2.SMBus(bus_number)
        self.address = device_address

    def initialize(self):
        # Power Management 1 Register
        self.bus.write_byte_data(self.address, 0x6B, 0x00)  # Set to 0 for normal operation

        # Configuration Register - Gyroscope Configuration
        self.bus.write_byte_data(self.address, 0x1B, 0x08)  # Set to 0x08 for +/- 500 degrees/second

        # Configuration Register - Accelerometer Configuration
        self.bus.write_byte_data(self.address, 0x1C, 0x08)  # Set to 0x08 for +/- 4g

        # Sample Rate Divider
        self.bus.write_byte_data(self.address, 0x19, 0x07)  # Set to 7 for a sample rate of 1kHz

        # Enable I2C bypass for external magnetometer (if used)
        # self.bus.write_byte_data(self.address, 0x37, 0x02)  # Uncomment this line if you have an external magnetometer

        # You may need to add more initialization steps based on your specific IMU's datasheet

        print("Accelerometer initialized successfully.")

    def readData(self):
        # Read the accelerometer data
        data = self.bus.read_i2c_block_data(self.address, 0x3B, 6)

        # Assuming the data is in 16-bit two's complement format
        x = (data[0] << 8) | data[1]
        y = (data[2] << 8) | data[3]
        z = (data[4] << 8) | data[5]

        # Convert to signed value if necessary (e.g., for 16-bit signed data)
        if x > 32767:
            x -= 65536
        if y > 32767:
            y -= 65536
        if z > 32767:
            z -= 65536

        return x, y, z
