import tkinter as tk
from tkinter import ttk

class ExperimentApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configurar la ventana principal
        self.title("Experiment Setup")
        self.geometry("1200x800")
        self.configure(bg="#E8EAF6")  # Manteniendo el color de fondo principal

        # Crear los frames principales
        self.create_sidebar()
        self.create_topbar()
        self.create_content()

    def create_sidebar(self):
        # Barra lateral con el estilo consistente
        sidebar = tk.Frame(self, bg="#C5CAE9", width=250)
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

        # Pestañas en la barra superior
        btn_new_experiment = tk.Button(topbar, text="Create new experiment", width=20, bg="#C5CAE9", font=("Arial", 10))
        btn_new_experiment.pack(side="left", padx=10)

        btn_experiment_setup = tk.Button(topbar, text="Experiment Setup", width=20, bg="#C5CAE9", font=("Arial", 10))
        btn_experiment_setup.pack(side="left")

        btn_experiment_history = tk.Button(topbar, text="Experiment history", width=20, bg="#C5CAE9", font=("Arial", 10))
        btn_experiment_history.pack(side="left")

    def create_content(self):
        # Área de contenido principal, con estilo y colores consistentes
        content_frame = tk.Frame(self, bg="white")
        content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Título de la página
        lbl_page = tk.Label(content_frame, text="Page / Experiment", font=("Arial", 16), bg="white")
        lbl_page.grid(row=0, column=0, padx=10, pady=10)

        # Crear la sección "Record" con un marco
        record_frame = tk.Frame(content_frame, bg="white", relief="solid", bd=2)
        record_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)

        # Configuración del formulario del experimento, con coherencia en el diseño
        lbl_experiment_name = tk.Label(record_frame, text="Experiment Name", bg="white", font=("Arial", 12))
        lbl_experiment_name.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        entry_experiment_name = tk.Entry(record_frame, width=40)
        entry_experiment_name.grid(row=0, column=1, padx=10, pady=10)

        lbl_description = tk.Label(record_frame, text="Description", bg="white", font=("Arial", 12))
        lbl_description.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        entry_description = tk.Entry(record_frame, width=40)
        entry_description.grid(row=1, column=1, padx=10, pady=10)

        lbl_objective = tk.Label(record_frame, text="Objective", bg="white", font=("Arial", 12))
        lbl_objective.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        combo_objective = ttk.Combobox(record_frame, values=["Purpose and Goals"], width=37)
        combo_objective.grid(row=2, column=1, padx=10, pady=10)

        lbl_duration = tk.Label(record_frame, text="Duration of the experiment", bg="white", font=("Arial", 12))
        lbl_duration.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        combo_duration = ttk.Combobox(record_frame, values=["Estimated Time"], width=37)
        combo_duration.grid(row=3, column=1, padx=10, pady=10)

        lbl_participants = tk.Label(record_frame, text="Participants", bg="white", font=("Arial", 12))
        lbl_participants.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        combo_participants = ttk.Combobox(record_frame, values=["Individual / Groups"], width=37)
        combo_participants.grid(row=4, column=1, padx=10, pady=10)

        # Configuración adicional de sensores
        lbl_active_sensors = tk.Label(record_frame, text="Active Sensors", bg="white", font=("Arial", 12))
        lbl_active_sensors.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        combo_sensors = ttk.Combobox(record_frame, values=["Select Sensors"], width=20)
        combo_sensors.grid(row=0, column=3, padx=10, pady=10)

        lbl_signals_capture = tk.Label(record_frame, text="Type of Signals to Capture", bg="white", font=("Arial", 12))
        lbl_signals_capture.grid(row=1, column=2, padx=10, pady=10, sticky="w")

        # Señales a capturar
        chk_brain = tk.Checkbutton(record_frame, text="Brain activity", bg="white")
        chk_brain.grid(row=2, column=2, padx=10, pady=5)

        chk_concentration = tk.Checkbutton(record_frame, text="Concentration", bg="white")
        chk_concentration.grid(row=2, column=3, padx=10, pady=5)

        chk_emotions = tk.Checkbutton(record_frame, text="Emotions", bg="white")
        chk_emotions.grid(row=2, column=4, padx=10, pady=5)

        # Configuración de estímulos
        lbl_stimulus = tk.Label(record_frame, text="Stimulus Configuration", bg="white", font=("Arial", 12))
        lbl_stimulus.grid(row=3, column=2, padx=10, pady=10, sticky="w")
        combo_stimulus = ttk.Combobox(record_frame, values=["Images / videos / sounds"], width=20)
        combo_stimulus.grid(row=3, column=3, padx=10, pady=10)

        # Frecuencia de medición
        lbl_frequency = tk.Label(record_frame, text="Frecuencia de Medición", bg="white", font=("Arial", 12))
        lbl_frequency.grid(row=4, column=2, padx=10, pady=10, sticky="w")
        combo_frequency = ttk.Combobox(record_frame, values=["1 second / 10 seconds"], width=20)
        combo_frequency.grid(row=4, column=3, padx=10, pady=10)

        # Área de Signos
        lbl_sign = tk.Label(record_frame, text="Sign", bg="white", font=("Arial", 12))
        lbl_sign.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        text_sign = tk.Text(record_frame, height=5, width=60)
        text_sign.grid(row=6, column=0, columnspan=4, padx=10, pady=10)

    # Métodos para manejar eventos de menú
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
    app = ExperimentApp()
    app.mainloop()
