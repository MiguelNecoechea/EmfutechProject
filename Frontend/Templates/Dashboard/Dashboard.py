import tkinter as tk
from tkinter import ttk

class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configurar la ventana principal
        self.title("Dashboard")
        self.geometry("1200x800")
        self.configure(bg="#E8EAF6")  # Manteniendo el color de fondo coherente

        # Crear los frames principales
        self.create_sidebar()
        self.create_topbar()
        self.create_content()

    def create_sidebar(self):
        # Barra lateral con el estilo guardado
        sidebar = tk.Frame(self, bg="#C5CAE9", width=250, height=800)
        sidebar.pack(side="left", fill="y")

        # Opciones en la barra lateral
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Experiment", self.show_experiment),
            ("Measurement", self.show_measurement),
            ("Reports", self.show_reports),
            ("Study Management", self.show_study_management),
            ("Configuration", self.show_configuration),
            ("File Manager", self.show_file_manager),
            ("Account", self.show_account),
            ("Support", self.show_support)
        ]

        for text, command in buttons:
            btn = tk.Button(sidebar, text=text, bg="#C5CAE9", bd=0, anchor="w", padx=10, font=("Arial", 10))
            btn.pack(fill="x", pady=5)

    def create_topbar(self):
        # Barra superior con el estilo guardado
        topbar = tk.Frame(self, bg="#C5CAE9", height=50)
        topbar.pack(side="top", fill="x")

        # Título de la página
        lbl_title = tk.Label(topbar, text="Page / Dashboard", font=("Arial", 16), bg="#C5CAE9")
        lbl_title.pack(side="left", padx=10)

        # Botones de control estilo guardado
        btn_start = tk.Button(topbar, text="Start", width=10)
        btn_start.pack(side="right", padx=10)

        btn_pause = tk.Button(topbar, text="Pause", width=10)
        btn_pause.pack(side="right")

        btn_stop = tk.Button(topbar, text="Stop", width=10)
        btn_stop.pack(side="right")

    def create_content(self):
        # Área principal del contenido, con el color de fondo en blanco para las áreas principales
        content_frame = tk.Frame(self, bg="white")
        content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Tabs en el área de contenido
        tab_control = ttk.Notebook(content_frame)
        
        # Crear pestañas con el estilo y color de fondo blanco
        tab_summary = ttk.Frame(tab_control)
        tab_real_time_status = ttk.Frame(tab_control)
        tab_key_indicators = ttk.Frame(tab_control)
        tab_metrics = ttk.Frame(tab_control)
        
        tab_control.add(tab_summary, text="Summary")
        tab_control.add(tab_real_time_status, text="Real-time status")
        tab_control.add(tab_key_indicators, text="Key indicators")
        tab_control.add(tab_metrics, text="Metrics")

        tab_control.pack(expand=1, fill="both")

        # Secciones dentro de la primera pestaña (Summary)
        lbl_live_feeds = tk.Label(tab_summary, text="Live Feeds", font=("Arial", 14), bg="white")
        lbl_live_feeds.pack(anchor="w", padx=20, pady=10)

        feeds_frame = tk.Frame(tab_summary, bg="white")
        feeds_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Cuadros de señales siguiendo el diseño que ya analizamos
        for row in range(2):
            for col in range(2):
                signal_box = tk.Label(feeds_frame, text="Signs", width=20, height=5, relief="groove", font=("Arial", 12))
                signal_box.grid(row=row, column=col, padx=20, pady=20)

    # Métodos para las diferentes opciones del menú
    def show_dashboard(self):
        print("Dashboard selected")

    def show_experiment(self):
        print("Experiment selected")

    def show_measurement(self):
        print("Measurement selected")

    def show_reports(self):
        print("Reports selected")

    def show_study_management(self):
        print("Study Management selected")

    def show_configuration(self):
        print("Configuration selected")

    def show_file_manager(self):
        print("File Manager selected")

    def show_account(self):
        print("Account selected")

    def show_support(self):
        print("Support selected")

if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
