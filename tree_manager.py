import os
from typing import Set, Dict, List, Callable, Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from path_utils import normalize_path

class TreeManager:
    """
    Administrador del árbol de archivos
    """
    
    def __init__(self, tree_model: QStandardItemModel):
        """
        Inicializa un nuevo administrador de árbol
        
        Args:
            tree_model: Modelo de árbol de Qt
        """
        self.tree_model = tree_model
        self.base_path = ""
        self.selected_paths = set()
        self.is_visible_fn = None  # Función para determinar visibilidad
    
    def set_visibility_function(self, is_visible_fn: Callable[[str], bool]) -> None:
        """
        Establece la función para determinar visibilidad de elementos
        
        Args:
            is_visible_fn: Función que toma una ruta y devuelve True si es visible
        """
        self.is_visible_fn = is_visible_fn
    
    def set_base_path(self, path: str) -> None:
        """
        Establece la ruta base del árbol
        
        Args:
            path: Ruta base para el árbol
        """
        self.base_path = path
    
    def set_selected_paths(self, paths: Set[str]) -> None:
        """
        Establece el conjunto de rutas seleccionadas
        
        Args:
            paths: Conjunto de rutas seleccionadas
        """
        self.selected_paths = paths
    
    def get_selected_paths(self) -> Set[str]:
        """
        Obtiene el conjunto de rutas seleccionadas
        
        Returns:
            Conjunto de rutas seleccionadas
        """
        return self.selected_paths
    
    def populate_tree(self) -> None:
        """Puebla el árbol con el contenido de la carpeta base"""
        # Limpiar árbol
        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(["Nombre"])
        
        if not self.base_path:
            return
        
        root_item = self.tree_model.invisibleRootItem()
        
        # Crear el nodo para la carpeta base
        base_name = os.path.basename(self.base_path)
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
        self._add_directory(base_item, self.base_path, "")
    
    def _add_directory(self, parent_item: QStandardItem, dir_path: str, rel_path: str) -> None:
        """
        Añade recursivamente los elementos de un directorio al árbol
        
        Args:
            parent_item: Item padre en el árbol
            dir_path: Ruta completa del directorio
            rel_path: Ruta relativa a la base
        """
        try:
            # Ordenar: primero archivos, luego carpetas (por nombre)
            items = sorted(os.listdir(dir_path), key=lambda x: (
                not os.path.isdir(os.path.join(dir_path, x)), x.lower()
            ))
            
            for item_name in items:
                # Construir rutas
                full_path = os.path.join(dir_path, item_name)
                item_rel_path = os.path.join(rel_path, item_name) if rel_path else item_name
                
                # Verificar visibilidad según filtro
                visible = True
                if self.is_visible_fn:
                    visible = self.is_visible_fn(item_rel_path)
                
                # Verificar si algún hijo debe ser visible
                has_visible_children = False
                if os.path.isdir(full_path) and not visible:
                    has_visible_children = self._check_children_visibility(full_path, item_rel_path)
                
                # Si ni este ni sus hijos son visibles, omitir
                if not visible and not has_visible_children:
                    continue
                
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
    
    def _check_children_visibility(self, dir_path: str, rel_path: str) -> bool:
        """
        Verifica recursivamente si algún hijo debe ser visible
        
        Args:
            dir_path: Ruta completa del directorio
            rel_path: Ruta relativa a la base
            
        Returns:
            bool: True si algún hijo debe ser visible
        """
        try:
            for item in os.listdir(dir_path):
                item_rel_path = os.path.join(rel_path, item)
                full_path = os.path.join(dir_path, item)
                
                # Verificar visibilidad según filtro
                if self.is_visible_fn and self.is_visible_fn(item_rel_path):
                    return True
                
                # Si es directorio, verificar recursivamente
                if os.path.isdir(full_path):
                    if self._check_children_visibility(full_path, item_rel_path):
                        return True
        except (PermissionError, FileNotFoundError):
            pass
        
        return False
    
    def apply_filter(self) -> None:
        """
        Actualiza la visibilidad de los elementos según la función de filtro
        """
        if not self.is_visible_fn:
            # Sin filtro - mostrar todo
            self._show_all_items()
            return
        
        # Aplicar filtro recursivamente
        root = self.tree_model.invisibleRootItem()
        for i in range(root.rowCount()):
            self._apply_filter_to_item(root.child(i))
    
    def _show_all_items(self) -> None:
        """Muestra todos los elementos en el árbol"""
        def show_recursive(item):
            index = self.tree_model.indexFromItem(item)
            self.tree_view.setRowHidden(index.row(), index.parent(), False)
            
            for i in range(item.rowCount()):
                show_recursive(item.child(i))
        
        # Comenzar desde los elementos de primer nivel
        root = self.tree_model.invisibleRootItem()
        for i in range(root.rowCount()):
            show_recursive(root.child(i))
    
    def _apply_filter_to_item(self, item: QStandardItem) -> bool:
        """
        Aplica el filtro a un elemento y sus hijos recursivamente
        
        Args:
            item: Item al que aplicar el filtro
            
        Returns:
            bool: True si el item o alguno de sus hijos es visible
        """
        # Obtener información del elemento
        path = item.data(Qt.ItemDataRole.UserRole)
        is_dir = item.hasChildren()
        
        # Procesar hijos primero
        visible_children = False
        if is_dir:
            for i in range(item.rowCount()):
                child_visible = self._apply_filter_to_item(item.child(i))
                visible_children = visible_children or child_visible
        
        # Verificar si el elemento coincide con el filtro
        matches = False
        
        # Los directorios con hijos visibles siempre se muestran
        if is_dir and visible_children:
            matches = True
        elif self.is_visible_fn:
            matches = self.is_visible_fn(path)
        else:
            matches = True  # Si no hay filtro, todo es visible
        
        return matches
    
    def handle_item_changed(self, item: QStandardItem) -> None:
        """
        Maneja los cambios en los checkboxes de los elementos
        
        Args:
            item: Item que cambió
        """
        if not item.isCheckable():
            return
        
        # Obtener información del item
        path = item.data(Qt.ItemDataRole.UserRole)
        check_state = item.checkState()
        
        # Aplicar el mismo estado a todos los hijos visibles
        if item.hasChildren():
            self._set_check_state_to_children(item, check_state)
            
        # Actualizar la lista de seleccionados
        if check_state == Qt.CheckState.Checked:
            self._add_path_and_children(path, item)
        else:
            self._remove_path_and_children(path, item)
    
    def _set_check_state_to_children(self, parent_item: QStandardItem, state: Qt.CheckState) -> None:
        """
        Establece el mismo estado de selección a todos los hijos visibles
        
        Args:
            parent_item: Item padre
            state: Estado de selección a aplicar
        """
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            
            # Verificar visibilidad según filtro
            path = child.data(Qt.ItemDataRole.UserRole)
            visible = True
            if self.is_visible_fn:
                visible = self.is_visible_fn(path)
            
            # Solo cambiar estado si es visible
            if visible:
                child.setCheckState(state)
            
            # Recursividad para los subhijos visibles
            if child.hasChildren():
                self._set_check_state_to_children(child, state)
    
    def _add_path_and_children(self, parent_path: str, parent_item: QStandardItem) -> None:
        """
        Añade la ruta del elemento y todos sus hijos al conjunto de seleccionados
        
        Args:
            parent_path: Ruta del elemento padre
            parent_item: Item padre
        """
        self.selected_paths.add(parent_path)
        
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            child_path = child.data(Qt.ItemDataRole.UserRole)
            
            # Verificar visibilidad según filtro
            visible = True
            if self.is_visible_fn:
                visible = self.is_visible_fn(child_path)
            
            # Solo añadir si es visible
            if visible:
                self.selected_paths.add(child_path)
                
                # Recursividad para los subhijos visibles
                if child.hasChildren():
                    self._add_path_and_children(child_path, child)
    
    def _remove_path_and_children(self, parent_path: str, parent_item: QStandardItem) -> None:
        """
        Elimina la ruta del elemento y todos sus hijos del conjunto de seleccionados
        
        Args:
            parent_path: Ruta del elemento padre
            parent_item: Item padre
        """
        self.selected_paths.discard(parent_path)
        
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            child_path = child.data(Qt.ItemDataRole.UserRole)
            
            # Eliminar independientemente de la visibilidad
            self.selected_paths.discard(child_path)
            
            # Recursividad para los subhijos
            if child.hasChildren():
                self._remove_path_and_children(child_path, child)
    
    def reset_selection(self) -> None:
        """Reinicia todas las selecciones"""
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