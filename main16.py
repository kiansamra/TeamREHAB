"""
--------------------------------------------------------------------------
Main
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

Main

  This centralized script runs all relevant drivers of the exercise tracker to
  allow the user to turn on and operate the exercise tracker.  It allows the
  user to turn tracking on/off with a switch, perform exercises and count reps, 
  receive feedback if a rep is completed with a green LED and a live count of
  reps on a 16x2 LCD display.

"""

import time
import csv
import os
from datetime import datetime
import pytz
import urllib.parse
import numpy as np
from accelerometer_manager import AccelerometerManager
from rep_counter import RepCounter
from button import Button
from led import LED
from LCD import LCD
from googleapiclient.discovery import build
from google.oauth2 import service_account

from flask import Flask, jsonify
from flask import render_template
from flask_cors import CORS  # Add this import for CORS support
from threading import Thread
from flask import request
from googleapiclient.http import MediaFileUpload
import Adafruit_BBIO.GPIO as GPIO

#switch_pin = "P2_2"
# Define the GPIO pins for the stepper motor control
step_pin = "P2_6"  # Change to the actual pin you connected
direction_pin = "P2_8"  # Change to the actual pin you connected

# Set up GPIO pins
GPIO.setup(step_pin, GPIO.OUT)
GPIO.setup(direction_pin, GPIO.OUT)

delay = 0.00075 

def move_stepper(is_forward):
    GPIO.output(direction_pin, GPIO.HIGH if is_forward else GPIO.LOW)  # Set direction
    GPIO.output(step_pin, GPIO.HIGH)
    time.sleep(delay)
    GPIO.output(step_pin, GPIO.LOW)
    time.sleep(delay)
    
# Define the GPIO pins for the stepper motor control
step_pin2 = "P2_10"  # Change to the actual pin you connected
direction_pin2 = "P2_18"  # Change to the actual pin you connected

# Set up GPIO pins
GPIO.setup(step_pin2, GPIO.OUT)
GPIO.setup(direction_pin2, GPIO.OUT)


def move_stepper2(is_forward):
    GPIO.output(direction_pin2, GPIO.HIGH if is_forward else GPIO.LOW)  # Set direction
    GPIO.output(step_pin2, GPIO.HIGH)
    time.sleep(delay)
    GPIO.output(step_pin2, GPIO.LOW)
    time.sleep(delay)

# Define the GPIO pins for the stepper motor control
step_pin3 = "P2_20"  # Change to the actual pin you connected
direction_pin3 = "P2_22"  # Change to the actual pin you connected

# Set up GPIO pins
GPIO.setup(step_pin3, GPIO.OUT)
GPIO.setup(direction_pin3, GPIO.OUT)


import math
from bisect import bisect_left
import numpy as np

import time

# Define the constants
step_per_rev = 360 / 1.8  # Steps per revolution for 1.8-degree stepper motor
preset_values = {
    # 0: 0,
    # 5: 0.921,
    # 10: 1.414,
    # 15: 1.966
    0: 1.966,
    5: 1.414,
    10: 0.921,
    15:0
}

# Set up GPIO pins
step_pin3 = "P2_20"  # Change to the actual pin you connected
direction_pin3 = "P2_22"  # Change to the actual pin you connected

# Set up GPIO pins
GPIO.setup(step_pin3, GPIO.OUT)
GPIO.setup(direction_pin3, GPIO.OUT)

# Define the delay between steps
#delay = 0.01  # Adjust as needed

# Define global variable for current position
current_position = 0

def calculate_steps(direction):
    global current_position
    
    # Update current position based on direction
    if direction == 5:  # Moving forward
        current_position = min(current_position + 5, 15)  # Ensure position is within range
    elif direction == -5:  # Moving backward
        current_position = max(current_position - 5, 0)  # Ensure position is within range
    
    # Print current position
    print("Current Position:", current_position)
    
    # Find the next and previous preset positions based on the updated current position
    if direction == 5:
        next_position = next((pos for pos in sorted(preset_values.keys()) if pos > current_position), None)
        prev_position = next((pos for pos in sorted(preset_values.keys(), reverse=True) if pos < current_position), None)
    elif direction == -5:
        next_position = next((pos for pos in sorted(preset_values.keys(), reverse=True) if pos < current_position), None)
        prev_position = next((pos for pos in sorted(preset_values.keys()) if pos > current_position), None)
    
     # Determine the actual next position based on direction
    if direction == 5:
        next_position = next_position if next_position is not None else prev_position
    elif direction == -5:
        next_position = prev_position if prev_position is not None else next_position
    
    # Print next and previous positions
    print("Next Position:", next_position)
    print("Previous Position:", prev_position)
    
    # Calculate steps needed to move to the next preset position
    if next_position is not None:
        angle_change = abs(preset_values[current_position] - preset_values[prev_position])
        print("Angle Change:", angle_change)
        steps = int(round(angle_change * step_per_rev / (2 * math.pi)))
        print("Steps to move:", steps)
        return steps
    else:
        return 0  # No next preset position, return 0 steps (stay at current position)


# Move the stepper motor
def move_stepper3(is_right):
    delay = 0.01
    y_movement = 5 if is_right else -5  # 5 pounds per button click
    steps = calculate_steps(y_movement)
    
    # Determine direction
    direction = GPIO.HIGH if is_right else GPIO.LOW
    
    # Move the stepper motor
    GPIO.output(direction_pin3, direction)
    for _ in range(steps):
        GPIO.output(step_pin3, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin3, GPIO.LOW)
        time.sleep(delay)


#switch = Button(switch_pin)
#prev_switch_state = False

slider_value = 0
slider_value2 = 0
slider_value3 = 0

folder_id = "Please Create A New Session"

app = Flask(__name__, template_folder='templates')
#CORS(app)  # Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})


import random

# Add a function to generate a random session ID
def generate_random_session_id():
    return ''.join(random.choices('0123456789abcdef', k=6))
    

tracking_enabled = False

def get_or_generate_session_id():
    session_id = request.cookies.get('session_id')
    if session_id is None:
        session_id = generate_random_session_id()
    return session_id

sets_list = []

# Add a new route to handle slider value updates
@app.route('/api/update_slider_value', methods=['POST'])
def update_slider_value():
    global slider_value
    data = request.get_json()
    slider_value = data.get('sliderDirection', '')

    return jsonify({'success': True})

@app.route('/api/update_slider_value2', methods=['POST'])
def update_slider_value2():
    global slider_value2
    data = request.get_json()
    slider_value2 = data.get('sliderDirection', '')

    return jsonify({'success': True})
    
@app.route('/api/move_stepper3', methods=['POST'])
def move_stepper3_route():
    data = request.get_json()
    is_right = data.get('direction', True)  # Default direction is right
    move_stepper3(is_right)
    return jsonify({'success': True})

@app.route('/api/update_sets_list', methods=['POST'])
def update_sets_list():
    global sets_list
    data = request.get_json()
    set_item = data.get('set', '')
    sets_list.append(set_item)
    return jsonify({'success': True})

@app.route('/api/new_session', methods=['POST'])
def new_session_api():
    global sets_list
    # Generate a new session ID
    new_session_id = generate_random_session_id()
    sets_list = []  # Reset the sets list for the new session
    
    # Create a folder in Google Drive for the new session
    folder_name = f"session_{new_session_id}"
    folder_id = create_drive_folder(folder_name)
    
    return jsonify({'success': True, 'newSessionId': new_session_id, 'folderId': folder_id})

def create_drive_folder(folder_name):
    global folder_id
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [PARENT_FOLDER_ID]
    }

    folder = service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    folder_id = folder.get('id')
    print(f'Folder "{folder_name}" created in Google Drive with ID: {folder_id}')

    return folder_id

@app.route('/')
def home():
    session_id = get_or_generate_session_id()
    return render_template('index.html', session_id=session_id, sets_list=sets_list)

# Add a new route to get the list of sets
@app.route('/api/get_sets_list')
def get_sets_list():
    return jsonify({'sets_list': sets_list})

# Add a new route to start and stop tracking
@app.route('/api/start_tracking', methods=['POST'])
def start_tracking_api():
    global tracking_enabled
    global current_exercise_type
    tracking_enabled = True
    
    # Get the exercise type from the request body
    data = request.get_json()
    current_exercise_type = data.get('exerciseType', 'Unknown')

    return jsonify({'success': True, 'exerciseType': current_exercise_type})

current_set_number = 0

@app.route('/api/stop_tracking', methods=['GET'])
def stop_tracking_api():
    global tracking_enabled
    global current_set_number

    tracking_enabled = False
    current_set_number += 1
    return jsonify({'success': True, 'setNumber': current_set_number, 'reps': prev_reps})


@app.route('/api/get_rep_count')
def get_rep_count():
    global prev_reps  # Use the global prev_reps
    return jsonify({'rep_count': prev_reps})


SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'
PARENT_FOLDER_ID = "1wmeP5BNGQ41lYpDJBq1olm2QznSOJVGp"

def authenticate():
    creds = None

    # Load the credentials from the file if available
    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    except FileNotFoundError:
        print("Service account file not found.")

    # If credentials are expired, refresh them
    if creds and creds.expired:
        try:
            creds.refresh(Request())
            print("Credentials refreshed successfully.")
        except Exception as e:
            print(f"Error refreshing credentials: {e}")

    return creds
    
def upload_file(file_path, filename, folder_id):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': urllib.parse.quote(filename),
        'parents': [folder_id]
    }

    media = MediaFileUpload(file_path, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media
    ).execute()

def save_session_info(session_start_time, session_end_time, total_reps, folder_id):
    # Convert to your local timezone (CST)
    cst = pytz.timezone('America/Chicago')
    session_start_time = session_start_time.astimezone(cst)
    session_end_time = session_end_time.astimezone(cst)

    session_length = session_end_time - session_start_time
    session_length_seconds = int(session_length.total_seconds())
    session_length_minutes = session_length_seconds // 60
    session_length_seconds = session_length_seconds % 60

    session_info = {
        'Session Start Time': session_start_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        'Session End Time': session_end_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        'Session Length (minutes:seconds)': f'{session_length_minutes}:{session_length_seconds}',
        'Total Repetitions': total_reps,
        'Resistance (lbs)': current_position,
        'Exercise Type': current_exercise_type
    }

    # Get a formatted string of the session start time to include in the file name
    formatted_start_time = session_start_time.strftime("%Y%m%d_%H%M%S")

    # Construct the file name with the formatted start time
    session_file_name = f'{formatted_start_time}_session_info.csv'

    with open(session_file_name, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=session_info.keys())
        writer.writeheader()
        writer.writerow(session_info)

    print(f'folder id: {folder_id}')
    # Upload the session info to Google Drive with the constructed file name
    upload_file(session_file_name, session_file_name, folder_id)
    print(f'Session info uploaded')

    # Delete the local session info file
    os.remove(session_file_name)
    print(f'Session info locally deleted')

def save_accel_data(accel_data, session_start_time, folder_id):
    # Get a formatted string of the session start time to include in the file name
    formatted_start_time = session_start_time.strftime("%Y%m%d_%H%M%S")

    # Construct the file name with the formatted start time
    accel_file_name = f'{formatted_start_time}_accel_data.csv'

    with open(accel_file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['X', 'Y', 'Z'])  # Write header

        for data_point in accel_data:
            writer.writerow(data_point)

    # Upload the accelerometer data to Google Drive with the constructed file name
    upload_file(accel_file_name, accel_file_name, folder_id)
    print(f'Accelerometer data uploaded')

    # Delete the local accelerometer data file
    os.remove(accel_file_name)
    print(f'Accelerometer data locally deleted')

# ... (previous code)

def run_flask_app():
    app.run(debug=True, host='0.0.0.0', port=8001, use_reloader=False)
    #app.run(debug=True, host='192.168.7.2', port=8001, use_reloader=False)



prev_reps = 0
def main():
    global prev_reps
    global tracking_enabled
    global folder_id
    global switch
    global prev_switch_state
    global slider_value
    
    rep_counter = RepCounter(threshold_multiplier=0.65)
    accel_manager = AccelerometerManager(bus_number=1, device_address=0x68)
    accel_manager.initialize()
    led = LED("P2_4")
    #lcd = LCD("P2_18", "P2_10", "P2_6", "P2_8", "P1_4", "P1_2", 16, 2)

    accel_data = []
    session_start_time = None

    # Start the Flask app in a separate thread
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()

    while True:
        #switch_state = switch.is_pressed()

        # if switch_state:
        #     print("Switch pressed. Moving stepper forward.")
        #     move_stepper(True)  # Move in one direction when switch is pressed
        # else:
        #     print("Switch released. Moving stepper backward.")
        #     move_stepper(False)  # Move in the opposite direction when switch is released

        # if switch_state != prev_switch_state:
        #     prev_switch_state = switch_state  # Update prev_switch_state here
        #     print(f"switch changed")
            
        # Move the stepper motor based on the slider value
        if slider_value == 'right':
            move_stepper(True)  # Move forward
        elif slider_value == 'left':
            move_stepper(False)  # Move backward
        if slider_value2 == 'right':
            move_stepper2(True)  # Move forward
        elif slider_value2 == 'left':
            move_stepper2(False)  # Move backward
        if slider_value3 == 'right':
            move_stepper3(True)  # Move forward
        elif slider_value3 == 'left':
            move_stepper3(False)  # Move backward
        
        
        if tracking_enabled:
            x, y, z = accel_manager.readData()
            accel_data.append([x, y, z])

            result = rep_counter.process_data(np.array(accel_data))
            accel_magnitude = result['accel_magnitude']
            counting_periods = result['counting_periods']
            activity_counts = result['activity_counts']

            if session_start_time is None:
                session_start_time = datetime.now()

            if activity_counts > prev_reps:
                prev_reps = activity_counts
                led.on()
                print(f'Total Repetitions: {activity_counts}')
                time.sleep(0.5)
                led.off()

            time.sleep(0.005)  # 100Hz
        else:
            #print(f'tracking disabled')
            if session_start_time is not None:
                session_end_time = datetime.now()
                save_session_info(session_start_time, session_end_time, prev_reps, folder_id)
                save_accel_data(accel_data, session_start_time, folder_id)
                session_start_time = None  # Reset session_start_time for the next session

                # Reset accel_data after saving
                accel_data = []

            rep_counter = RepCounter(threshold_multiplier=0.65)
            led.off()
            prev_reps = 0
            #time.sleep(1)  # Add a delay to prevent multiple session saves

if __name__ == "__main__":
    main()