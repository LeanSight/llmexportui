from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional, Set

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel

from path_utils import normalize_path # Asumiendo que path_utils.py existe y es relevante

__all__ = ["TreeManager"]

# Rol personalizado para almacenar si un ítem es un directorio
IS_DIRECTORY_ROLE = Qt.ItemDataRole.UserRole + 1

class TreeManager:
    """Administra el árbol de archivos y la lógica de selección, guardando solo archivos seleccionados."""

    # ---------------------------------------------------------------------
    # INITIALISATION
    # ---------------------------------------------------------------------
    def __init__(self, tree_model: QStandardItemModel) -> None:
        self._model: QStandardItemModel = tree_model
        self._base_path: Path | None = None
        self._selected_paths: Set[str] = set()  # Solo almacena rutas relativas de ARCHIVOS
        self._is_visible: Optional[Callable[[str], bool]] = None

    # ------------------------------------------------------------------
    # PUBLIC CONFIGURATION API
    # ------------------------------------------------------------------
    def set_visibility_function(self, fn: Callable[[str], bool]) -> None:
        """Registra la función que decide si un nodo es visible."""
        self._is_visible = fn

    def set_base_path(self, path: str | os.PathLike[str]) -> None:
        """Define la carpeta raíz y purga selecciones inexistentes."""
        self._base_path = Path(path).resolve()
        self._prune_nonexistent_selections() 

    def set_selected_paths(self, paths: Set[str]) -> None:
        """Carga la selección previamente almacenada (rutas de archivos)."""
        self._selected_paths = set(paths)

    # ------------------------------------------------------------------
    # PUBLIC QUERIES
    # ------------------------------------------------------------------
    def get_selected_paths(self) -> Set[str]:
        """Devuelve las rutas de ARCHIVOS actualmente seleccionadas (relativas)."""
        return set(self._selected_paths)

    # ------------------------------------------------------------------
    # TREE BUILDING
    # ------------------------------------------------------------------
    def populate_tree(self) -> None:
        """Reconstruye el modelo en memoria a partir del disco."""
        self._model.blockSignals(True) 
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["Nombre"])

        if self._base_path is None:
            self._model.blockSignals(False)
            return

        self._prune_nonexistent_selections() 

        root_item = self._model.invisibleRootItem()
        
        base_folder_display_name = f"[{self._base_path.name}]"
        base_folder_item = QStandardItem(base_folder_display_name)
        base_folder_item.setData("", Qt.ItemDataRole.UserRole) 
        base_folder_item.setData(True, IS_DIRECTORY_ROLE) 
        base_folder_item.setCheckable(True)
        root_item.appendRow(base_folder_item)

        self._add_directory_items(base_folder_item, self._base_path, rel_path_context="")
        
        self._calculate_and_set_folder_state_from_children(base_folder_item)
        self._update_ancestor_states_after_population(base_folder_item) 

        self._model.blockSignals(False)


    def _add_directory_items(
        self,
        parent_ui_item: QStandardItem,
        abs_dir_path: Path,
        *,
        rel_path_context: str,
    ) -> None:
        """Añade recursivamente ítems de directorio y archivo al parent_ui_item, ordenados y con formato."""
        try:
            all_names_in_dir = os.listdir(abs_dir_path)
        except PermissionError:
            return 

        sortable_entries = []
        for name in all_names_in_dir:
            current_abs_path_entry = abs_dir_path / name
            try:
                is_entry_dir = current_abs_path_entry.is_dir() 
                sortable_entries.append({'name': name, 'is_dir': is_entry_dir, 'abs_path': current_abs_path_entry})
            except OSError: 
                continue 
        
        sortable_entries.sort(key=lambda e: (not e['is_dir'], e['name'].lower()))

        for entry in sortable_entries:
            name = entry['name']
            is_dir = entry['is_dir']
            current_abs_path = entry['abs_path']
            
            current_rel_path = str(Path(rel_path_context, name)) if rel_path_context else name

            is_item_visible = self._is_visible(current_rel_path) if self._is_visible else True
            if not is_item_visible and is_dir:
                if not self._has_visible_descendants(current_abs_path, current_rel_path):
                    continue
            elif not is_item_visible: 
                continue

            display_name = f"[{name}]" if is_dir else name
            ui_item = QStandardItem(display_name)
            
            ui_item.setData(current_rel_path, Qt.ItemDataRole.UserRole) 
            ui_item.setCheckable(True)
            ui_item.setData(is_dir, IS_DIRECTORY_ROLE) 
            
            parent_ui_item.appendRow(ui_item) 

            if is_dir:
                self._add_directory_items(ui_item, current_abs_path, rel_path_context=current_rel_path)
                self._calculate_and_set_folder_state_from_children(ui_item)
            else: # Es un archivo
                if current_rel_path in self._selected_paths:
                    ui_item.setCheckState(Qt.CheckState.Checked)
                else:
                    ui_item.setCheckState(Qt.CheckState.Unchecked)

    def _calculate_and_set_folder_state_from_children(self, folder_item: QStandardItem) -> None:
        if not folder_item.data(IS_DIRECTORY_ROLE): 
            return

        num_children = folder_item.rowCount()
        if num_children == 0: 
            folder_item.setCheckState(Qt.CheckState.Unchecked)
            return

        checked_children = 0
        partially_checked_children = 0
        for i in range(num_children):
            child = folder_item.child(i)
            if child is None: continue
            
            state = child.checkState()
            if state == Qt.CheckState.Checked:
                checked_children += 1
            elif state == Qt.CheckState.PartiallyChecked:
                partially_checked_children += 1
        
        current_state = folder_item.checkState()
        new_state = current_state

        if checked_children == num_children:
            new_state = Qt.CheckState.Checked
        elif checked_children == 0 and partially_checked_children == 0:
            new_state = Qt.CheckState.Unchecked
        else:
            new_state = Qt.CheckState.PartiallyChecked
        
        if new_state != current_state:
            folder_item.setCheckState(new_state)

    def _update_ancestor_states_after_population(self, item: QStandardItem) -> None:
        parent = item.parent()
        while parent is not None and parent != self._model.invisibleRootItem():
            self._calculate_and_set_folder_state_from_children(parent)
            parent = parent.parent()

    # ------------------------------------------------------------------
    # PRIVATE HELPERS (Selección y Visibilidad)
    # ------------------------------------------------------------------
    def _prune_nonexistent_selections(self) -> None:
        if self._base_path is None:
            return
        valid_selected_files: Set[str] = set()
        for rel_file_path in list(self._selected_paths): 
            full_path = self._base_path / rel_file_path
            if full_path.is_file(): 
                valid_selected_files.add(rel_file_path)
        self._selected_paths = valid_selected_files


    def _has_visible_descendants(self, abs_dir_path: Path, base_rel_path_of_dir: str) -> bool:
        if self._is_visible is None:
            for _, _, files in os.walk(abs_dir_path):
                if files: return True 
            return False

        for root, _, files in os.walk(abs_dir_path):
            for f_name in files:
                abs_file_path = Path(root) / f_name
                try:
                    rel_to_treemanager_base = str(abs_file_path.relative_to(self._base_path))
                    if self._is_visible(rel_to_treemanager_base):
                        return True
                except ValueError: 
                    pass 
        return False

    # ------------------------------------------------------------------
    # CHECKBOX HANDLERS (Interacción del Usuario)
    # ------------------------------------------------------------------
    def handle_item_changed(self, item: QStandardItem) -> None:
        """Maneja el click del usuario en un checkbox y actualiza _selected_paths."""
        if not item.isCheckable():
            return

        rel_path = item.data(Qt.ItemDataRole.UserRole)
        is_dir = item.data(IS_DIRECTORY_ROLE) 
        new_check_state = item.checkState()

        # El estado del 'item' ya fue cambiado por la UI antes de que este handler sea llamado.
        # Ahora necesitamos propagar este cambio a _selected_paths y a los hijos/padres en la UI.

        if new_check_state == Qt.CheckState.Checked:
            self._apply_selection_recursive(item, rel_path, is_dir, True)
        elif new_check_state == Qt.CheckState.Unchecked:
            self._apply_selection_recursive(item, rel_path, is_dir, False)
        
        self._update_parent_state(item) # Actualizar estado visual de los padres

    def _apply_selection_recursive(self, item: QStandardItem, rel_path: str, is_dir: bool, select: bool):
        """
        Aplica el estado de selección (select=True para marcar, False para desmarcar)
        al ítem y sus descendientes, actualizando _selected_paths para archivos.
        También actualiza el checkState de la UI para los ítems afectados.
        """
        target_state = Qt.CheckState.Checked if select else Qt.CheckState.Unchecked

        # Actualizar _selected_paths para el ítem actual si es un archivo
        if not is_dir: # Es un archivo
            if select:
                self._selected_paths.add(rel_path)
            else:
                self._selected_paths.discard(rel_path)
        
        # Asegurar que el estado visual del ítem actual sea el correcto
        # Esto es importante porque `handle_item_changed` se llama *después* de que el estado del item
        # clickeado ya cambió. Para los hijos, necesitamos cambiarlo nosotros.
        if item.checkState() != target_state:
             item.setCheckState(target_state) # Actualiza UI, pero la señal principal está desconectada

        # Si es un directorio, aplicar recursivamente a los hijos
        if is_dir:
            for i in range(item.rowCount()):
                child = item.child(i)
                child_rel_path = child.data(Qt.ItemDataRole.UserRole)
                child_is_dir = child.data(IS_DIRECTORY_ROLE)
                
                # Llamada recursiva para procesar al hijo
                # No solo cambiamos su checkState, sino que llamamos a la lógica completa
                # para asegurar que _selected_paths se actualice para sub-archivos.
                self._apply_selection_recursive(child, child_rel_path, child_is_dir, select)


    def _update_parent_state(self, item: QStandardItem) -> None:
        """Actualiza el estado de check del padre de 'item' y sus ancestros."""
        parent = item.parent()
        if parent is None or parent == self._model.invisibleRootItem():
            return
        
        # El estado del padre se calcula y se establece.
        # Si setCheckState aquí dispara itemChanged, el guardián en main_window lo maneja.
        self._calculate_and_set_folder_state_from_children(parent)
        
        # Propagar hacia arriba recursivamente
        self._update_parent_state(parent) 

    # ------------------------------------------------------------------
    # OTHER PUBLIC UTILITIES
    # ------------------------------------------------------------------
    def reset_selection(self) -> None:
        """Deselecciona todos los ítems y limpia _selected_paths."""
        self._selected_paths.clear()
        if self._base_path: 
             self.populate_tree() # Repoblar asegura UI limpia y estados de carpeta correctos