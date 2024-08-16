import tkinter as tk  # Import the tkinter library for creating GUI applications
from tkinter import messagebox, scrolledtext, filedialog, simpledialog, Toplevel, IntVar  # Import specific tkinter # components for enhanced GUI functionality
from tkinter import ttk  # Import the themed tkinter widgets for a modern look
import requests  # Import the requests library to handle HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup to parse HTML content
import random  # Import random to select random elements
import threading  # Import threading to handle tasks in parallel
import schedule  # Import schedule to manage task scheduling
import time  # Import time for time-related operations
import os  # Import os for file and directory operations
import glob # Import wildcard file import
from datetime import datetime  # Import datetime to work with dates and times
from difflib import unified_diff  # Import unified_diff to find differences between two texts

# Predefined list of common HTML tags to suggest for scraping
tags = ['p', 'h1', 'h2', 'h3', 'div', 'span', 'a', 'ul', 'li', 'img', 'table']

active_scans_listbox = None

# State variable to control hotkeys (enabled or disabled) and mapping for custom hotkeys
hotkeys_enabled = False  # Whether hotkeys are enabled
hotkey_mapping = {  # Dictionary mapping actions to specific hotkeys
    'scrape': '1',  # '1' key triggers the scrape action
    'save': '2',  # '2' key triggers the save action
    'clear': '3',  # '3' key clears the text area
    'search': '4'  # '4' key triggers a search
}

# List to store positions of search matches within the text
search_matches = []
current_match_index = -1  # Index to keep track of the current match

# Variables to control saving behavior and file format
save_option = None  # This variable will track whether content should be saved with or without HTML tags
file_format_option = None  # This variable will track the desired file format (e.g., .txt, .csv, .json)

# Variables to store the full scraped content and previous content for comparison (used in the diff functionality)
full_content = ""
previous_content = ""

# Maximum number of scans to retain and the job name for scheduled scans
max_files = None
job_name = None

# Flag to pause active scans
pause_flag = False

# Dictionary to track the state of each scheduled scan (e.g., running, paused, stopped)
scans = {}


def update_last_updated(label):
    """Update the 'Last updated:' label with the current timestamp and change the color to green temporarily."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current time formatted as a string
    label.config(text=f"Last updated: {current_time}", foreground="green")  # Update the label's text and color

    def reset_label_color():
        if label.winfo_exists():  # Check if the label still exists (hasn't been closed)
            label.config(foreground="black")  # Reset the color to black

    root.after(2000, reset_label_color)  # Change the color back after 2 seconds


def scrape():
    """Scrape the HTML content from the given URL based on the specified tag and display it in the text area."""
    global full_content, previous_content  # Use global variables to track content
    if pause_flag:  # Do not scrape if scanning is paused
        return

    url = url_entry.get()  # Get the URL from the entry widget
    tag = tag_entry.get()  # Get the HTML tag from the entry widget

    if not url or not tag:  # Check if both URL and tag are provided
        messagebox.showerror("Error", "Please enter both a URL and a tag.")
        return

    try:
        response = requests.get(url)  # Make an HTTP GET request to the specified URL
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content using BeautifulSoup
        elements = soup.find_all(tag)  # Find all elements with the specified tag

        # Clear the text areas before displaying new content
        text_area.delete(1.0, tk.END)
        preview_text_area.delete(1.0, tk.END)
        previous_content = full_content  # Store previous content before updating
        full_content = ""  # Clear full_content for new data

        if elements:  # If elements are found with the specified tag
            for element in elements:
                full_content += str(element) + "\n\n"  # Store full element with tags
            # Display only the first 1000 characters in the preview text area
            preview_text_area.insert(tk.END, full_content[:10000] + "\n\n... [Content Truncated]")
        else:  # If no elements are found
            preview_text_area.insert(tk.END, f"No elements found with the tag '{tag}'.")

        update_last_updated(last_updated_label)  # Update the last updated label with the current time

        auto_save()  # Automatically save the scraped content after scraping

    except requests.exceptions.RequestException as e:  # Handle any HTTP-related exceptions
        messagebox.showerror("Error", f"Failed to retrieve the page: {e}")


def auto_save():
    """Automatically save the scraped content to a file based on the user's preferences."""
    global full_content, job_name

    file_content = full_content.strip()  # Remove any leading or trailing whitespace
    if not file_content:  # If there is no content, do not save
        return

    # Determine the file extension based on the selected file format
    if file_format_option.get() == 1:
        file_ext = ".csv"
    elif file_format_option.get() == 2:
        file_ext = ".json"
    else:
        file_ext = ".txt"

    # Check if tags should be removed before saving
    if save_option.get() == 2:  # Without Tags option
        soup = BeautifulSoup(file_content, 'html.parser')
        file_content = soup.get_text()  # Extract and save only the text

    # Generate a file path based on the job name and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not job_name:
        print("Failed to save the file: Job name not provided.")
        return

    file_path = f"./{job_name}/active_scans/{job_name}_{timestamp}{file_ext}"

    try:
        # Save the content to a file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(file_content)
        print(f"Content automatically saved to {file_path}")
    except Exception as e:  # Handle any exceptions that occur during the save process
        print(f"Failed to save the file: {e}")


def save_to_file():
    """Prompt the user to save the scraped content to a file."""
    global full_content
    file_content = full_content.strip()

    if not file_content:  # If there is no content, display an error message
        messagebox.showerror("Error", "No content to save.")
        return

    # Determine the file extension based on the selected file format
    if file_format_option.get() == 1:
        file_ext = ".csv"
    elif file_format_option.get() == 2:
        file_ext = ".json"
    else:
        file_ext = ".txt"

    # Check if tags should be removed before saving
    if save_option.get() == 2:  # Without Tags option
        soup = BeautifulSoup(file_content, 'html.parser')
        file_content = soup.get_text()

    # Open a file dialog to select the save location
    file_path = filedialog.asksaveasfilename(defaultextension=file_ext,
                                             filetypes=[("All Files", f"*{file_ext}")])
    if file_path:
        try:
            # Run the save operation in a separate thread to prevent blocking the UI
            save_thread = threading.Thread(target=save_content_to_file, args=(file_path, file_content))
            save_thread.start()
        except Exception as e:  # Handle any exceptions during the save process
            messagebox.showerror("Error", f"Failed to save the file: {e}")


def save_content_to_file(file_path, content):
    """Save the provided content to the specified file path."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    messagebox.showinfo("Success", "File saved successfully.")  # Display a success message once the file is saved


def clear_text_area():
    """Clear the content of both text areas."""
    text_area.delete(1.0, tk.END)  # Clear the full content area
    preview_text_area.delete(1.0, tk.END)  # Clear the preview text area


def search_within_text(text_area, search_entry, search_matches):
    """Search for a term within the text area and highlight the matches."""
    search_term = search_entry.get()  # Get the search term from the entry widget
    if not search_term:  # If no search term is provided, display an error message
        messagebox.showerror("Error", "Please enter a search term.")
        return

    search_matches.clear()  # Clear previous search matches

    full_text = text_area.get(1.0, tk.END)  # Get the full text from the text area

    # Remove previous highlights
    text_area.tag_remove('highlight', '1.0', tk.END)

    # Search for the term within the full text
    start_pos = 0
    while True:
        start_pos = full_text.find(search_term, start_pos)  # Find the search term in the text
        if start_pos == -1:  # If the term is not found, break the loop
            break
        end_pos = start_pos + len(search_term)  # Calculate the end position of the match
        search_matches.append((start_pos, end_pos))  # Store the match positions
        start_pos = end_pos  # Move to the next position after the match

    if search_matches:  # If matches are found, highlight the first one
        go_to_match(text_area, search_matches, 0)
    else:  # If no matches are found, display an info message
        messagebox.showinfo("No Matches", "No matches found.")


def go_to_match(text_area, search_matches, index):
    """Go to and highlight the specified match in the text area."""
    if 0 <= index < len(search_matches):  # Ensure the index is valid
        start_pos, end_pos = search_matches[index]  # Get the match positions
        text_area.mark_set("insert", f"1.{start_pos}")  # Move the cursor to the start of the match
        text_area.tag_add('highlight', f"1.{start_pos}", f"1.{end_pos}")  # Highlight the match
        text_area.tag_config('highlight', background='yellow', foreground='black')  # Set the highlight color
        text_area.see(f"1.{start_pos}")  # Scroll to the match position


def next_match(text_area, search_matches, current_match_index):
    """Move to the next match in the text area."""
    if search_matches and current_match_index[0] < len(search_matches) - 1:
        current_match_index[0] += 1  # Increment the current match index
        go_to_match(text_area, search_matches, current_match_index[0])  # Go to the next match


def previous_match(text_area, search_matches, current_match_index):
    """Move to the previous match in the text area."""
    if search_matches and current_match_index[0] > 0:
        current_match_index[0] -= 1  # Decrement the current match index
        go_to_match(text_area, search_matches, current_match_index[0])  # Go to the previous match


def export_search():
    """Export the search results to a file."""
    search_text = text_area.get("1.0", tk.END).strip()  # Get the full text from the text area
    if not search_text:  # If there is no text, display an error message
        messagebox.showerror("Error", "No search results to export.")
        return

    # Determine the file extension based on the selected file format
    if file_format_option.get() == 1:
        file_ext = ".csv"
    elif file_format_option.get() == 2:
        file_ext = ".json"
    else:
        file_ext = ".txt"

    # Check if tags should be removed before exporting
    if save_option.get() == 2:  # Without Tags option
        soup = BeautifulSoup(search_text, 'html.parser')
        search_text = soup.get_text()

    # Open a file dialog to select the save location for the search results
    file_path = filedialog.asksaveasfilename(defaultextension=file_ext,
                                             filetypes=[("All Files", f"*{file_ext}")])
    if file_path:
        try:
            # Save the search results to the selected file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(search_text)
            messagebox.showinfo("Success", "Search results exported successfully.")
        except Exception as e:  # Handle any exceptions during the export process
            messagebox.showerror("Error", f"Failed to export the search results: {e}")


def toggle_hotkeys():
    """Toggle the hotkeys on or off."""
    global hotkeys_enabled  # Use the global hotkeys_enabled variable
    hotkeys_enabled = not hotkeys_enabled  # Toggle the state of hotkeys
    status = "enabled" if hotkeys_enabled else "disabled"  # Set the status text based on the state
    hotkeys_button.config(text=f"Hotkeys: {status.capitalize()}")  # Update the button text


def on_key_press(event):
    """Handle key press events to trigger actions via hotkeys."""
    if hotkeys_enabled:  # If hotkeys are enabled, check for the corresponding action
        if event.char == hotkey_mapping['scrape']:
            scrape()
        elif event.char == hotkey_mapping['save']:
            save_to_file()
        elif event.char == hotkey_mapping['clear']:
            clear_text_area()
        elif event.char == hotkey_mapping['search']:
            search_within_text(text_area, search_entry, search_matches)


def set_custom_hotkeys():
    """Allow the user to set custom hotkeys for specific actions."""
    global hotkey_mapping  # Use the global hotkey_mapping variable
    for action in hotkey_mapping:  # Iterate over each action in the mapping
        key = simpledialog.askstring("Custom Hotkey",
                                     f"Set hotkey for {action.capitalize()} (current: {hotkey_mapping[action]}):")
        if key:  # If a new key is provided, update the mapping
            hotkey_mapping[action] = key.lower()


def show_suggestion():
    """Show a random HTML tag suggestion to the user."""
    suggested_tag = random.choice(tags)  # Choose a random tag from the predefined list
    suggestion_label.config(text=f"Try scraping: <{suggested_tag}>")  # Display the suggested tag


def parse_data(parse_type):
    """Parse the scraped HTML content based on the specified type (text, links, images, tables)."""
    global full_content
    file_content = full_content.strip()

    if not file_content:  # If there is no content, display an error message
        messagebox.showerror("Error", "No content to parse.")
        return

    soup = BeautifulSoup(file_content, 'html.parser')  # Parse the HTML content using BeautifulSoup

    # Clear the text area before displaying the parsed content
    text_area.delete(1.0, tk.END)

    if parse_type == "text":  # If parsing text, extract and display the text content
        text_area.insert(tk.END, soup.get_text())
    elif parse_type == "links":  # If parsing links, extract and display all link URLs
        links = [a['href'] for a in soup.find_all('a', href=True)]
        for link in links:
            text_area.insert(tk.END, link + "\n")
    elif parse_type == "images":  # If parsing images, extract and display all image URLs
        images = [img['src'] for img in soup.find_all('img', src=True)]
        for img in images:
            text_area.insert(tk.END, img + "\n")
    elif parse_type == "tables":  # If parsing tables, extract and display all tables as HTML
        tables = soup.find_all('table')
        for table in tables:
            text_area.insert(tk.END, str(table) + "\n\n")


def highlight_differences():
    """Highlight differences between the previous and current scraped content."""
    global full_content, previous_content

    if not previous_content:  # If there is no previous content to compare, display an info message
        messagebox.showinfo("No Previous Scan", "There is no previous scan to compare.")
        return

    # Perform a diff comparison between the previous and current content
    diff = list(unified_diff(previous_content.splitlines(), full_content.splitlines()))

    if diff:  # If differences are found, display them in the text area
        diff_text = "\n".join(diff)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, diff_text)
        messagebox.showinfo("Differences Found", "Differences have been highlighted in the text area.")
    else:  # If no differences are found, display an info message
        messagebox.showinfo("No Differences", "No differences found between the previous and current scan.")


def pause_active_scans(scan_name):
    """Pause or resume the specified active scan based on the current state."""
    if scan_name not in scans:
        return

    current_state = scans[scan_name]['state']

    # Toggle between Paused and Running states
    if current_state == 'Running':
        scans[scan_name]['state'] = 'Paused'
        pause_button.config(text="Resume")  # Change button to Resume
        print(f'{scan_name} paused')
    elif current_state == 'Paused':
        scans[scan_name]['state'] = 'Running'
        pause_button.config(text="Pause")  # Change button to Pause
        print(f'{scan_name} resumed')

    update_active_scans_listbox()  # Update the UI with the new state



# Define active_scans_listbox globally so that it can be accessed by all functions

def update_active_scans_listbox():
    """Update the active scans listbox with the current scan information."""
    global active_scans_listbox
    if active_scans_listbox is not None and active_scans_listbox.winfo_exists():  # Check if the listbox exists
        active_scans_listbox.delete(0, tk.END)  # Clear the listbox
        for job_name, scan_info in scans.items():  # Add each scan and its current state to the listbox
            scan_state = scan_info.get('state', 'Unknown')  # Retrieve the current state of the scan
            active_scans_listbox.insert(tk.END, f"{job_name} - {scan_state}")  # Display the job name and its state
    else:
        print("Warning: active_scans_listbox is not initialized or has been destroyed.")



def open_schedule_window():
    """Open a new window to view and manage active scans."""
    global active_scans_listbox  # Declare as global to modify it
    schedule_window = Toplevel(root)  # Create a new top-level window
    schedule_window.title("Scheduled Scans")  # Set the window title

    # Initialize the active_scans_listbox
    active_scans_listbox = tk.Listbox(schedule_window, width=60, height=15)
    active_scans_listbox.pack(pady=5)

    # Text area to display the recent results of the selected job
    job_results_text_area = scrolledtext.ScrolledText(schedule_window, wrap=tk.WORD, width=50, height=5,
                                                      font=("Arial", 11))
    job_results_text_area.pack(pady=5)

    # Create the control buttons once at the start
    control_buttons_frame = ttk.Frame(schedule_window)  # Create a frame to hold the buttons
    control_buttons_frame.pack(pady=5)

    run_button = ttk.Button(control_buttons_frame, text="Run", state="disabled")
    run_button.grid(row=0, column=0, padx=5)

    pause_button = ttk.Button(control_buttons_frame, text="Pause", state="disabled")
    pause_button.grid(row=0, column=1, padx=5)

    stop_button = ttk.Button(control_buttons_frame, text="Stop", state="disabled")
    stop_button.grid(row=0, column=2, padx=5)

    selected_scan = None  # To keep track of the currently selected scan

    def update_control_buttons(scan_name):
        """Update control buttons based on the selected scan's state."""
        if scan_name is None or scan_name not in scans:
            print(f'Scan is not in database')
            return

        scan_state = scans[scan_name]['state']

        # Update the buttons based on the state
        if scan_state == 'Running':
            run_button.config(state="disabled")
            pause_button.config(state="normal", text="Pause", command=lambda: pause_active_scans(scan_name))
            stop_button.config(state="normal", command=lambda: stop_scan(scan_name))
        elif scan_state == 'Paused':
            run_button.config(state="normal", command=lambda: run_scan(scan_name))
            pause_button.config(state="normal", text="Resume", command=lambda: pause_active_scans(scan_name))
            stop_button.config(state="normal", command=lambda: stop_scan(scan_name))
        else:  # Stopped
            run_button.config(state="normal", command=lambda: run_scan(scan_name))
            pause_button.config(state="disabled")
            stop_button.config(state="disabled")

    # Text area to display the recent results of the selected job
    job_results_text_area = scrolledtext.ScrolledText(schedule_window, wrap=tk.WORD, width=60, height=5,
                                                      # Reduced height
                                                      font=("Arial", 11))
    job_results_text_area.pack(pady=5)

    def update_job_results():
        """Update the displayed job results when a scan is selected."""
        selected_index = active_scans_listbox.curselection()  # Get the selected item index
        if selected_index:  # If an item is selected
            selected_job = active_scans_listbox.get(selected_index).split(" - ")[0]  # Get the selected job name
            global selected_scan  # Update the global selected scan
            selected_scan = selected_job

            update_control_buttons(selected_scan)  # Update control buttons for the selected scan

            try:
                # Define the pattern to match files with the selected_scan and any timestamp
                file_pattern = f"./{selected_scan}/active_scans/{selected_scan}_*.txt"

                # Use glob to find all files that match the pattern
                matching_files = glob.glob(file_pattern)

                if matching_files:  # If matching files are found
                    # Get the most recent file based on modification time
                    latest_file = max(matching_files, key=os.path.getmtime)

                    # Open the most recent matching file
                    with open(latest_file, 'r') as file:
                        job_results = file.read()

                    # Limit the output to 2000 characters
                    if len(job_results) > 2000:
                        job_results = job_results[:2000] + "\n\n... [Output Truncated]"

                    job_results_text_area.delete(1.0, tk.END)  # Clear the text area
                    job_results_text_area.insert(tk.END, job_results)  # Insert the job results
                else:
                    # No matching files found
                    job_results_text_area.delete(1.0, tk.END)
                    job_results_text_area.insert(tk.END, f"No recent results found for {selected_scan}.")
            except FileNotFoundError:
                job_results_text_area.delete(1.0, tk.END)
                job_results_text_area.insert(tk.END, f"No recent results found for {selected_scan}.")
            except Exception as e:
                job_results_text_area.delete(1.0, tk.END)
                job_results_text_area.insert(tk.END, f"Error loading job results: {str(e)}")

    def run_scan(scan_name):
        """Set the state of the selected scan to 'Running', start the scan, and update the UI."""
        if scan_name in scans and scans[scan_name]['state'] != 'Running':
            scans[scan_name]['state'] = 'Running'
            update_active_scans_listbox()
            update_control_buttons(scan_name)

            # Create a thread to run the actual scan logic
            scan_thread = threading.Thread(target=scan_logic, args=(scan_name,))
            scans[scan_name]['thread'] = scan_thread  # Store the thread reference
            scan_thread.start()
            print(f'Scan {scan_name} is running')

    def stop_scan(scan_name):
        """Set the state of the selected scan to 'Stopped', stop the scan, and update the UI."""
        if scan_name in scans and scans[scan_name]['state'] == 'Running':
            scans[scan_name]['state'] = 'Stopped'
            update_active_scans_listbox()
            update_control_buttons(scan_name)

            # You would typically signal the thread to stop here
            scan_thread = scans[scan_name].get('thread')
            if scan_thread and scan_thread.is_alive():
                # Add your logic to stop the scan here
                print(f'Scan {scan_name} is stopping')
                # Example: Set a stop flag in the scan logic and wait for the thread to finish
                scans[scan_name]['stop_flag'] = True
                scan_thread.join()
            print(f'Scan {scan_name} has stopped')

    def scan_logic(scan_name):
        """Simulate the scanning process."""
        while scans[scan_name]['state'] == 'Running' and not scans[scan_name].get('stop_flag', False):
            # Replace this with the actual scanning logic
            print(f"Scanning... {scan_name}")
            time.sleep(2)  # Simulate work by sleeping

        print(f"Scan {scan_name} stopped.")



    def update_active_scans_listbox():
        """Update the active scans listbox with the current scan information."""
        active_scans_listbox.delete(0, tk.END)  # Clear the listbox
        for job_name, scan_info in scans.items():  # Add each scan and its state to the listbox
            active_scans_listbox.insert(tk.END, f"{job_name} - {scan_info['state']}")

    # Example usage: Adding two sample scans
    scans[job_name] = {"state": "Stopped"}
    update_active_scans_listbox()  # Update the active scans listbox

    # Bind the selection event to update job results when a scan is selected
    active_scans_listbox.bind("<<ListboxSelect>>", lambda event: update_job_results())


def open_schedule_popup():
    """Open a popup window to schedule new scraping tasks."""
    schedule_popup = Toplevel(root)  # Create a new top-level window
    schedule_popup.title("Schedule Scraping")  # Set the window title

    # Create and place the job name label and entry field
    job_name_label = ttk.Label(schedule_popup, text="Job Name:")
    job_name_label.grid(row=0, column=0, padx=10, pady=10)

    job_name_entry = ttk.Entry(schedule_popup, width=30)  # Entry widget for the job name
    job_name_entry.grid(row=0, column=1, padx=10, pady=10)

    # Create and place the interval label and entry field
    interval_label = ttk.Label(schedule_popup, text="Schedule Scraping Every:")
    interval_label.grid(row=1, column=0, padx=10, pady=10)

    interval_entry = ttk.Entry(schedule_popup, width=10)  # Entry widget for the interval
    interval_entry.grid(row=1, column=1, padx=10, pady=10)

    # Create and place the combobox for time units (e.g., seconds, minutes)
    unit_combobox = ttk.Combobox(schedule_popup, values=["seconds", "minutes", "hours", "days"], state="readonly")
    unit_combobox.grid(row=1, column=2, padx=10, pady=10)
    unit_combobox.current(1)  # Set the default value to "minutes"

    # Create and place the max files label and entry field
    max_files_label = ttk.Label(schedule_popup, text="Max Files to Keep:")
    max_files_label.grid(row=2, column=0, padx=10, pady=10)

    max_files_entry = ttk.Entry(schedule_popup, width=10)  # Entry widget for the max files
    max_files_entry.grid(row=2, column=1, padx=10, pady=10)

    # Create and place the overwrite checkbox to control file overwriting behavior
    overwrite_var = IntVar()  # Variable to track the state of the checkbox
    overwrite_checkbox = ttk.Checkbutton(schedule_popup, text="Overwrite Previous Scans", variable=overwrite_var)
    overwrite_checkbox.grid(row=3, column=1, padx=10, pady=10)

    def schedule_and_close():
        """Schedule the scraping task based on user input and close the popup window."""
        try:
            global job_name, max_files
            interval = int(interval_entry.get())  # Get the interval as an integer
            unit = unit_combobox.get()  # Get the selected time unit
            job_name = job_name_entry.get()  # Get the job name from the entry field
            max_files = int(max_files_entry.get())  # Get the max files as an integer

            if not job_name:  # If no job name is provided, display an error message
                messagebox.showerror("Error", "Please enter a job name.")
                return

            os.makedirs(f"./{job_name}/active_scans",
                        exist_ok=True)  # Create the directory for the job if it doesn't exist

            scans[job_name] = {"state": "Stopped"}  # Add the job to the scans dictionary

            # Only update the listbox if it has been initialized (i.e., if the window has been opened)
            if active_scans_listbox is not None:
                update_active_scans_listbox()  # Update the active scans listbox

            schedule_scraping(interval, unit)  # Schedule the scraping task
            schedule_popup.destroy()  # Close the popup window
        except ValueError:  # Handle any value errors (e.g., non-integer inputs)
            messagebox.showerror("Error", "Please enter valid numbers for the interval and max files.")



    def cancel_and_close():
        """Close the popup window without scheduling a task."""
        schedule_popup.destroy()

    # Create and place the Schedule and Cancel buttons
    schedule_button = ttk.Button(schedule_popup, text="Schedule", command=schedule_and_close)
    schedule_button.grid(row=4, column=1, padx=10, pady=10)

    cancel_button = ttk.Button(schedule_popup, text="Cancel", command=cancel_and_close)
    cancel_button.grid(row=4, column=2, padx=10, pady=10)


# Scheduling Functionality
def schedule_scraping(interval, unit):
    """Schedule the scraping task at the specified interval and time unit."""
    if unit == "seconds":
        schedule.every(interval).seconds.do(scrape)
    elif unit == "minutes":
        schedule.every(interval).minutes.do(scrape)
    elif unit == "hours":
        schedule.every(interval).hours.do(scrape)
    elif unit == "days":
        schedule.every(interval).days.do(scrape)

    # Run the scheduling in a separate thread to avoid blocking the main GUI thread
    threading.Thread(target=run_scheduler).start()


def run_scheduler():
    """Continuously run the scheduled tasks."""
    while True:  # Run indefinitely
        schedule.run_pending()  # Execute any pending tasks
        time.sleep(1)  # Sleep for 1 second before checking again


# Set up the GUI
root = tk.Tk()  # Create the main application window
root.title("Simple Web Scraper")  # Set the window title

# Set the background color for the main window
root.configure(bg="#f0f0f0")

# Variable to control saving behavior (with or without tags)
save_option = tk.IntVar(value=1)  # Default is "With Tags"

# Variable to control file format selection
file_format_option = tk.IntVar(value=3)  # Default is ".txt"

# Apply styling to ttk widgets
style = ttk.Style()
style.configure("TButton", font=("Arial", 12), padding=6)
style.configure("TLabel", font=("Arial", 12), background="#f0f0f0")
style.configure("TEntry", font=("Arial", 12))

# Button Frame: contains Schedule Scraping, View Active Scans, Pause Active Scans
button_frame = ttk.Frame(root)  # Create a frame to hold the buttons
button_frame.pack(pady=10)

# Create and place the buttons for scheduling, viewing, and pausing scans
schedule_popup_button = ttk.Button(button_frame, text="Schedule Scraping", command=open_schedule_popup)
schedule_popup_button.grid(row=0, column=0, padx=3)

schedule_window_button = ttk.Button(button_frame, text="View Active Scans", command=open_schedule_window)
schedule_window_button.grid(row=0, column=1, padx=3)

pause_button = ttk.Button(button_frame, text="Pause Active Scans", command=lambda: pause_active_scans(selected_scan))
pause_button.grid(row=0, column=2, padx=3)

# Additional Button Frame: contains Highlight Differences, Hotkeys, Set Custom Hotkeys
additional_button_frame = ttk.Frame(root)
additional_button_frame.pack(pady=3)

# Create and place buttons for highlighting differences, toggling hotkeys, and setting custom hotkeys
highlight_button = ttk.Button(additional_button_frame, text="Highlight Differences", command=highlight_differences)
highlight_button.grid(row=0, column=0, padx=3)

hotkeys_button = ttk.Button(additional_button_frame, text="Hotkeys: Disabled", command=toggle_hotkeys)
hotkeys_button.grid(row=0, column=1, padx=3)

custom_hotkeys_button = ttk.Button(additional_button_frame, text="Set Custom Hotkeys", command=set_custom_hotkeys)
custom_hotkeys_button.grid(row=0, column=2, padx=3)

# Action Button Frame: contains ?, Scrape, Clear Text Area
action_button_frame = ttk.Frame(root)
action_button_frame.pack(pady=5)

# Create and place buttons for suggestions, scraping, and clearing the text area
suggestions_button = ttk.Button(action_button_frame, text="?", width=5, command=show_suggestion)
suggestions_button.grid(row=0, column=0, padx=5)

scrape_button = ttk.Button(action_button_frame, text="Scrape", command=scrape)
scrape_button.grid(row=0, column=1, padx=5)

clear_text_area_button = ttk.Button(action_button_frame, text="Clear Text Area", command=clear_text_area)
clear_text_area_button.grid(row=0, column=2, padx=5)

# URL input: Create and place the URL label and entry field
url_label = ttk.Label(root, text="Enter URL:")
url_label.pack(pady=5)
url_entry = ttk.Entry(root, width=50)
url_entry.pack(pady=5)

# Tag input: Create and place the tag label and entry field
tag_label = ttk.Label(root, text="Enter Tag to Scrape:")
tag_label.pack(pady=5)
tag_entry = ttk.Entry(root, width=50)
tag_entry.pack(pady=5)

# Smaller preview text area to display a preview of the results
preview_text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=5, font=("Arial", 11))
preview_text_area.pack(pady=5)

# Last updated label
last_updated_label = ttk.Label(root, text="Last updated: Never", font=("Arial", 12))
last_updated_label.pack(pady=10)

# Save Options: Checkboxes for saving with or without tags and file format options
options_frame = ttk.Frame(root)
options_frame.pack(pady=10)

# Create and place the save button, radio buttons for saving options, and file format options
save_button = ttk.Button(options_frame, text="Save to File", command=lambda: check_limit() and save_to_file())
save_button.grid(row=0, column=0, padx=5)

with_tags_checkbox = ttk.Radiobutton(options_frame, text="With Tags", variable=save_option, value=1)
with_tags_checkbox.grid(row=0, column=1, padx=5)

without_tags_checkbox = ttk.Radiobutton(options_frame, text="Without Tags", variable=save_option, value=2)
without_tags_checkbox.grid(row=0, column=2, padx=5)

csv_checkbox = ttk.Radiobutton(options_frame, text=".csv", variable=file_format_option, value=1)
csv_checkbox.grid(row=0, column=3, padx=5)

json_checkbox = ttk.Radiobutton(options_frame, text=".json", variable=file_format_option, value=2)
json_checkbox.grid(row=0, column=4, padx=5)

txt_checkbox = ttk.Radiobutton(options_frame, text=".txt", variable=file_format_option, value=3)
txt_checkbox.grid(row=0, column=5, padx=5)

# Full scrolled text area to display results
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10, font=("Arial", 11))
text_area.pack(pady=5)

# Suggestion label to display the suggestion from the "?" button
suggestion_label = ttk.Label(root, text="", font=("Arial", 12))
suggestion_label.pack(pady=5)

# Search label and entry field
search_label = ttk.Label(root, text="Search within Scraped Content:")
search_label.pack(pady=5)
search_entry = ttk.Entry(root, width=50)
search_entry.pack(pady=5)

# Search, Previous, Next, Export Search buttons
search_button_frame = ttk.Frame(root)
search_button_frame.pack(pady=10)

# Create and place buttons for searching, navigating matches, and exporting search results
search_button = ttk.Button(search_button_frame, text="Search",
                           command=lambda: search_within_text(text_area, search_entry, search_matches))
search_button.grid(row=0, column=0, padx=5)

previous_button = ttk.Button(search_button_frame, text="Previous",
                             command=lambda: previous_match(text_area, search_matches, [current_match_index]))
previous_button.grid(row=0, column=1, padx=5)

next_button = ttk.Button(search_button_frame, text="Next",
                         command=lambda: next_match(text_area, search_matches, [current_match_index]))
next_button.grid(row=0, column=2, padx=5)

export_button = ttk.Button(search_button_frame, text="Export Search", command=export_search)
export_button.grid(row=0, column=3, padx=5)

# Parse Options: Buttons for parsing data (Text, Links, Images, Tables)
parse_button_frame = ttk.Frame(root)
parse_button_frame.pack(pady=10)

# Create and place buttons for parsing different types of content
parse_text_button = ttk.Button(parse_button_frame, text="Parse Text", command=lambda: parse_data("text"))
parse_text_button.grid(row=0, column=0, padx=5)

parse_links_button = ttk.Button(parse_button_frame, text="Parse Links", command=lambda: parse_data("links"))
parse_links_button.grid(row=0, column=1, padx=5)

parse_images_button = ttk.Button(parse_button_frame, text="Parse Images", command=lambda: parse_data("images"))
parse_images_button.grid(row=0, column=2, padx=5)

parse_tables_button = ttk.Button(parse_button_frame, text="Parse Tables", command=lambda: parse_data("tables"))
parse_tables_button.grid(row=0, column=3, padx=5)

# Bind key press event to trigger actions via hotkeys
root.bind("<Key>", on_key_press)

# Run the GUI loop (start the application)
root.mainloop()
