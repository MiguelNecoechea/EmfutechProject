import tkinter as tk
from tkinter import ttk

# Create the main window
root = tk.Tk()
root.title("Study Management Interface")
root.geometry("1000x600")
root.configure(bg="#E8EAF6")

# Sidebar Frame
sidebar_frame = tk.Frame(root, bg="#C5CAE9", width=200, height=600)
sidebar_frame.pack(side="left", fill="y")

# Sidebar options
options = ["Dashboard", "Experiment", "Measurement", "Reports", "Study Management", "Configuration", "File Manager", "Account", "Support"]
for option in options:
    button = tk.Button(sidebar_frame, text=option, bg="#C5CAE9", bd=0, anchor="w", padx=10)
    button.pack(fill="x", pady=5)

# Main Content Frame
content_frame = tk.Frame(root, bg="white")
content_frame.pack(side="right", expand=True, fill="both")

# Top Bar with Dropdown Menus
top_bar_frame = tk.Frame(content_frame, bg="#C5CAE9", height=50)
top_bar_frame.pack(side="top", fill="x")

menu_items = ["Study Name", "Description", "Study Objectives", "Study Duration"]
for item in menu_items:
    menu_button = tk.Menubutton(top_bar_frame, text=item, bg="#C5CAE9", bd=0, relief="raised", padx=10)
    menu_button.pack(side="left", padx=10)

# Search Bar
search_entry = tk.Entry(top_bar_frame, bg="white", width=20)
search_entry.pack(side="right", padx=10)
search_icon = tk.Label(top_bar_frame, text="🔍", bg="#C5CAE9")
search_icon.pack(side="right")

# Page Label
page_label = tk.Label(content_frame, text="Page / Study Management", bg="white", font=("Arial", 16))
page_label.pack(anchor="w", padx=20, pady=10)

# Menu with Assign Groups, Segmentation, Group Editing
menu_frame = tk.Frame(content_frame, bg="white")
menu_frame.pack(anchor="w", padx=20)

menu_options = ["Assign Groups", "Segmentation", "Group Editing"]
for option in menu_options:
    button = tk.Menubutton(menu_frame, text=option, bg="white", bd=1, relief="raised", padx=10)
    button.pack(side="left", padx=5)

# Content Area for Study Management
study_management_frame = tk.Frame(content_frame, bg="white", bd=2, relief="solid", padx=20, pady=20)
study_management_frame.pack(expand=True, fill="both", padx=20, pady=20)

# Left Column
left_frame = tk.Frame(study_management_frame, bg="white")
left_frame.pack(side="left", expand=True, fill="both")

study_status_label = tk.Label(left_frame, text="Study Status", bg="white", font=("Arial", 14))
study_status_label.pack(padx=10, pady=10, anchor="w")

participant_progress_label = tk.Label(left_frame, text="Participant Progress", bg="white", font=("Arial", 14))
participant_progress_label.pack(padx=10, pady=10, anchor="w")

# Right Column
right_frame = tk.Frame(study_management_frame, bg="white")
right_frame.pack(side="right", expand=True, fill="both")

study_dashboard_label = tk.Label(right_frame, text="Study Dashboard", bg="white", font=("Arial", 14))
study_dashboard_label.pack(padx=10, pady=10, anchor="w")

results_management_label = tk.Label(right_frame, text="Results Management", bg="white", font=("Arial", 14))
results_management_label.pack(padx=10, pady=10, anchor="w")

# Start the main loop
root.mainloop()
