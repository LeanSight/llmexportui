import os
from typing import Set, Dict, List, Any, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QTreeView, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLineEdit, QLabel, QMenu, QMessageBox,
    QGroupBox, QFormLayout, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction

from config_manager import ConfigManager
from i18n import translate, get_system_language
from filter_engine import FilterEngine
from tree_manager import TreeManager
from export_generator import generate_export_content

class LLMExportApp(QMainWindow):
    """Aplicación para exportar archivos en formato amigable para LLMs."""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes principales
        self.config_manager = ConfigManager()
        self.filter_engine = FilterEngine()
        
        # Idioma actual (desde sistema operativo por defecto)
        self.current_language = get_system_language()
        
        # Configurar interfaz
        self.setup_ui()
        
        # Inicializar tree manager con el modelo creado
        self.tree_manager = TreeManager(self.tree_model)
        self.tree_manager.set_visibility_function(self.filter_engine.is_visible)
        
        # Cargar configuración guardada
        self.config_manager.load_config()
        self.current_language = self.config_manager.language
        
        # Actualizar interfaz con la configuración
        self.retranslate_ui()
        self.update_recent_menu()
    
    def tr(self, key, **kwargs):
        """Traduce una clave al idioma actual."""
        return translate(key, self.current_language, **kwargs)
    
    def setup_ui(self):
        """Configura los elementos de la interfaz de usuario."""
        # Configuración de la ventana principal
        self.setWindowTitle(self.tr('app_title'))
        self.setGeometry(100, 100, 800, 600)
        
        # === MENÚ PRINCIPAL ===
        self.setup_menu()
        
        # === WIDGET CENTRAL ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # === BARRA DE HERRAMIENTAS ===
        toolbar_layout = QHBoxLayout()
        
        # Grupo de filtros
        filter_group = QGroupBox(self.tr('filter_section'))
        filter_layout = QFormLayout(filter_group)
        
        # Filtro de inclusión
        self.include_filter = QLineEdit()
        self.include_filter.setPlaceholderText(self.tr('include_filter_placeholder'))
        self.include_filter.textChanged.connect(self.apply_filters)
        filter_layout.addRow(self.tr('include_filter_label'), self.include_filter)
        
        # Filtro de exclusión
        self.exclude_filter = QLineEdit()
        self.exclude_filter.setPlaceholderText(self.tr('exclude_filter_placeholder'))
        self.exclude_filter.textChanged.connect(self.apply_filters)
        filter_layout.addRow(self.tr('exclude_filter_label'), self.exclude_filter)
        
        toolbar_layout.addWidget(filter_group)
        
        # Botones
        buttons_layout = QVBoxLayout()
        
        open_button = QPushButton(self.tr('open_folder_button'))
        open_button.clicked.connect(self.open_folder_dialog)
        buttons_layout.addWidget(open_button)
        
        reset_button = QPushButton(self.tr('reset_button'))
        reset_button.clicked.connect(self.reset_selection)
        buttons_layout.addWidget(reset_button)
        
        export_button = QPushButton(self.tr('export_button'))
        export_button.clicked.connect(self.export_selected)
        buttons_layout.addWidget(export_button)
        
        toolbar_layout.addLayout(buttons_layout)
        
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
        
        # === BARRA DE ESTADO ===
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("")
        self.status_bar.addWidget(self.status_label)
        
    def setup_menu(self):
        """Configura el menú principal"""
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
    
    def retranslate_ui(self):
        """Actualiza todos los textos de la interfaz al idioma actual."""
        # Título de ventana
        self.setWindowTitle(self.tr('app_title'))
        
        # Actualizar menús
        menubar = self.menuBar()
        menubar.clear()
        
        # Recrea los menús con textos traducidos
        self.setup_menu()
        self.update_recent_menu()
        
        # Actualizar elementos de la barra de herramientas
        form_layout = self.centralWidget().layout().itemAt(0).layout().itemAt(0).widget().layout()
        
        # Etiquetas de filtros
        filter_group = self.centralWidget().layout().itemAt(0).layout().itemAt(0).widget()
        filter_group.setTitle(self.tr('filter_section'))
        
        # Formulario de filtros (2 filas: include y exclude)
        for row in range(2):
            label_widget = form_layout.itemAt(row, QFormLayout.ItemRole.LabelRole).widget()
            field_widget = form_layout.itemAt(row, QFormLayout.ItemRole.FieldRole).widget()
            
            if row == 0:  # Include filter
                label_widget.setText(self.tr('include_filter_label'))
                field_widget.setPlaceholderText(self.tr('include_filter_placeholder'))
            elif row == 1:  # Exclude filter
                label_widget.setText(self.tr('exclude_filter_label'))
                field_widget.setPlaceholderText(self.tr('exclude_filter_placeholder'))
        
        # Actualizar botones
        buttons_layout = self.centralWidget().layout().itemAt(0).layout().itemAt(1).layout()
        buttons = [
            (0, self.tr('open_folder_button')),
            (1, self.tr('reset_button')),
            (2, self.tr('export_button'))
        ]
        
        for idx, text in buttons:
            button = buttons_layout.itemAt(idx).widget()
            if isinstance(button, QPushButton):
                button.setText(text)
        
        # Actualizar estado
        self.update_status_bar()
    
    def change_language(self, language):
        """Cambia el idioma de la interfaz y guarda la preferencia."""
        if language in ('en', 'es') and language != self.current_language:
            self.current_language = language
            self.config_manager.set_language(language)
            self.retranslate_ui()
    
    def update_recent_menu(self):
        """Actualiza el menú de carpetas recientes."""
        self.recent_menu.clear()
        
        for folder in self.config_manager.recent_folders:
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
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, self.tr('error'), f"{folder_path} no existe.")
            return
        
        # Convertir a ruta absoluta
        folder_path = os.path.abspath(folder_path)
        
        # Actualizar estado
        self.config_manager.set_current_folder(folder_path)
        
        # Actualizar título de la ventana
        self.setWindowTitle(f"{self.tr('app_title')} - {folder_path}")
        
        # Cargar selecciones anteriores
        selected_paths = set(self.config_manager.get_selection(folder_path))
        self.tree_manager.set_selected_paths(selected_paths)
        self.tree_manager.set_base_path(folder_path)
        
        # Cargar filtros de la carpeta
        folder_filters = self.config_manager.get_folder_filters(folder_path)
        self.include_filter.setText(folder_filters.get("include_patterns", ""))
        self.exclude_filter.setText(folder_filters.get("exclude_patterns", ""))
        
        # Configurar motor de filtros
        self.filter_engine.set_base_path(folder_path)
        self.filter_engine.set_include_patterns(self.include_filter.text())
        self.filter_engine.set_exclude_patterns(self.exclude_filter.text())
        
        # Poblar árbol
        self.tree_manager.populate_tree()
        
        # Actualizar menús
        self.update_recent_menu()
        
        # Expandir el nodo raíz
        root = self.tree_model.invisibleRootItem()
        if root.rowCount() > 0:
            self.tree_view.expand(self.tree_model.indexFromItem(root.child(0)))
        
        # Actualizar barra de estado
        self.update_status_bar()
    
    def apply_filters(self):
        """Aplica los filtros y actualiza la visibilidad de los elementos."""
        # Obtener y guardar filtros actuales
        include_patterns = self.include_filter.text()
        exclude_patterns = self.exclude_filter.text()
        
        if not self.config_manager.current_folder:
            return
        
        # Guardar filtros en la configuración
        self.config_manager.set_folder_filters(
            self.config_manager.current_folder,
            include_patterns,
            exclude_patterns
        )
        
        # Actualizar motor de filtros
        self.filter_engine.set_include_patterns(include_patterns)
        self.filter_engine.set_exclude_patterns(exclude_patterns)
        
        # Reconstruir el árbol para aplicar los nuevos filtros
        self.tree_manager.populate_tree()
        
        # Actualizar barra de estado
        self.update_status_bar()
    
    def update_status_bar(self):
        """Actualiza la barra de estado con información actual"""
        if not self.config_manager.current_folder:
            self.status_label.setText("")
            return
        
        # Contar elementos visibles y totales
        visible_count = 0
        total_count = 0
        
        # Simplemente mostramos un mensaje estático por ahora
        # En una implementación real, contaríamos los items
        visible_count = len(self.tree_manager.get_selected_paths())
        total_count = 100  # Placeholder
        
        self.status_label.setText(self.tr('showing_items', visible=visible_count, total=total_count))
    
    @pyqtSlot(QStandardItem)
    def handle_item_changed(self, item):
        """Maneja los cambios en los checkboxes de los elementos."""
        if item.isCheckable():
            # Evitar recursión mientras procesamos
            self.tree_model.itemChanged.disconnect(self.handle_item_changed)
            
            self.tree_manager.handle_item_changed(item)
            
            # Guardar selección actualizada
            self.config_manager.save_selection(self.tree_manager.get_selected_paths())
            
            # Reconectar la señal
            self.tree_model.itemChanged.connect(self.handle_item_changed)
            
            # Actualizar barra de estado
            self.update_status_bar()
    
    def reset_selection(self):
        """Reinicia todas las selecciones."""
        self.tree_manager.reset_selection()
        self.config_manager.save_selection(self.tree_manager.get_selected_paths())
        self.update_status_bar()
    
    def export_selected(self):
        """Exporta los archivos seleccionados en formato LLM-friendly."""
        if not self.config_manager.current_folder:
            QMessageBox.warning(self, self.tr('error'), self.tr('no_folder_open'))
            return
        
        selected_paths = self.tree_manager.get_selected_paths()
        if not selected_paths:
            QMessageBox.warning(self, self.tr('error'), self.tr('no_files_selected'))
            return
        
        # Diálogo para guardar archivo
        initial_path = self.config_manager.last_export_location or os.path.expanduser("~")
        folder_name = os.path.basename(self.config_manager.current_folder)
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            self.tr('save_as'), 
            os.path.join(initial_path, f"{folder_name}_export.txt"), 
            "Archivos de texto (*.txt)"
        )
        
        if not file_path:
            return
        
        # Actualizar última ubicación
        self.config_manager.set_export_location(os.path.dirname(file_path))
        
        # Generar y guardar contenido exportado
        try:
            content = generate_export_content(
                self.config_manager.current_folder, 
                selected_paths
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            QMessageBox.information(
                self, 
                self.tr('success'), 
                f"{self.tr('export_success')}\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                self.tr('error'),
                f"{self.tr('export_error')} {e}"
            )
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        # Guardar configuración
        self.config_manager.save_config()
        event.accept()