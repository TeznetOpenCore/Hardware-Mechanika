import tkinter as tk
import serial
import threading
import pygame

# Serial and Pygame setup for sound
COM_PORT = '/dev/ttyUSB0'  # Update this to your actual COM port
BAUD_RATE = 9600

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# Initialize pygame mixer for playing sound
def play_sound(file_path):
    try:
        pygame.mixer.init()  # Initialize the mixer
        pygame.mixer.music.load(file_path)  # Load the MP3 file
        pygame.mixer.music.play()  # Play the MP3 file
    except pygame.error as e:
        print(f"Error playing sound: {e}")

# Sound file paths
add_update_sound_path = "/home/nero/prjx/Zamock/look-easy_JX3Yu5M.mp3"  # Update with your actual sound file path
startup_sound_path = "/home/nero/prjx/Zamock/real-trap-shit.mp3"  # Update with your actual sound file path
manual_command_sound_path = "/home/nero/Downloads/damn-son-whered-you-find-this.mp3"  # Update with your actual sound file path

# Keys for registers
keys = {
    "EXX": "",
    "EYX": "",
    "EZX": ""
}

# Serial communication functions
def send_command(command):
    command_with_crlf = f"{command}\r\n"  # Ensure CR and LF are included
    print(f"[SENT] - {command_with_crlf.strip()}")  # Debugging line
    try:
        ser.write(command_with_crlf.encode())
    except Exception as e:
        print(f"[ERROR] - {e}")

def read_from_lock_station():
    while True:
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            if response:
                print(f"[RECEIVED] - {response}")
                root.after(0, display_message, response)

def display_message(message):
    message_box.insert(tk.END, message + "\n")  # Display received message
    message_box.see(tk.END)  # Scroll to the bottom

# Key management functions
def update_register_contents(event):
    selected_register = register_listbox.curselection()
    if selected_register:
        reg_name = register_listbox.get(selected_register)
        key_var.set(keys[reg_name])  # Show the selected key in the entry
        current_content.set(keys[reg_name])  # Update display area with current content

def add_or_update_key():
    selected_register = register_listbox.curselection()
    key = key_var.get()
    if selected_register:
        reg_name = register_listbox.get(selected_register)
        keys[reg_name] = key  # Update the dictionary
        print(f"[UPDATED] - {reg_name}: {key}")
        
        # Construct and send the appropriate AT command
        payload_length = len(key) + len(reg_name) + 1  # +1 for the '-' separator
        message = f"AT+SEND=0,{payload_length},{reg_name}-{key}"
        send_command(message)
        
        current_content.set(key)  # Update the display area
        play_sound(add_update_sound_path)  # Play sound when the key is added/updated
    key_var.set("")  # Clear the entry

def delete_key():
    selected_register = register_listbox.curselection()
    if selected_register:
        reg_name = register_listbox.get(selected_register)
        keys[reg_name] = ""  # Clear the key
        print(f"[DELETED] - {reg_name}")
        
        # Construct and send the appropriate AT command
        payload_length = len(reg_name) + 7  # Length is 0 for an empty key
        message = f"AT+SEND=0,{payload_length},remove {reg_name}"
        send_command(message)
        
        current_content.set("")  # Clear display area
    update_register_list()

def update_register_list():
    register_listbox.delete(0, tk.END)  # Clear the listbox
    for reg in keys:
        register_listbox.insert(tk.END, reg)  # Add all registers

def send_manual_command():
    manual_command = manual_command_var.get()
    if manual_command:  # Check if command is not empty
        send_command(manual_command)
        play_sound(manual_command_sound_path)  # Play sound on command send
    else:
        print("[ERROR] - COMMAND CANNOT BE NULL")

def on_closing():
    if ser.is_open:
        ser.close()
    root.destroy()

# Create the GUI with Tkinter
root = tk.Tk()
root.title("Home Station GUI")
root.configure(bg='black')  # Set background to black
root.protocol("WM_DELETE_WINDOW", on_closing)  # Handle window close event

# Main frame for layout
main_frame = tk.Frame(root, bg='black')  # Set background to black
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Frame for Key Slot Management
slot_frame = tk.Frame(main_frame, bg='black')  # Set background to black
slot_frame.pack(side=tk.TOP, pady=10)

# Input for the key
key_var = tk.StringVar()
key_entry = tk.Entry(slot_frame, textvariable=key_var, bg='black', fg='lime', bd=2, relief='solid', font=("Arial", 12))  # Lime green text and black entry
key_entry.pack(side=tk.LEFT, padx=5)

# Buttons for adding/updating and deleting keys
button_style = {
    'bg': 'purple',
    'fg': 'white',
    'activebackground': 'lime',
    'activeforeground': 'black',
    'font': ("Arial", 10),
    'bd': 2,  # Grey border
    'highlightthickness': 1,
    'relief': 'raised'  # Raised effect
}

# Create buttons with grey border
add_update_button = tk.Button(slot_frame, text="Add/Update Key", command=add_or_update_key, **button_style)
add_update_button.pack(side=tk.LEFT, padx=5)

delete_button = tk.Button(slot_frame, text="Delete Key", command=delete_key, **button_style)
delete_button.pack(side=tk.LEFT, padx=5)

# Frame for displaying registers
register_frame = tk.Frame(main_frame, bg='black')  # Set background to black
register_frame.pack(side=tk.TOP, pady=10)

# Listbox for registers with a fixed width
register_listbox = tk.Listbox(register_frame, selectmode=tk.SINGLE, height=6, width=15, bg='black', fg='lime', font=("Arial", 12))  # Black background, lime green text
register_listbox.pack(side=tk.LEFT)
register_listbox.bind('<<ListboxSelect>>', update_register_contents)  # Bind selection event
update_register_list()  # Populate the list at start

# Frame for displaying current register contents
current_content = tk.StringVar()
current_content_label = tk.Label(register_frame, textvariable=current_content, wraplength=200, justify=tk.LEFT, bg='black', fg='lime', font=("Arial", 12))  # Black background, lime green text
current_content_label.pack(side=tk.LEFT, padx=(5, 10), pady=5)

# Frame for Manual AT Commands and message box
bottom_frame = tk.Frame(main_frame, bg='black')  # Set background to black
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

# Manual AT command entry and button, centered in bottom frame
manual_command_var = tk.StringVar()
manual_command_entry = tk.Entry(bottom_frame, textvariable=manual_command_var, width=50, bg='black', fg='lime', bd=2, relief='solid', font=("Arial", 12))  # Lime green text and black entry
manual_command_entry.pack(side=tk.TOP, pady=5)

tk.Button(bottom_frame, text="Send Manual AT Command", command=send_manual_command, **button_style).pack(side=tk.TOP, pady=5)

# Create a text box to display messages, filling the bottom frame
message_box = tk.Text(bottom_frame, height=10, width=70, bg='black', fg='lime', font=("Arial", 12), bd=3, relief='solid')  # Black background, lime green text
message_box.pack(pady=5, fill=tk.BOTH, expand=True)

# Start a thread to read from the lock station
def start_read_thread():
    threading.Thread(target=read_from_lock_station, daemon=True).start()

start_read_thread()

# Play the sound when the program starts
play_sound(startup_sound_path)  # Play sound on startup

# Start Tkinter GUI
root.mainloop()

