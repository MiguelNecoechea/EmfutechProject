import tkinter as tk
from tkinter import ttk

# Crear la ventana principal
root = tk.Tk()
root.title("Dashboard")
root.geometry("1200x800")
root.configure(bg="#E8EAF6")

# Crear el marco de la barra lateral
sidebar_frame = tk.Frame(root, bg="#C5CAE9", width=200)
sidebar_frame.pack(side="left", fill="y")

# Opciones de la barra lateral
sidebar_options = ["Dashboard", "Experiment", "Measurement", "Reports", "Study Management", "Configuration", "File Manager", "Account", "Support"]
for option in sidebar_options:
    btn = tk.Button(sidebar_frame, text=option, bg="#C5CAE9", bd=0, anchor="w", padx=10, font=("Arial", 10))
    btn.pack(fill="x", pady=5)

# Crear el marco del contenido principal
content_frame = tk.Frame(root, bg="white")
content_frame.pack(side="right", expand=True, fill="both")

# Barra superior con pestañas
tab_frame = tk.Frame(content_frame, bg="#C5CAE9", height=50)
tab_frame.pack(side="top", fill="x")

tab_titles = ["Summary", "Real-time status", "Key indicators", "Metrics"]
for title in tab_titles:
    tab_button = tk.Button(tab_frame, text=title, bg="#C5CAE9", bd=0, padx=10, pady=5, font=("Arial", 10))
    tab_button.pack(side="left", padx=5, pady=10)

# Botones de control (Start, Stop, etc.)
control_frame = tk.Frame(tab_frame, bg="#C5CAE9")
control_frame.pack(side="right", padx=10)

btn_start = tk.Button(control_frame, text="Start", width=6)
btn_start.pack(side="right", padx=5)

btn_pause = tk.Button(control_frame, text="Pause", width=6)
btn_pause.pack(side="right", padx=5)

btn_stop = tk.Button(control_frame, text="Stop", width=6)
btn_stop.pack(side="right", padx=5)

# Etiqueta de la página
page_label = tk.Label(content_frame, text="Page / Dashboard", bg="white", font=("Arial", 16))
page_label.pack(anchor="w", padx=20, pady=10)

# Sección de Live Feeds
live_feeds_label = tk.Label(content_frame, text="Live Feeds", bg="white", font=("Arial", 14))
live_feeds_label.pack(anchor="w", padx=20)

feeds_frame = tk.Frame(content_frame, bg="white")
feeds_frame.pack(padx=20, pady=10)

# Cuadros de señales
for row in range(2):
    for col in range(2):
        signal_box = tk.Label(feeds_frame, text="Signs", width=20, height=5, relief="groove", font=("Arial", 12))
        signal_box.grid(row=row, column=col, padx=20, pady=20)

root.mainloop()
