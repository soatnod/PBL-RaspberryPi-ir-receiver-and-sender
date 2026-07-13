#gemini

import pigpio
import time

# --- Configuration ---
IR_PIN = 16          # The GPIO pin your IR LED is connected to (BCM numbering)
FREQ = 38000         # 38 kHz carrier frequency

# NEC Protocol Timings (in microseconds)
LEADER_MARK = 29850
LEADER_SPACE = 49350
LEADER_MARK_SECOND = 3450
LEADER_SPACE_SECOND = 1590
BIT_MARK = 400
ZERO_SPACE = BIT_MARK
ONE_SPACE = 3 * BIT_MARK

#---------------------------------------------------------------------------------------------------------------------------------------

def add_carrier_burst(pulses, duration_us):
    """Generates a 38kHz PWM burst for the specified duration."""
    cycles = int((duration_us * FREQ) / 1000000)
    on_time = int(1000000 / (FREQ * 2)) # Half cycle
    for _ in range(cycles):
        # Turn pin ON, turn pin OFF, wait on_time microseconds
        pulses.append(pigpio.pulse(1 << IR_PIN, 0, on_time))
        pulses.append(pigpio.pulse(0, 1 << IR_PIN, on_time))

def add_space(pulses, duration_us):
    """Creates an empty gap (LED off) for the specified duration."""
    pulses.append(pigpio.pulse(0, 0, duration_us))

def send_massive_ir_message(pi, payload_bytes, chunk_size=8):
    wave_ids = []
    
    # --- 1. Create the Leader Wave ---
    pulses = []
    add_carrier_burst(pulses, LEADER_MARK)
    add_space(pulses, LEADER_SPACE)
    add_carrier_burst(pulses, LEADER_MARK_SECOND)
    add_space(pulses, LEADER_SPACE_SECOND)
    pi.wave_add_generic(pulses)
    leader_wid = pi.wave_create()
    if leader_wid >= 0:
        wave_ids.append(leader_wid)
    else:
        print("Error creating Leader Wave")
        return

    # --- 2. Create Chunked Data Waves ---
    # We break the payload array into chunks (default 8 bytes / 64 bits)
    for i in range(0, len(payload_bytes), chunk_size):
        chunk = payload_bytes[i:i + chunk_size]
        pulses = []
        
        for byte in chunk:
            for b in range(8):
                bit = (byte >> b) & 1
                add_carrier_burst(pulses, BIT_MARK)
                if bit == 1:
                    add_space(pulses, ONE_SPACE)
                else:
                    add_space(pulses, ZERO_SPACE)
                    
        pi.wave_add_generic(pulses)
        chunk_wid = pi.wave_create()
        if chunk_wid >= 0:
            wave_ids.append(chunk_wid)
        else:
            print(f"Error creating Data Wave at chunk {i}")
            # Clean up what we've built so far to avoid memory leaks
            for wid in wave_ids: pi.wave_delete(wid)
            return

    # --- 3. Create the Final Stop Bit Wave ---
    pulses = []
    add_carrier_burst(pulses, BIT_MARK)
    pi.wave_add_generic(pulses)
    stop_wid = pi.wave_create()
    if stop_wid >= 0:
        wave_ids.append(stop_wid)
    else:
        print("Error creating Stop Bit Wave")
        for wid in wave_ids: pi.wave_delete(wid)
        return

    # --- 4. Chain and Transmit ---
    try:
        # wave_chain takes a list of wave IDs and fires them seamlessly
        pi.wave_chain(wave_ids)
        
        # Wait for the entire chain to finish transmitting
        while pi.wave_tx_busy():
            time.sleep(0.01)
            
    finally:
        # --- 5. Clean Up Memory ---
        # It is critical to delete waves after use, or pigpio will crash
        for wid in wave_ids:
            pi.wave_delete(wid)

def sendSignal(mode, temperature, power):
    # Connect to the pigpio daemon
    pi = pigpio.pi()
    
    if not pi.connected:
        print("Failed to connect to pigpio daemon. Did you run 'sudo pigpiod'?")
        exit()
        
    pi.wave_clear()

    # Set the pin to output mode
    pi.set_mode(IR_PIN, pigpio.OUTPUT)

    print("Sending IR Signal...")

    if temperature not in list(range(16, 33)):
        print(f"error: temperature should be between 16 and 32. currently at \'{temperature}\'.")
        exit()

    tempHex = temperature * 4

    match mode:
        case 'cooler':
            modeHex = 0x23
        case 'heater':
            modeHex = 0x26
        case 'dehumid':
            modeHex = 0x25
        case 'fan':
            modeHex = 0x21
            tempHex = 0x6c
        case _:
            print(f"error: mode \'{mode}\' not recognized. ")
            exit()
    
    match power:
        case 'off':
            powerHex = 0xe0
        case 'on':
            powerHex = 0xf0
        case _:
            print(f"error: power setting \'{power}\' should be either \'on\' or \'off\'.")
            exit()
        

    hex_strings = [
        "0x1",
        "0x10",
        "0x0",
        "0x40",
        "0xbf",
        "0xff",
        "0x0",
        "0xcc",
        "0x33",
        "0x92",
        "0x6d",
        "0x13",
        "0xec",
        "0x00",         #13 temperature
        "0x00",         #14 inverse bit
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0x00",         #25 fan speed & mode
        "0x00",         #26 inverse bit
        "0x00",         #27 power button
        "0x00",          #28 inverse bit
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0x80",
        "0x7f",
        "0x3",
        "0xfc",
        "0x1",
        "0xfe",
        "0x88",
        "0x77",
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0xff",
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0x0",
        "0xff",
        "0x0"
    ]

    command = [int(hex_val, 16) for hex_val in hex_strings]

    command[13] = tempHex
    command[14] = 255 - tempHex

    command[25] = modeHex
    command[26] = 255 - modeHex
    
    command[27] = powerHex
    command[28] = 255 - powerHex
    
    send_massive_ir_message(pi, command, chunk_size=8)

    
    
    print("Signal sent successfully.")

    # Close connection
    pi.stop()

# --- Main Execution ---
if __name__ == "__main__":

    sendSignal('heater', 31, 'off')
