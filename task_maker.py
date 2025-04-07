import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os.path
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request

# Constants
CLIENT_SECRET_FILE = 'credentials.json'  # The credentials file you downloaded
API_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_account():
    """Authenticate the user and return a service object."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = googleapiclient.discovery.build(API_NAME, API_VERSION, credentials=creds)
    return service

def create_event(service, name, description, start_date, start_time, end_time, all_day, event_type):
    """Create an event in Google Calendar."""
    event_date = datetime.strptime(start_date, '%m-%d-%Y')  # Changed format to MM-DD-YYYY
    
    if all_day or 'full day activity' in description.lower():
        start_datetime = event_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = event_date.replace(hour=23, minute=59, second=59, microsecond=0)
    else:
        try:
            start_datetime = datetime.strptime(f"{start_date} {start_time}", '%m-%d-%Y %I:%M %p')  # Handle AM/PM format
            if event_type == "Event" and end_time:  # If it's an event, add end time
                end_datetime = datetime.strptime(f"{start_date} {end_time}", '%m-%d-%Y %I:%M %p')  # Handle AM/PM format
            else:  # If it's a task, no end time needed
                end_datetime = start_datetime
        except ValueError:
            print("Error: Time format is incorrect. Use HH:MM AM/PM format for start and end times.")
            return

    event = {
        'summary': name,
        'description': description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'America/New_York',  # Use EST (Eastern Standard Time)
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'America/New_York',  # Use EST (Eastern Standard Time)
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {event.get("htmlLink")}')

def on_submit():
    """Handles the submit button click."""
    name = name_entry.get()
    description = description_text.get("1.0", "end-1c")
    start_date = start_date_entry.get()  # Input in MM-DD-YYYY format
    start_time = start_time_entry.get()  # Input in HH:MM AM/PM format
    end_time = end_time_entry.get()  # Input in HH:MM AM/PM format (for events)
    all_day = all_day_var.get()
    event_type = task_event_var.get()  # Task or Event

    try:
        service = authenticate_google_account()
        create_event(service, name, description, start_date, start_time, end_time, all_day, event_type)
        print("Event created successfully!")
    except Exception as e:
        print(f"Error creating event: {e}")

def toggle_time_fields():
    """Toggle the visibility of time fields when 'All Day Event' is selected."""
    if all_day_var.get():
        start_time_label.grid_forget()
        start_time_entry.grid_forget()
        end_time_label.grid_forget()
        end_time_entry.grid_forget()
    else:
        start_time_label.grid(row=4, column=0, padx=10, pady=5)
        start_time_entry.grid(row=4, column=1, padx=10, pady=5)
        if task_event_var.get() == "Event":  # Only show end time for Events
            end_time_label.grid(row=5, column=0, padx=10, pady=5)
            end_time_entry.grid(row=5, column=1, padx=10, pady=5)
        else:  # Hide end time for Tasks
            end_time_label.grid_forget()
            end_time_entry.grid_forget()

def update_task_event(*args):
    """Update the form fields based on the selection of Task or Event."""
    toggle_time_fields()

# Animation for fading in widgets
def fade_in(widget, interval=50, alpha=0.1):
    def update_color():
        nonlocal alpha
        if alpha < 1:
            widget.configure(fg=f"#{int(alpha*255):02x}{int(alpha*255):02x}{int(alpha*255):02x}")
            alpha += 0.05
            widget.after(interval, update_color)
    
    update_color()

# GUI Setup
root = tk.Tk()
root.geometry("500x400")
root.title("TaskMaker for Google Calendar")
root.configure(bg='#1C1C1C')  # Dark background for dark mode

frame = tk.Frame(root, bg='#1C1C1C')
frame.pack(pady=20, padx=20, fill="both", expand=True)

# --- Task or Event Selection --- 
task_event_label = tk.Label(frame, text="Select Type (Task/Event):", font=("Helvetica", 12, "bold"), bg='#1C1C1C', fg='#ECF0F1')
task_event_label.grid(row=0, column=0, padx=10, pady=5)
task_event_var = tk.StringVar()
task_event_dropdown = ttk.Combobox(frame, textvariable=task_event_var, values=["Task", "Event"], font=("Helvetica", 11), state="readonly", width=12)
task_event_dropdown.grid(row=0, column=1, padx=10, pady=5)
task_event_dropdown.set("Event")  # Default value is Event
task_event_var.trace("w", update_task_event)

# --- Task Name --- 
name_label = tk.Label(frame, text="Task Name:", font=("Helvetica", 11), bg='#1C1C1C', fg='#ECF0F1')
name_label.grid(row=1, column=0, padx=10, pady=5)
name_entry = tk.Entry(frame, font=("Helvetica", 11), bg='#2E2E2E', fg='#ECF0F1', bd=0, insertbackground='white', relief="flat", width=30)
name_entry.grid(row=1, column=1, padx=10, pady=5)

# --- Task Description --- 
description_label = tk.Label(frame, text="Description:", font=("Helvetica", 11), bg='#1C1C1C', fg='#ECF0F1')
description_label.grid(row=2, column=0, padx=10, pady=5)
description_text = tk.Text(frame, height=4, font=("Helvetica", 11), bg='#2E2E2E', fg='#ECF0F1', wrap="word", width=30, bd=0, relief="flat")
description_text.grid(row=2, column=1, padx=10, pady=5)

# --- Start Date (MM-DD-YYYY) --- 
start_date_label = tk.Label(frame, text="Start Date (MM-DD-YYYY):", font=("Helvetica", 11), bg='#1C1C1C', fg='#ECF0F1')
start_date_label.grid(row=3, column=0, padx=10, pady=5)
start_date_entry = tk.Entry(frame, font=("Helvetica", 11), bg='#2E2E2E', fg='#ECF0F1', bd=0, insertbackground='white', relief="flat", width=30)
start_date_entry.grid(row=3, column=1, padx=10, pady=5)

# --- Start Time (HH:MM AM/PM) --- 
start_time_label = tk.Label(frame, text="Start Time (HH:MM AM/PM):", font=("Helvetica", 11), bg='#1C1C1C', fg='#ECF0F1')
start_time_label.grid(row=4, column=0, padx=10, pady=5)
start_time_entry = tk.Entry(frame, font=("Helvetica", 11), bg='#2E2E2E', fg='#ECF0F1', bd=0, insertbackground='white', relief="flat", width=12)
start_time_entry.grid(row=4, column=1, padx=10, pady=5)

# --- End Time (HH:MM AM/PM) --- 
end_time_label = tk.Label(frame, text="End Time (HH:MM AM/PM):", font=("Helvetica", 11), bg='#1C1C1C', fg='#ECF0F1')
end_time_label.grid(row=5, column=0, padx=10, pady=5)
end_time_entry = tk.Entry(frame, font=("Helvetica", 11), bg='#2E2E2E', fg='#ECF0F1', bd=0, insertbackground='white', relief="flat", width=12)
end_time_entry.grid(row=5, column=1, padx=10, pady=5)

# --- All Day Event --- 
all_day_var = tk.BooleanVar()
all_day_check = tk.Checkbutton(frame, text="All Day?", variable=all_day_var, font=("Helvetica", 11), bg='#1C1C1C', fg='#ECF0F1', selectcolor='#2E2E2E', command=toggle_time_fields)
all_day_check.grid(row=6, column=0, padx=10, pady=5)

# --- Submit Button --- 
submit_button = tk.Button(frame, text="Submit", font=("Helvetica", 12, "bold"), bg='#3498db', fg='#fff', relief="flat", width=20, command=on_submit)
submit_button.grid(row=7, column=0, columnspan=2, pady=20)

# Fade in animation for labels and input fields
fade_in(task_event_label)
fade_in(name_label)
fade_in(description_label)
fade_in(start_date_label)
fade_in(start_time_label)
fade_in(end_time_label)
fade_in(all_day_check)
fade_in(submit_button)

root.mainloop()
