import tkinter as tk
from tkinter import ttk

class MeasurementApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configurar la ventana principal
        self.title("Measurement Setup")
        self.geometry("1200x800")
        self.configure(bg="#E8EAF6")

        # Crear los frames principales
        self.create_sidebar()
        self.create_topbar()
        self.create_content()

    def create_sidebar(self):
        # Barra lateral
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
        # Barra superior
        topbar = tk.Frame(self, bg="#C5CAE9", height=50)
        topbar.pack(side="top", fill="x")

        # Pestañas en la barra superior
        btn_selection = tk.Button(topbar, text="Selection", bg="#C5CAE9", font=("Arial", 10))
        btn_selection.pack(side="left", padx=10)

        btn_frequency_setting = tk.Button(topbar, text="Frequency Setting", bg="#C5CAE9", font=("Arial", 10))
        btn_frequency_setting.pack(side="left")

        btn_calibration = tk.Button(topbar, text="Calibration", bg="#C5CAE9", font=("Arial", 10))
        btn_calibration.pack(side="left")

    def create_content(self):
        # Área de contenido principal
        content_frame = tk.Frame(self, bg="white")
        content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Título de la página
        lbl_page = tk.Label(content_frame, text="Page / Measurement", font=("Arial", 16), bg="white")
        lbl_page.pack(anchor="w", padx=20, pady=10)

        # Crear la sección "Test"
        test_frame = tk.Frame(content_frame, bg="white", relief="solid", bd=2, padx=20, pady=20)
        test_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Título de Test
        lbl_test = tk.Label(test_frame, text="Test", font=("Arial", 14), bg="white")
        lbl_test.grid(row=0, column=0, padx=10, pady=10)

        # Opciones de prueba
        lbl_real_time = tk.Label(test_frame, text="Real-Time Monitoring", font=("Arial", 12), bg="white")
        lbl_real_time.grid(row=1, column=0, padx=10, pady=20, sticky="w")

        lbl_eeg = tk.Label(test_frame, text="EEG", font=("Arial", 12), bg="white")
        lbl_eeg.grid(row=1, column=1, padx=50, pady=20)

        lbl_eye_tracking = tk.Label(test_frame, text="Eye Tracking", font=("Arial", 12), bg="white")
        lbl_eye_tracking.grid(row=2, column=0, padx=10, pady=20, sticky="w")

        lbl_emotional_response = tk.Label(test_frame, text="Emotional Response", font=("Arial", 12), bg="white")
        lbl_emotional_response.grid(row=2, column=1, padx=50, pady=20)

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
    app = MeasurementApp()
    app.mainloop()
