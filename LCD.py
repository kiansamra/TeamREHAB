# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
HT16K33 I2C Library
--------------------------------------------------------------------------
License:   
Copyright 2018-2023 Kian Samra

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
Software API:

LCD(rs, enable, d4, d5, d6, d7, cols, rows)
- Provide GPIO pin for the register select bus
- Provide GPIO pin for the enable bus
- Provide GPIO pins for the four data buses
    (Note: LCD will only be used in 4-bit mode)
- Provide the number of columns to be used (1 to 16)
-Provide the number of rows to be used (1 to 2)
clear()
- Removes all the data from the lcd and sets the cursor position to 0

print(data)
- Prints the data entered onto the lcd

setCursor(column,row)
- Sets the cursor position to the specified row and column
- stores the cursor position so it can be retrieved

getCursor()
- gets the current cursor position

--------------------------------------------------------------------------
Sof



Background Information: 
 
  * Using Hitachi's HD44780U 16x2 LCD Display:
    * https://www.digikey.com/en/htmldatasheets/production/1542762/0/0/1/hd44780u-lcd-ii-.html
    
    * Base code (adapted below):
        * https://github.com/pimylifeup/Adafruit_Python_CharLCD/blob/master/Adafruit_CharLCD/Adafruit_CharLCD.py

    * =Characters Supported from:
        * https://www.digikey.com/en/htmldatasheets/production/1542762/0/0/1/hd44780u-lcd-ii-.html
        
"""
import Adafruit_BBIO.GPIO as GPIO
import time

# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

#Commands
LCD_CLEARDISPLAY        = 0x01
LCD_RETURNHOME          = 0x02
LCD_ENTRYMODESET        = 0x04
LCD_DISPLAYCONTROL      = 0x08
LCD_CURSORSHIFT         = 0x10
LCD_FUNCTIONSET         = 0x20
LCD_SETCGRAMADDR        = 0x40
LCD_SETDDRAMADDR        = 0x80

# Entry flags
LCD_ENTRYRIGHT          = 0x00
LCD_ENTRYLEFT           = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

LCD_DISPLAYON           = 0x04
LCD_DISPLAYOFF          = 0x00
LCD_CURSORON            = 0x02
LCD_CURSOROFF           = 0x00
LCD_BLINKON             = 0x01
LCD_BLINKOFF            = 0x00

LCD_DISPLAYMOVE         = 0x08
LCD_CURSORMOVE          = 0x00
LCD_MOVERIGHT           = 0x04
LCD_MOVELEFT            = 0x00

#Sets Function set to 4-bit mode

LCD_8BITMODE            = 0x10
LCD_4BITMODE            = 0x00
LCD_2LINE               = 0x08
LCD_1LINE               = 0x00
LCD_5x10DOTS            = 0x04
LCD_5x8DOTS             = 0x00

#Offsets LCD up to 2 rows
LCD_ROW_OFFSETS         = (0x00, 0x40)

LCD_COL_SPACE = 2

# ------------------------------------------------------------------------
# Functions / Classes
# ------------------------------------------------------------------------
class LCD():
    """Class to control HD44780U 16x2 LCD display"""
    
    # Class variables
    rs = None
    enable = None
    d4 = None
    d5 = None
    d6 = None
    d7 = None
    cursor_position = (0,0)
    def __init__(self, rs, enable, d4,d5,d6,d7, cols, rows):
        #
        #stores the user inputted parameters about the lcd
        self._cols = cols
        self._rows = rows
        self._rs = rs
        self._enable = enable
        self._d4 = d4
        self._d5 = d5
        self._d6 = d6
        self._d7 = d7
        
        self.setup()
        #initializes display
        self.write8(0x33)
        self.write8(0x32)
        
        #initialize display control function and mode
        self.displaycontrol =  LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.displayfunction = LCD_4BITMODE | LCD_1LINE | LCD_2LINE | LCD_5x8DOTS
        self.displaymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        
        # Write registers.
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write8(LCD_FUNCTIONSET | self.displayfunction)
        self.write8(LCD_ENTRYMODESET | self.displaymode)  # set the entry mode
        self.clear()
        
        #initializes the cursor position
        self.cursor_position = (0,0)
    def setup(self):
        #set the pins as output
        for pin in (self._rs, self._enable, self._d4, self._d5, self._d6, self._d7):
            GPIO.setup(pin, GPIO.OUT)
        
    def clear(self):
        """clears the LCD display"""
        self.write8(LCD_CLEARDISPLAY) #command to clear display
        self._delay_microseconds(3000)
        
        
    def setCursor(self, col, row):
        """Move the cursor to an explicit column and row position."""
        # ensures row and column are within the bounds of the lcd display
        if row >= self._rows:
           row = self._rows - 1
        
        if row < 0:
            row = 0
        
        if col >= self._cols:
            row = self._cols - 1
        
        if col < 0:
            col = 0
            
        # Set location.
        self.write8(LCD_SETDDRAMADDR | (col + LCD_ROW_OFFSETS[row]))
        
        #get location
        self.cursor_position = (col,row)
    
    def scroll_left(self):
        row = self.cursor_position[1]
        """Moves the cursor two positions to the left"""
        if self.cursor_position[0] == 0:
            col = 0
        else:
            col = self.cursor_position[0] - LCD_COL_SPACE
        # Set location.
        self.write8(LCD_SETDDRAMADDR | (col + LCD_ROW_OFFSETS[self.cursor_position[1]]))

        #get location
        self.cursor_position = (col,row)
        print(self.cursor_position)
    
    def scroll_right(self):
        row = self.cursor_position[1]
        """Moves the cursor two positions to the right"""
        if self.cursor_position[0] >= self._cols - LCD_COL_SPACE:
            col = self._cols - LCD_COL_SPACE
        else:
            col = self.cursor_position[0] + LCD_COL_SPACE
        # Set location.
        self.write8(LCD_SETDDRAMADDR | (col + LCD_ROW_OFFSETS[self.cursor_position[1]]))
        #get location
        self.cursor_position = (col,row)
        print(self.cursor_position)
        
    def get_cursor(self):
        """Gets the current cursor position"""
        return self.cursor_position
        
        
    def show_cursor(self, show):
        """Show or hide the cursor.  Cursor is shown if show is True."""
        if show:
            self.displaycontrol |= LCD_CURSORON
        else:
            self.displaycontrol &= ~LCD_CURSORON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)
        
    def enable_display(self, enable):
        """Enable or disable the display.  Set enable to True to enable."""
        if enable:
            self.displaycontrol |= LCD_DISPLAYON
        else:
            self.displaycontrol &= ~LCD_DISPLAYON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)
    
    
    def move_left(self):
        """Move display left one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVELEFT)

    def move_right(self):
        """Move display right one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVERIGHT)
    
    def message(self, text):
        """Write text to display.  Note that text can include newlines."""
        row = 0
        # Iterate through each character.
        for char in text:
            # Advance to next row if character is a new row.
            if char == '\n':
                row += 1
                col = 0
                self.set_cursor(col, row)
            # Write the character to the display.
            else:
                self.write8(ord(char), True)
    
    def flash(self, text,col,row):
        """flashes the text on the display"""
        while True:
            self.setCursor(col,row)
            self.message(textcd )
            time.sleep(2)
            self.setCursor(col,row)
            self.message("")
    
    def endFlash(self,text,col,row):
        """stops flashing the text"""
        self.setCursor(col,row)
        self.message(text)
        
        
    def write8(self, value, char_mode=False):
        """Write 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        """
        # One millisecond delay to prevent writing too quickly.
        self._delay_microseconds(1000)
        # Set character / data bit.
        GPIO.output(self._rs, char_mode)
        # Write upper 4 bits.
        GPIO.output(self._d4, ((value >> 4) & 1) > 0)
        GPIO.output(self._d5, ((value >> 5) & 1) > 0)
        GPIO.output(self._d6, ((value >> 6) & 1) > 0)
        GPIO.output(self._d7, ((value >> 7) & 1) > 0)
        
        self._pulse_enable()
        # Write lower 4 bits.
        GPIO.output(self._d4, (value  & 1) > 0)
        GPIO.output(self._d5, ((value >> 1) & 1) > 0)
        GPIO.output(self._d6, ((value >> 2) & 1) > 0)
        GPIO.output(self._d7, ((value >> 3) & 1) > 0)
        
        self._pulse_enable()
    
    def _delay_microseconds(self, microseconds):
        # Busy wait in loop because delays are generally very short (few microseconds).
        end = time.time() + (microseconds/1000000.0)
        while time.time() < end:
            pass

    def _pulse_enable(self):
        # Pulse the clock enable line off, on, off to send command.
        GPIO.output(self._enable, False)
        self._delay_microseconds(1)       # 1 microsecond pause - enable pulse must be > 450ns
        GPIO.output(self._enable, True)
        self._delay_microseconds(1)       # 1 microsecond pause - enable pulse must be > 450ns
        GPIO.output(self._enable, False)
        self._delay_microseconds(1)       # commands need > 37us to settle
        
 #End class


# ------------------------------------------------------------------------
# Main script
# ------------------------------------------------------------------------

if __name__ == '__main__':
    print("Test HD44780U LCD Display")
    import time
    #import Adafruit_CharLCD as LCD
    
    # pin names taken from
    # https://github.com/adafruit/adafruit-beaglebone-io-python/blob/master/source/common.c#L73
    rs = "P1_2"
    enable = "P1_4"
    d4 = "P2_2"
    d5 = "P2_4"
    d6 = "P2_6"
    d7 = "P2_8"
    cols = 16
    rows = 2
    
    lcd = LCD(rs, enable, d4, d5, d6, d7, cols, rows)
    
    
    lcd.setCursor(0, 0)
    lcd.message("WELCOM TO BIOE CRAWL")
    
    # Demo showing the cursor.
    # lcd.clear()
    # lcd.show_cursor(True)
    # lcd.message('Show cursor')
    # time.sleep(2)
    # print("Show cursor")

    #test setting the cursor to each position
    # lcd.clear()
    # for row in range(rows):
    #     for column in range(cols):
    #         lcd.clear()
    #         lcd.setCursor(column, row)
    #         print("cursor moved to {0}".format(lcd.cursor_position))
    #         time.sleep(0.5)
    
    # #Write a message to the lcd
    # lcd.clear()
    # message = "lol"
    # time.sleep(0.5)
    # lcd.message(message)
    
    # # Scroll message right/left.
    # lcd.clear()
    # message = [4,5,6,7,8,9,10]
    # #lcd.message(message)
    # lcd.setCursor(0,0)
    # for i in range(cols-len(message)):
    #     time.sleep(0.5)
    #     lcd.scroll_right()
    #     print(lcd.cursor_position)
    # for i in range(cols-len(message)):
    #     time.sleep(0.5)
    #     lcd.scroll_left()
    #     print(lcd.cursor_position)
    
    # lcd.clear()
    # print("Test Finished")
    # lcd.message("Test Finished")
    # time.sleep(1)
    # lcd.clear()