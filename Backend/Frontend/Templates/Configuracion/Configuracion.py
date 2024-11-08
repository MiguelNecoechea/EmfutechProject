import tkinter as tk
from tkinter import ttk

# Crear la ventana principal
root = tk.Tk()
root.title("Interfaz de Configuración")
root.geometry("1200x700")
root.configure(bg="#E8EAF6")

# Sidebar Frame
sidebar_frame = tk.Frame(root, bg="#C5CAE9", width=200, height=700)
sidebar_frame.pack(side="left", fill="y")

# Opciones de la barra lateral
options = ["Dashboard", "Experimento", "Medición", "Reportes", "Gestión de Estudio", "Configuración", "Gestor de Archivos", "Cuenta", "Soporte"]
for option in options:
    button = tk.Button(sidebar_frame, text=option, bg="#C5CAE9", bd=0, anchor="w", padx=10)
    button.pack(fill="x", pady=5)

# Frame de contenido principal
content_frame = tk.Frame(root, bg="white")
content_frame.pack(side="right", expand=True, fill="both")

# Barra superior con menús desplegables
top_bar_frame = tk.Frame(content_frame, bg="#C5CAE9", height=50)
top_bar_frame.pack(side="top", fill="x")

menu_items = ["Nombre del Estudio", "Descripción", "Objetivos del Estudio", "Duración del Estudio"]
for item in menu_items:
    menu_button = tk.Menubutton(top_bar_frame, text=item, bg="#C5CAE9", bd=0, relief="raised", padx=10)
    menu_button.pack(side="left", padx=10)

# Barra de búsqueda
search_entry = tk.Entry(top_bar_frame, bg="white", width=20)
search_entry.pack(side="right", padx=10)
search_icon = tk.Label(top_bar_frame, text="🔍", bg="#C5CAE9")
search_icon.pack(side="right")

# Etiqueta de página
page_label = tk.Label(content_frame, text="Página / Configuración", bg="white", font=("Arial", 16))
page_label.pack(anchor="w", padx=20, pady=10)

# Menú con Asignar Grupos, Segmentación, Edición de Grupos
menu_frame = tk.Frame(content_frame, bg="white")
menu_frame.pack(anchor="w", padx=20)

menu_options = ["Asignar Grupos", "Segmentación", "Edición de Grupos"]
for option in menu_options:
    button = tk.Menubutton(menu_frame, text=option, bg="white", bd=1, relief="raised", padx=10)
    button.pack(side="left", padx=5)

# Área de contenido para la gestión del estudio
configuracion_frame = tk.Frame(content_frame, bg="white", bd=2, relief="solid", padx=20, pady=20)
configuracion_frame.pack(expand=True, fill="both", padx=20, pady=20)

# Columna Izquierda
left_frame = tk.Frame(configuracion_frame, bg="white")
left_frame.pack(side="left", expand=True, fill="both")

# Configuración de dispositivos
device_settings_label = tk.Label(left_frame, text="Configuración del Dispositivo", bg="white", font=("Arial", 14))
device_settings_label.pack(padx=10, pady=10, anchor="w")

connected_device_label = tk.Label(left_frame, text="Selección de Dispositivo Conectado", bg="white", font=("Arial", 12))
connected_device_label.pack(padx=10, pady=5, anchor="w")

check_eeg = tk.Checkbutton(left_frame, text="EEG", bg="white")
check_eeg.pack(padx=10, anchor="w")

check_eyes = tk.Checkbutton(left_frame, text="Seguimiento Ocular", bg="white")
check_eyes.pack(padx=10, anchor="w")

check_emotions = tk.Checkbutton(left_frame, text="Emociones", bg="white")
check_emotions.pack(padx=10, anchor="w")

# Frecuencia de captura de señales
signal_capture_label = tk.Label(left_frame, text="Frecuencia de Captura de Señales", bg="white", font=("Arial", 12))
signal_capture_label.pack(padx=10, pady=10, anchor="w")

frequency_dropdown = ttk.Combobox(left_frame, values=["1 segundo / 10 segundos"])
frequency_dropdown.pack(padx=10, anchor="w")

# Configuración de umbrales
threshold_label = tk.Label(left_frame, text="Configuración de Umbrales", bg="white", font=("Arial", 12))
threshold_label.pack(padx=10, pady=10, anchor="w")

threshold_dropdown = ttk.Combobox(left_frame, values=["Límite mínimo de atención"])
threshold_dropdown.pack(padx=10, anchor="w")

# Columna Derecha
right_frame = tk.Frame(configuracion_frame, bg="white")
right_frame.pack(side="right", expand=True, fill="both")

study_dashboard_label = tk.Label(right_frame, text="Panel de Control del Estudio", bg="white", font=("Arial", 14))
study_dashboard_label.pack(padx=10, pady=10, anchor="w")

results_management_label = tk.Label(right_frame, text="Gestión de Resultados", bg="white", font=("Arial", 14))
results_management_label.pack(padx=10, pady=10, anchor="w")

# Progreso de los participantes
participant_progress_label = tk.Label(left_frame, text="Progreso de los Participantes", bg="white", font=("Arial", 14))
participant_progress_label.pack(padx=10, pady=10, anchor="w")

# Ejecutar el loop principal
root.mainloop()

