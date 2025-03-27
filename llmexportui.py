import os
import sys
import json
import locale
import argparse  # Nuevo import
from typing import Set, Dict, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTreeView, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLineEdit, QLabel, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction

# Diccionarios de traducción
TRANSLATIONS = {
    'en': {
        'app_title': 'LLM Export Tool',
        'file_menu': 'File',
        'open_folder': 'Open Folder',
        'recent_folders': 'Recent Folders',
        'exit': 'Exit',
        'options_menu': 'Options',
        'reset_selection': 'Reset Selection',
        'filter_label': 'Filter:',
        'filter_placeholder': 'Filter by extension (e.g.: *.py, *.md)',
        'open_folder_button': 'Open Folder',
        'reset_button': 'Reset Selection',
        'export_button': 'Export',
        'error': 'Error',
        'success': 'Success',
        'no_folder_open': 'No folder is open.',
        'no_files_selected': 'No files selected for export.',
        'save_as': 'Save as',
        'export_success': 'File exported successfully to:',
        'export_error': 'Error exporting:',
        'language_menu': 'Language',
        'english': 'English',
        'spanish': 'Spanish',
    },
    'es': {
        'app_title': 'Exportador para LLM',
        'file_menu': 'Archivo',
        'open_folder': 'Abrir Carpeta',
        'recent_folders': 'Carpetas Recientes',
        'exit': 'Salir',
        'options_menu': 'Opciones',
        'reset_selection': 'Reiniciar Selección',
        'filter_label': 'Filtro:',
        'filter_placeholder': 'Filtrar por extensión (ej: *.py, *.md)',
        'open_folder_button': 'Abrir Carpeta',
        'reset_button': 'Reiniciar Selección',
        'export_button': 'Exportar',
        'error': 'Error',
        'success': 'Éxito',
        'no_folder_open': 'No hay ninguna carpeta abierta.',
        'no_files_selected': 'No hay archivos seleccionados para exportar.',
        'save_as': 'Guardar como',
        'export_success': 'Archivo exportado con éxito a:',
        'export_error': 'Error al exportar:',
        'language_menu': 'Idioma',
        'english': 'Inglés',
        'spanish': 'Español',
    }
}

def get_system_language():
    """Detecta el idioma del sistema operativo."""
    try:
        # Método actualizado para evitar la advertencia de deprecación
        locale.setlocale(locale.LC_ALL, '')
        lang_code = locale.getlocale()[0]
        if lang_code and lang_code.startswith('es'):
            return 'es'
            
        # Alternativa para sistemas donde getlocale() podría no funcionar
        import os
        env_lang = os.environ.get('LANG', '') or os.environ.get('LANGUAGE', '') or os.environ.get('LC_ALL', '')
        if env_lang and env_lang.startswith('es'):
            return 'es'
    except Exception:
        pass
    return 'en'


class LLMExportApp(QMainWindow):
    """Aplicación para exportar archivos en formato amigable para LLMs."""
    
    def __init__(self):
        super().__init__()
        
        # Datos de estado
        self.current_folder = ""
        self.last_export_location = ""
        self.recent_folders = []
        self.selections = {}  # {carpeta: [archivos_seleccionados]}
        self.selected_paths = set()
        
        # Idioma actual (desde sistema operativo por defecto)
        self.current_language = get_system_language()
        
        # Archivo de configuración en el directorio del usuario
        self.config_file = os.path.join(os.path.expanduser("~"), ".llm_export_config.json")
        
        # Configurar interfaz
        self.setup_ui()
        
        # Cargar configuración guardada
        self.load_config()
    
    def _normalize_path(self, path):
        """
        Normaliza una ruta de archivo para asegurar consistencia en comparaciones.
        Convierte todos los separadores a formato unificado.
        """
        # Normalizar a backslash (estilo Windows)
        return path.replace('/', '\\')
    
    def tr(self, key):
        """Traduce una clave al idioma actual."""
        try:
            return TRANSLATIONS[self.current_language][key]
        except KeyError:
            return key
    
    def setup_ui(self):
        """Configura los elementos de la interfaz de usuario."""
        # Configuración de la ventana principal
        self.setWindowTitle(self.tr('app_title'))
        self.setGeometry(100, 100, 800, 600)
        
        # === MENÚ PRINCIPAL ===
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu(self.tr('file_menu'))
        
        open_action = QAction(self.tr('open_folder'), self)
        open_action.triggered.connect(self.open_folder_dialog)
        file_menu.addAction(open_action)
        
        self.recent_menu = QMenu(self.tr('recent_folders'), self)
        file_menu.addMenu(self.recent_menu)
        
        exit_action = QAction(self.tr('exit'), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Opciones
        options_menu = menubar.addMenu(self.tr('options_menu'))
        
        reset_action = QAction(self.tr('reset_selection'), self)
        reset_action.triggered.connect(self.reset_selection)
        options_menu.addAction(reset_action)
        
        # Menú de idioma
        language_menu = menubar.addMenu(self.tr('language_menu'))
        
        english_action = QAction(self.tr('english'), self)
        english_action.triggered.connect(lambda: self.change_language('en'))
        language_menu.addAction(english_action)
        
        spanish_action = QAction(self.tr('spanish'), self)
        spanish_action.triggered.connect(lambda: self.change_language('es'))
        language_menu.addAction(spanish_action)
        
        # === WIDGET CENTRAL ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # === BARRA DE HERRAMIENTAS ===
        toolbar_layout = QHBoxLayout()
        
        # Filtro de extensiones
        toolbar_layout.addWidget(QLabel(self.tr('filter_label')))
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(self.tr('filter_placeholder'))
        self.filter_input.textChanged.connect(self.apply_filter)
        toolbar_layout.addWidget(self.filter_input)
        
        # Botones
        open_button = QPushButton(self.tr('open_folder_button'))
        open_button.clicked.connect(self.open_folder_dialog)
        toolbar_layout.addWidget(open_button)
        
        reset_button = QPushButton(self.tr('reset_button'))
        reset_button.clicked.connect(self.reset_selection)
        toolbar_layout.addWidget(reset_button)
        
        export_button = QPushButton(self.tr('export_button'))
        export_button.clicked.connect(self.export_selected)
        toolbar_layout.addWidget(export_button)
        
        main_layout.addLayout(toolbar_layout)
        
        # === VISTA DE ÁRBOL ===
        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Nombre"])
        self.tree_model.itemChanged.connect(self.handle_item_changed)
        
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        
        main_layout.addWidget(self.tree_view)
    
    def handle_item_changed(self, item):
        """Maneja los cambios en los checkboxes de los elementos."""
        if item.isCheckable():
            # Evitar recursión
            self.tree_model.itemChanged.disconnect(self.handle_item_changed)
            
            path = item.data(Qt.ItemDataRole.UserRole)
            check_state = item.checkState()
            
            # Aplicar el mismo estado a todos los hijos
            if item.hasChildren():
                self._set_check_state_to_children(item, check_state)
                
            # Actualizar la lista de seleccionados
            if check_state == Qt.CheckState.Checked:
                self._add_path_and_children(path, item)
            else:
                self._remove_path_and_children(path, item)
            
            self.save_selection()
            
            # Reconectar la señal
            self.tree_model.itemChanged.connect(self.handle_item_changed)
    
    def _set_check_state_to_children(self, parent_item, state):
        """Establece el mismo estado de selección a todos los hijos."""
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            child.setCheckState(state)
            
            # Recursividad para los subhijos
            if child.hasChildren():
                self._set_check_state_to_children(child, state)
    
    def _add_path_and_children(self, parent_path, parent_item):
        """Añade la ruta del elemento y todos sus hijos al conjunto de seleccionados."""
        self.selected_paths.add(parent_path)
        
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            child_path = child.data(Qt.ItemDataRole.UserRole)
            
            self.selected_paths.add(child_path)
            
            # Recursividad para los subhijos
            if child.hasChildren():
                self._add_path_and_children(child_path, child)
    
    def _remove_path_and_children(self, parent_path, parent_item):
        """Elimina la ruta del elemento y todos sus hijos del conjunto de seleccionados."""
        self.selected_paths.discard(parent_path)
        
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            child_path = child.data(Qt.ItemDataRole.UserRole)
            
            self.selected_paths.discard(child_path)
            
            # Recursividad para los subhijos
            if child.hasChildren():
                self._remove_path_and_children(child_path, child)
    
    def change_language(self, language):
        """Cambia el idioma de la interfaz y guarda la preferencia."""
        if language in TRANSLATIONS and language != self.current_language:
            self.current_language = language
            # Actualizar la interfaz
            self.retranslate_ui()
            # Guardar preferencia
            self.save_config()
    
    def retranslate_ui(self):
        """Actualiza todos los textos de la interfaz al idioma actual."""
        # Título de ventana
        self.setWindowTitle(self.tr('app_title'))
        
        # Actualizar menús
        menubar = self.menuBar()
        menubar.clear()
        
        # Recrea los menús con textos traducidos
        file_menu = menubar.addMenu(self.tr('file_menu'))
        
        open_action = QAction(self.tr('open_folder'), self)
        open_action.triggered.connect(self.open_folder_dialog)
        file_menu.addAction(open_action)
        
        self.recent_menu = QMenu(self.tr('recent_folders'), self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()
        
        exit_action = QAction(self.tr('exit'), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        options_menu = menubar.addMenu(self.tr('options_menu'))
        
        reset_action = QAction(self.tr('reset_selection'), self)
        reset_action.triggered.connect(self.reset_selection)
        options_menu.addAction(reset_action)
        
        language_menu = menubar.addMenu(self.tr('language_menu'))
        
        english_action = QAction(self.tr('english'), self)
        english_action.triggered.connect(lambda: self.change_language('en'))
        language_menu.addAction(english_action)
        
        spanish_action = QAction(self.tr('spanish'), self)
        spanish_action.triggered.connect(lambda: self.change_language('es'))
        language_menu.addAction(spanish_action)
        
        # Actualizar elementos de la barra de herramientas
        toolbar_layout = self.centralWidget().layout().itemAt(0).layout()
        
        # Actualizar etiqueta de filtro
        label_widget = toolbar_layout.itemAt(0).widget()
        if isinstance(label_widget, QLabel):
            label_widget.setText(self.tr('filter_label'))
            
        # Actualizar placeholder
        self.filter_input.setPlaceholderText(self.tr('filter_placeholder'))
        
        # Actualizar botones
        button_indices = [2, 3, 4]  # Índices de los botones en el layout
        button_texts = [
            self.tr('open_folder_button'),
            self.tr('reset_button'),
            self.tr('export_button')
        ]
        
        for idx, text in zip(button_indices, button_texts):
            button = toolbar_layout.itemAt(idx).widget()
            if isinstance(button, QPushButton):
                button.setText(text)
    
    def load_config(self):
        """Carga la configuración guardada desde el archivo JSON."""
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
                        normalized_paths[self._normalize_path(abs_path)] = abs_path
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
                if language in TRANSLATIONS:
                    self.current_language = language
                    self.retranslate_ui()
                
                # Actualizar menú de carpetas recientes
                self.update_recent_menu()
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
    
    def save_config(self):
        """Guarda la configuración en el archivo JSON."""
        config = {
            'recent_folders': self.recent_folders,
            'last_export_location': self.last_export_location,
            'selections': self.selections,
            'language': self.current_language  # Guardar el idioma
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
    
    def save_selection(self):
        """Guarda la selección actual para la carpeta abierta."""
        if self.current_folder:
            self.selections[self.current_folder] = list(self.selected_paths)
            self.save_config()
    
    def update_recent_menu(self):
        """Actualiza el menú de carpetas recientes."""
        self.recent_menu.clear()
        
        for folder in self.recent_folders:
            action = QAction(folder, self)
            action.triggered.connect(lambda checked=False, f=folder: self.open_folder(f))
            self.recent_menu.addAction(action)
    
    def open_folder_dialog(self):
        """Muestra un diálogo para seleccionar una carpeta."""
        folder = QFileDialog.getExistingDirectory(self, self.tr('open_folder'))
        if folder:
            self.open_folder(folder)
    
    def open_folder(self, folder_path):
        """Abre una carpeta y muestra su contenido en el árbol."""
        # Convertir a ruta absoluta
        folder_path = os.path.abspath(folder_path)
        
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, self.tr('error'), f"{folder_path} no existe.")
            return
        
        # Normalizar la ruta
        normalized_path = self._normalize_path(folder_path)
        
        # Actualizar carpeta actual
        self.current_folder = folder_path  # Mantener la ruta original para uso del sistema
        
        # Añadir a carpetas recientes con ruta normalizada
        normalized_recent_folders = [self._normalize_path(path) for path in self.recent_folders]
        if normalized_path in normalized_recent_folders:
            # Eliminar la entrada existente (podría tener otro formato de separador)
            index = normalized_recent_folders.index(normalized_path)
            self.recent_folders.pop(index)
        
        self.recent_folders.insert(0, folder_path)  # Guardar la ruta original
        self.recent_folders = self.recent_folders[:10]  # Limitar a 10 carpetas
        self.update_recent_menu()
        
        # Limpiar árbol
        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(["Nombre"])
        
        # Cargar selecciones anteriores
        self.selected_paths = set()
        if folder_path in self.selections:
            self.selected_paths = set(self.selections[folder_path])
        
        # Poblar árbol
        self.populate_tree(folder_path)
        
        # Actualizar título de la ventana
        self.setWindowTitle(f"{self.tr('app_title')} - {folder_path}")
        
        # Guardar configuración
        self.save_config()
    
    def populate_tree(self, folder_path):
        """Puebla el árbol con el contenido de la carpeta, mostrando la carpeta base como nodo raíz."""
        root_item = self.tree_model.invisibleRootItem()
        
        # Crear el nodo para la carpeta base
        base_name = os.path.basename(folder_path)
        base_item = QStandardItem(base_name)
        base_item.setData("", Qt.ItemDataRole.UserRole)  # Ruta relativa vacía para el nodo raíz
        base_item.setCheckable(True)
        
        # Verificar si el nodo raíz estaba seleccionado previamente
        if "" in self.selected_paths:
            base_item.setCheckState(Qt.CheckState.Checked)
        else:
            base_item.setCheckState(Qt.CheckState.Unchecked)
        
        # Añadir el nodo raíz al árbol
        root_item.appendRow(base_item)
        
        # Añadir elementos recursivamente a partir del nodo raíz
        self._add_directory(base_item, folder_path, "")
        
        # Expandir el nodo raíz para mostrar su contenido inmediatamente
        self.tree_view.expand(self.tree_model.indexFromItem(base_item))
    
    def _add_directory(self, parent_item, dir_path, rel_path):
        """Añade recursivamente los elementos de un directorio al árbol."""
        try:
            # Ordenar: primero archivos, luego carpetas (por nombre)
            items = sorted(os.listdir(dir_path), key=lambda x: (
                not os.path.isdir(os.path.join(dir_path, x)), x.lower()
            ))
            
            for item_name in items:
                # Construir rutas
                full_path = os.path.join(dir_path, item_name)
                item_rel_path = os.path.join(rel_path, item_name) if rel_path else item_name
                
                # Crear elemento en el árbol
                tree_item = QStandardItem(item_name)
                tree_item.setData(item_rel_path, Qt.ItemDataRole.UserRole)  # Guardar ruta relativa
                tree_item.setCheckable(True)
                
                # Verificar si estaba seleccionado previamente
                if item_rel_path in self.selected_paths:
                    tree_item.setCheckState(Qt.CheckState.Checked)
                else:
                    tree_item.setCheckState(Qt.CheckState.Unchecked)
                
                # Añadir al padre
                parent_item.appendRow(tree_item)
                
                # Si es un directorio, procesar recursivamente
                if os.path.isdir(full_path):
                    self._add_directory(tree_item, full_path, item_rel_path)
        except PermissionError:
            # Ignorar directorios sin permiso de acceso
            pass
    
    def apply_filter(self):
        """Aplica un filtro por extensiones a los elementos mostrados."""
        filter_text = self.filter_input.text().strip()
        
        if not filter_text:
            # Sin filtro - mostrar todo
            self._show_all_items()
            return
        
        # Separar extensiones (ej: "*.py, *.md" -> ["*.py", "*.md"])
        filters = [ext.strip() for ext in filter_text.split(',')]
        
        # Aplicar filtro recursivamente
        root = self.tree_model.invisibleRootItem()
        for i in range(root.rowCount()):
            self._apply_filter_to_item(root.child(i), filters)
    
    def _show_all_items(self):
        """Muestra todos los elementos en el árbol."""
        def show_recursive(item):
            index = self.tree_model.indexFromItem(item)
            self.tree_view.setRowHidden(index.row(), index.parent(), False)
            
            for i in range(item.rowCount()):
                show_recursive(item.child(i))
        
        # Comenzar desde los elementos de primer nivel
        root = self.tree_model.invisibleRootItem()
        for i in range(root.rowCount()):
            show_recursive(root.child(i))
    
    def _apply_filter_to_item(self, item, filters):
        """Aplica el filtro a un elemento y sus hijos recursivamente."""
        # Obtener información del elemento
        item_text = item.text()
        index = self.tree_model.indexFromItem(item)
        is_dir = item.hasChildren()
        
        # Procesar hijos primero
        visible_children = False
        if is_dir:
            for i in range(item.rowCount()):
                child_visible = self._apply_filter_to_item(item.child(i), filters)
                visible_children = visible_children or child_visible
        
        # Verificar si el elemento coincide con el filtro
        matches = False
        
        # Los directorios con hijos visibles siempre se muestran
        if is_dir and visible_children:
            matches = True
        else:
            # Verificar si el nombre coincide con algún filtro
            for filter_pattern in filters:
                if filter_pattern.startswith('*'):
                    # Filtro por extensión (*.py)
                    if item_text.endswith(filter_pattern[1:]):
                        matches = True
                        break
                else:
                    # Filtro exacto
                    if item_text == filter_pattern:
                        matches = True
                        break
        
        # Mostrar u ocultar según el resultado
        self.tree_view.setRowHidden(index.row(), index.parent(), not matches)
        
        return matches
    
    def reset_selection(self):
        """Reinicia todas las selecciones."""
        # Limpiar conjunto de selecciones
        self.selected_paths.clear()
        
        # Desmarcar todos los checkboxes
        def uncheck_all(item):
            item.setCheckState(Qt.CheckState.Unchecked)
            for i in range(item.rowCount()):
                uncheck_all(item.child(i))
        
        # Aplicar a todos los elementos
        root = self.tree_model.invisibleRootItem()
        for i in range(root.rowCount()):
            uncheck_all(root.child(i))
        
        # Actualizar selecciones guardadas
        if self.current_folder:
            self.selections[self.current_folder] = []
            self.save_config()
    
    def export_selected(self):
        """Exporta los archivos seleccionados en formato LLM-friendly."""
        if not self.current_folder:
            QMessageBox.warning(self, self.tr('error'), self.tr('no_folder_open'))
            return
        
        if not self.selected_paths:
            QMessageBox.warning(self, self.tr('error'), self.tr('no_files_selected'))
            return
        
        # Diálogo para guardar archivo
        initial_path = self.last_export_location or os.path.expanduser("~")
        folder_name = os.path.basename(self.current_folder)
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            self.tr('save_as'), 
            os.path.join(initial_path, f"{folder_name}_export.txt"), 
            "Archivos de texto (*.txt)"
        )
        
        if not file_path:
            return
        
        # Actualizar última ubicación
        self.last_export_location = os.path.dirname(file_path)
        self.save_config()
        
        # Generar y guardar contenido exportado
        try:
            content = self.generate_export_content()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, self.tr('success'), 
                                    f"{self.tr('export_success')}\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, self.tr('error'), 
                                f"{self.tr('export_error')} {e}")
    
    def generate_export_content(self):
        """Genera el contenido exportado en formato LLM-friendly."""
        # Formato similar a Gitingest
        result = ["Directory structure:"]
        
        # Generar estructura de directorios
        dir_structure = self._generate_directory_structure()
        result.append(dir_structure)
        result.append("")  # Línea en blanco
        
        # Generar contenido de archivos
        file_contents = self._generate_file_contents()
        result.append(file_contents)
        
        return "\n".join(result)
    
    def _generate_directory_structure(self):
        """Genera representación en árbol de la estructura de directorios."""
        lines = []
        
        # Nombre de la carpeta base
        base_name = os.path.basename(self.current_folder)
        lines.append(f"└── {base_name}/")
        
        # Función recursiva para añadir elementos al árbol
        def build_tree(path, prefix=""):
            try:
                # Listar y ordenar los elementos
                items = sorted(os.listdir(path), key=lambda x: (
                    not os.path.isdir(os.path.join(path, x)), x.lower()
                ))
                
                for i, item in enumerate(items):
                    # Construir rutas
                    item_path = os.path.join(path, item)
                    rel_path = os.path.relpath(item_path, self.current_folder)
                    
                    # Verificar si está seleccionado
                    is_selected = rel_path in self.selected_paths
                    
                    # Verificar si algún hijo está seleccionado
                    has_selected_children = any(
                        p in self.selected_paths and p.startswith(rel_path + os.sep)
                        for p in self.selected_paths
                    )
                    
                    # Si ni este ni sus hijos están seleccionados, omitir
                    if not is_selected and not has_selected_children:
                        continue
                    
                    # Determinar prefijo según posición
                    is_last = i == len(items) - 1
                    item_prefix = prefix + ("└── " if is_last else "├── ")
                    
                    # Añadir elemento al árbol
                    if os.path.isdir(item_path):
                        lines.append(f"{item_prefix}{item}/")
                    else:
                        lines.append(f"{item_prefix}{item}")
                    
                    # Si es directorio, procesar recursivamente
                    if os.path.isdir(item_path):
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        build_tree(item_path, next_prefix)
            except (PermissionError, FileNotFoundError):
                # Ignorar errores de acceso
                pass
        
        # Comenzar la recursión
        build_tree(self.current_folder, "    ")
        
        return "\n".join(lines)
    
    def _generate_file_contents(self):
        """Genera el contenido de archivos seleccionados."""
        content = []
        
        # Procesar archivos seleccionados
        for rel_path in sorted(self.selected_paths):
            full_path = os.path.join(self.current_folder, rel_path)
            
            # Omitir directorios
            if os.path.isdir(full_path):
                continue
            
            # Añadir separador y encabezado de archivo - formato Gitingest
            content.append("=" * 48)
            content.append(f"File: {rel_path}")
            content.append("=" * 48)
            
            # Leer contenido del archivo
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    file_content = f.read()
                content.append(file_content)
            except Exception as e:
                content.append(f"[Error al leer el archivo: {e}]")
            
            # Separador entre archivos
            content.append("\n")
        
        return "\n".join(content)
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        # Guardar configuración
        self.save_config()
        event.accept()

if __name__ == "__main__":
    # Procesar argumentos personalizados
    parser = argparse.ArgumentParser(description='LLM Export Tool')
    parser.add_argument('folder', nargs='?', help='Carpeta inicial para abrir automáticamente')
    args, remaining_args = parser.parse_known_args()
    
    # Inicializar la aplicación Qt con los argumentos restantes
    app = QApplication(remaining_args)
    window = LLMExportApp()
    window.show()
    
    # Si se proporcionó una carpeta inicial, abrirla
    if args.folder and os.path.isdir(args.folder):
        window.open_folder(args.folder)
    
    sys.exit(app.exec())