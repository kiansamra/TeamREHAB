"""
--------------------------------------------------------------------------
Rep Counter
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

Rep Counter

  This driver analyzes x,y,z accelerometer data to determine when a user has
  performed a repetition (rep) of an exercise.
  
Software API

    __init__(threshold_multiplier)
        - Sets threshold multiplier as given input value (default = 0.6)
        - This is currently not being utilized but can be to have rep
        detection cutoff to be based on gathered data instead of a hard-coded
        value
        
    process_data(accel_data)
      - Takes x,y,z acclerometer data and processes it to find peaks of
      acceleration magnitude
      - Acceleration magnitude peaks above defined threshold are counted as
      reps
    

"""
import numpy as np
from scipy.signal import butter, lfilter

class RepCounter:
    def __init__(self, threshold_multiplier=0.6):
        self.threshold_multiplier = threshold_multiplier
        self.refractory_period = 0.3  # in seconds
        self.threshold_fraction = 1.7 / 3  # two-thirds of the range
        self.time_interval = 0.01  # time interval between rows in seconds
        self.hardcoded_threshold = 3400  # new hardcoded threshold value
        self.first_crossed = False  # flag to track the first crossing

        # Initialize variables
        self.activity_counts = 0
        self.last_crossing_time = -int(self.refractory_period / self.time_interval)
        self.counting_periods = []
        self.threshold = self.hardcoded_threshold

    def butterworth_filter(self, data):
        # Apply a Butterworth filter (low-pass filter)
        order = 1
        fs = 1.0  # Assuming a normalized frequency
        cutoff_frequency = 0.1  # Adjust as needed

        # Corrected the division operation
        Wn = 2 * cutoff_frequency / fs

        b, a = butter(order, Wn, btype='low')
        filtered_data = lfilter(b, a, data)
        return filtered_data

    def process_data(self, accel_data):
        # Step 1: Preprocess the Data
        accel_magnitude_z_normalized = np.abs(accel_data[:, 2] - 8300)  # Normalized z-axis accelerometer data

        # Apply a Butterworth filter
        accel_magnitude_z_normalized = self.butterworth_filter(accel_magnitude_z_normalized)

        # Set the initial hardcoded threshold value
        self.threshold = self.hardcoded_threshold

        # Initialize variables
        self.activity_counts = 0
        self.last_crossing_time = -int(self.refractory_period / self.time_interval)
        self.counting_periods = []
        self.first_crossed = False  # Add a flag to track the first crossing
        
        # Step 2: Threshold Crossing Technique
        for i in range(1, len(accel_magnitude_z_normalized)):
            if accel_magnitude_z_normalized[i - 1] < self.threshold <= accel_magnitude_z_normalized[i]:
                # Check refractory period using row index
                row_diff = i - self.last_crossing_time
                if row_diff > int(self.refractory_period / self.time_interval):
                    self.activity_counts += 1
                    self.last_crossing_time = i
                    self.counting_periods.append((i-1, i))
        
                    # Change the threshold after crossing 4000 and if it's the first crossing
                    if accel_magnitude_z_normalized[i] > self.threshold and self.threshold <= self.hardcoded_threshold and not self.first_crossed:
                        self.threshold = np.min(accel_magnitude_z_normalized) + self.threshold_fraction * (np.max(accel_magnitude_z_normalized) - np.min(accel_magnitude_z_normalized))
                        self.first_crossed = True  # Set the flag to True after the first crossing
        
        # Move the threshold print statement outside the loop
        #print(f"threshold: {self.threshold}")
        #print(f"magnitude: {accel_magnitude_z_normalized[-1]}") 
                

        # Return the results in a dictionary
        return {
            'accel_magnitude': accel_magnitude_z_normalized,
            'counting_periods': self.counting_periods,
            'activity_counts': self.activity_counts
        }
