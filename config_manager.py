import os
import json
from typing import Dict, List, Set, Any, Optional

from path_utils import normalize_path

class ConfigManager:
    """Gestor de configuración para la aplicación LLM Export Tool"""
    
    def __init__(self):
        """Inicializa un nuevo gestor de configuración"""
        # Datos de estado
        self.current_folder = ""
        self.last_export_location = ""
        self.recent_folders = []
        self.selections = {}  # {carpeta: [archivos_seleccionados]}
        self.language = "en"
        
        # Filtros por carpeta
        self.folder_filters = {}  # {carpeta: {"include_patterns": "", "exclude_patterns": ""}}
        
        # Archivo de configuración en el directorio del usuario
        self.config_file = os.path.join(os.path.expanduser("~"), ".llm_export_config.json")
    
    def load_config(self) -> None:
        """Carga la configuración guardada desde el archivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Normalizar rutas de carpetas recientes para eliminar duplicados
                raw_recent_folders = config.get('recent_folders', [])
                normalized_paths = {}
                
                # Eliminar duplicados manteniendo el orden y convirtiendo a rutas absolutas
                for path in raw_recent_folders:
                    try:
                        # Convertir a ruta absoluta (si no lo es ya)
                        abs_path = os.path.abspath(path)
                        normalized_paths[normalize_path(abs_path)] = abs_path
                    except Exception:
                        # Si falla la conversión a ruta absoluta, ignorar esta entrada
                        pass
                
                # Mantener solo las rutas originales absolutas, sin duplicados
                self.recent_folders = list(normalized_paths.values())
                
                self.last_export_location = config.get('last_export_location', '')
                
                # Convertir claves del diccionario selections a rutas absolutas
                selections_orig = config.get('selections', {})
                self.selections = {}
                for path, selected in selections_orig.items():
                    try:
                        abs_path = os.path.abspath(path)
                        self.selections[abs_path] = selected
                    except Exception:
                        # Si no se puede convertir, usar la ruta original
                        self.selections[path] = selected
                
                # Cargar preferencia de idioma
                language = config.get('language')
                if language in ('en', 'es'):
                    self.language = language
                
                # Cargar filtros por carpeta
                self.folder_filters = config.get('folder_filters', {})
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
    
    def save_config(self) -> None:
        """Guarda la configuración en el archivo JSON"""
        config = {
            'recent_folders': self.recent_folders,
            'last_export_location': self.last_export_location,
            'selections': self.selections,
            'language': self.language,
            'folder_filters': self.folder_filters
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
    
    def add_recent_folder(self, folder_path: str) -> None:
        """
        Añade una carpeta a la lista de recientes
        
        Args:
            folder_path: Ruta de la carpeta a añadir
        """
        # Convertir a ruta absoluta
        folder_path = os.path.abspath(folder_path)
        
        # Normalizar la ruta para comparación
        normalized_path = normalize_path(folder_path)
        
        # Verificar si ya existe
        normalized_recent_folders = [normalize_path(path) for path in self.recent_folders]
        if normalized_path in normalized_recent_folders:
            # Eliminar la entrada existente (podría tener otro formato de separador)
            index = normalized_recent_folders.index(normalized_path)
            self.recent_folders.pop(index)
        
        # Añadir al inicio y limitar a 10 carpetas
        self.recent_folders.insert(0, folder_path)
        self.recent_folders = self.recent_folders[:10]
        
        # Guardar configuración
        self.save_config()
    
    def set_current_folder(self, folder_path: str) -> None:
        """
        Establece la carpeta actual
        
        Args:
            folder_path: Ruta de la carpeta actual
        """
        self.current_folder = folder_path
        self.add_recent_folder(folder_path)
    
    def save_selection(self, selected_paths: Set[str]) -> None:
        """
        Guarda la selección actual para la carpeta abierta
        
        Args:
            selected_paths: Conjunto de rutas seleccionadas
        """
        if self.current_folder:
            self.selections[self.current_folder] = list(selected_paths)
            self.save_config()
    
    def get_selection(self, folder_path: str) -> List[str]:
        """
        Obtiene la selección guardada para una carpeta
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            Lista de rutas seleccionadas o lista vacía si no hay selección
        """
        return self.selections.get(folder_path, [])
    
    def set_folder_filters(self, folder_path: str, include_patterns: str, exclude_patterns: str) -> None:
        """
        Guarda los filtros para una carpeta específica
        
        Args:
            folder_path: Ruta de la carpeta
            include_patterns: Patrones de inclusión
            exclude_patterns: Patrones de exclusión
        """
        self.folder_filters[folder_path] = {
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns
        }
        self.save_config()
    
    def get_folder_filters(self, folder_path: str) -> Dict[str, str]:
        """
        Obtiene los filtros guardados para una carpeta
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            Diccionario con patrones de inclusión y exclusión
        """
        return self.folder_filters.get(folder_path, {
            "include_patterns": "",
            "exclude_patterns": ""
        })
    
    def set_language(self, language: str) -> None:
        """
        Establece el idioma de la aplicación
        
        Args:
            language: Código de idioma ('en' o 'es')
        """
        if language in ('en', 'es'):
            self.language = language
            self.save_config()
    
    def set_export_location(self, location: str) -> None:
        """
        Establece la última ubicación de exportación
        
        Args:
            location: Ruta del directorio de exportación
        """
        self.last_export_location = location
        self.save_config()