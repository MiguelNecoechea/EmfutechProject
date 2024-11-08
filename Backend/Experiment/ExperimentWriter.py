import os
import json
from datetime import datetime
import eel
from typing import Dict, Any

class ExperimentWriter:
    """
    Clase para manejar la escritura y lectura de datos de experimentos.
    Almacena los experimentos en la carpeta AuraBridge.
    """
    def __init__(self):
        """Inicializa el ExperimentWriter y crea la carpeta AuraBridge si no existe."""
        self.base_path = os.path.join(os.getcwd(), 'AuraBridge')
        self.ensure_directory_exists()
        self.register_eel_functions()

    def ensure_directory_exists(self) -> None:
        """Asegura que exista el directorio AuraBridge."""
        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
                print(f"Directorio creado: {self.base_path}")
        except Exception as e:
            print(f"Error al crear directorio: {str(e)}")

    def register_eel_functions(self) -> None:
        """Registra las funciones para ser accesibles desde JavaScript."""
        eel.expose(self.save_experiment)
        eel.expose(self.load_experiment)
        eel.expose(self.list_experiments)
        eel.expose(self.delete_experiment)
        print("Funciones Eel registradas")

    @eel.expose
    def save_experiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Guarda un nuevo experimento.
        
        Args:
            data: Diccionario con los datos del experimento
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Validar datos mínimos requeridos
            if not data.get('experimentName'):
                return {
                    'success': False,
                    'error': 'Nombre del experimento requerido',
                    'message': 'Debe proporcionar un nombre para el experimento'
                }

            # Generar nombre de archivo
            filename = self._generate_filename(data['experimentName'])
            file_path = os.path.join(self.base_path, filename)

            # Agregar metadatos
            experiment_data = {
                **data,
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'file_path': file_path,
                    'status': 'created'
                }
            }

            # Guardar archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(experiment_data, f, indent=2, ensure_ascii=False)

            return {
                'success': True,
                'data': experiment_data,
                'message': 'Experimento guardado exitosamente',
                'file_path': file_path
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al guardar el experimento'
            }

    def _generate_filename(self, experiment_name: str) -> str:
        """
        Genera un nombre de archivo único para el experimento.
        
        Args:
            experiment_name: Nombre base del experimento
            
        Returns:
            Nombre de archivo único con timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in experiment_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return f"{safe_name}_{timestamp}.json"

    @eel.expose
    def load_experiment(self, filename: str) -> Dict[str, Any]:
        """
        Carga un experimento existente.
        
        Args:
            filename: Nombre del archivo a cargar
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            file_path = os.path.join(self.base_path, filename)
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'Archivo no encontrado',
                    'message': f'No se encontró el archivo: {filename}'
                }

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'success': True,
                    'data': data,
                    'message': 'Experimento cargado exitosamente'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al cargar el experimento'
            }

    @eel.expose
    def list_experiments(self) -> Dict[str, Any]:
        """
        Lista todos los experimentos guardados.
        
        Returns:
            Dict con la lista de experimentos
        """
        try:
            if not os.path.exists(self.base_path):
                return {
                    'success': True,
                    'data': [],
                    'message': 'No hay experimentos guardados'
                }

            experiments = []
            for filename in os.listdir(self.base_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.base_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        experiments.append({
                            'filename': filename,
                            'name': data.get('experimentName', 'Sin nombre'),
                            'created_at': data.get('metadata', {}).get('created_at', ''),
                            'status': data.get('metadata', {}).get('status', '')
                        })

            return {
                'success': True,
                'data': experiments,
                'message': f'Se encontraron {len(experiments)} experimentos'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al listar experimentos'
            }

    @eel.expose
    def delete_experiment(self, filename: str) -> Dict[str, Any]:
        """
        Elimina un experimento existente.
        
        Args:
            filename: Nombre del archivo a eliminar
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            file_path = os.path.join(self.base_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return {
                    'success': True,
                    'message': f'Experimento {filename} eliminado exitosamente'
                }
            return {
                'success': False,
                'error': 'Archivo no encontrado',
                'message': f'No se encontró el archivo: {filename}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al eliminar el experimento'
            }

# Inicialización cuando se importa el módulo
writer = ExperimentWriter()