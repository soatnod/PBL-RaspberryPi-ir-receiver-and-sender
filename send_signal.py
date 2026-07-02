#gemini

import pigpio
import time

# --- Configuration ---
IR_PIN = 16          # The GPIO pin your IR LED is connected to (BCM numbering)
FREQ = 38000         # 38 kHz carrier frequency

# NEC Protocol Timings (in microseconds)
LEADER_MARK = 9000
LEADER_SPACE = 4500
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



# --- Main Execution ---
if __name__ == "__main__":
    # Connect to the pigpio daemon
    pi = pigpio.pi()
    
    if not pi.connected:
        print("Failed to connect to pigpio daemon. Did you run 'sudo pigpiod'?")
        exit()
        
    pi.wave_clear()

    # Set the pin to output mode
    pi.set_mode(IR_PIN, pigpio.OUTPUT)

    print("Sending IR Signal...")
    
    command = [
        0x80, 0x08, 0x00, 0x02, 0xfd, 0xff, 0x00, 0x33,
        0xcc, 0x49, 0xb6, 0xc8
    ]
    
    command_1 = [
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    ]
    
    send_massive_ir_message(pi, command_1, chunk_size=8)
    
    print("Signal sent successfully.")

    # Close connection
    pi.stop()
