import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

# Función para abrir el cuadro de diálogo de selección de archivos
def open_file():
    file_path = filedialog.askopenfilename(title="Selecciona un archivo")
    if file_path:
        file_listbox.insert(tk.END, file_path)

# Crear la ventana principal
root = tk.Tk()
root.title("Gestor de Archivos")
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
page_label = tk.Label(content_frame, text="Página / Gestor de Archivos", bg="white", font=("Arial", 16))
page_label.pack(anchor="w", padx=20, pady=10)

# Menú con Asignar Grupos, Segmentación, Edición de Grupos
menu_frame = tk.Frame(content_frame, bg="white")
menu_frame.pack(anchor="w", padx=20)

menu_options = ["Asignar Grupos", "Segmentación", "Edición de Grupos"]
for option in menu_options:
    button = tk.Menubutton(menu_frame, text=option, bg="white", bd=1, relief="raised", padx=10)
    button.pack(side="left", padx=5)

# Área de contenido para la gestión de archivos
file_manager_frame = tk.Frame(content_frame, bg="white", bd=2, relief="solid", padx=20, pady=20)
file_manager_frame.pack(expand=True, fill="both", padx=20, pady=20)

# Sección de búsqueda con campos de entrada y etiquetas
search_frame = tk.Frame(file_manager_frame, bg="white")
search_frame.pack(fill="x", pady=10)

study_name_label = tk.Label(search_frame, text="Nombre del Estudio", bg="white", font=("Arial", 12))
study_name_label.grid(row=0, column=0, padx=10, pady=5)

description_label = tk.Label(search_frame, text="Descripción", bg="white", font=("Arial", 12))
description_label.grid(row=0, column=1, padx=10, pady=5)

objectives_label = tk.Label(search_frame, text="Objetivos del Estudio", bg="white", font=("Arial", 12))
objectives_label.grid(row=0, column=2, padx=10, pady=5)

duration_label = tk.Label(search_frame, text="Duración del Estudio", bg="white", font=("Arial", 12))
duration_label.grid(row=0, column=3, padx=10, pady=5)

# Aquí puedes añadir las cajas de entrada para búsqueda si lo necesitas
search_name_entry = tk.Entry(search_frame, bg="white", width=15)
search_name_entry.grid(row=1, column=0, padx=10)

search_description_entry = tk.Entry(search_frame, bg="white", width=15)
search_description_entry.grid(row=1, column=1, padx=10)

search_objectives_entry = tk.Entry(search_frame, bg="white", width=15)
search_objectives_entry.grid(row=1, column=2, padx=10)

search_duration_entry = tk.Entry(search_frame, bg="white", width=15)
search_duration_entry.grid(row=1, column=3, padx=10)

# Lista para mostrar los archivos seleccionados
file_listbox = tk.Listbox(file_manager_frame, bg="white", width=80, height=10)
file_listbox.pack(pady=10)

# Botón para abrir el diálogo de archivos
browse_button = tk.Button(file_manager_frame, text="Buscar Archivos", command=open_file)
browse_button.pack()

# Iniciar el loop principal
root.mainloop()
