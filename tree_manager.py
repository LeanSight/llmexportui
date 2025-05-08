from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional, Set

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel

from path_utils import normalize_path

__all__ = ["TreeManager"]


class TreeManager:
    """Administra el árbol de archivos y la lógica de selección."""

    # ---------------------------------------------------------------------
    # INITIALISATION
    # ---------------------------------------------------------------------
    def __init__(self, tree_model: QStandardItemModel) -> None:
        self._model: QStandardItemModel = tree_model
        self._base_path: Path | None = None
        self._selected_paths: Set[str] = set()
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
        """Carga la selección previamente almacenada (sin validar)."""
        self._selected_paths = set(paths)

    # ------------------------------------------------------------------
    # PUBLIC QUERIES
    # ------------------------------------------------------------------
    def get_selected_paths(self) -> Set[str]:
        """Devuelve las rutas actualmente seleccionadas (relativas)."""
        return set(self._selected_paths)

    # ------------------------------------------------------------------
    # TREE BUILDING ------------------------------------------------------
    # ------------------------------------------------------------------
    def populate_tree(self) -> None:
        """Reconstruye el modelo en memoria a partir del disco."""
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["Nombre"])

        if self._base_path is None:
            return

        # Asegurar que la selección esté saneada antes de dibujar.
        self._prune_nonexistent_selections()

        root_item = self._model.invisibleRootItem()
        base_item = QStandardItem(self._base_path.name)
        base_item.setData("", Qt.ItemDataRole.UserRole)
        base_item.setCheckable(True)
        base_item.setCheckState(self._initial_state_for(""))
        root_item.appendRow(base_item)

        self._add_directory(base_item, self._base_path, rel_path="")

    # ------------------------------------------------------------------
    # PRIVATE HELPERS ----------------------------------------------------
    # ------------------------------------------------------------------
    def _prune_nonexistent_selections(self) -> None:
        """Elimina de *self._selected_paths* los archivos que ya no existen."""
        if self._base_path is None:
            return

        valid: Set[str] = set()
        for rel in self._selected_paths:
            if (self._base_path / rel).exists():
                valid.add(rel)
        self._selected_paths = valid

    # ---------------------------------------------------------------
    # MODEL CONSTRUCTION
    # ---------------------------------------------------------------
    def _add_directory(
        self,
        parent_item: QStandardItem,
        abs_dir: Path,
        *,
        rel_path: str,
    ) -> None:
        try:
            for name in sorted(os.listdir(abs_dir), key=str.lower):
                child_abs = abs_dir / name
                child_rel = str(Path(rel_path, name)) if rel_path else name

                visible = self._is_visible(child_rel) if self._is_visible else True
                if not visible and child_abs.is_dir():
                    # Comprobar visibilidad de nietos
                    visible = self._has_visible_descendants(child_abs)
                if not visible:
                    continue

                item = QStandardItem(name)
                item.setData(child_rel, Qt.ItemDataRole.UserRole)
                item.setCheckable(True)
                item.setCheckState(self._initial_state_for(child_rel))
                parent_item.appendRow(item)

                if child_abs.is_dir():
                    self._add_directory(item, child_abs, rel_path=child_rel)
        except PermissionError:
            # Directorio inaccesible: se ignora.
            pass

    def _initial_state_for(self, rel_path: str) -> Qt.CheckState:
        if rel_path in self._selected_paths:
            return Qt.CheckState.Checked
        if self._has_selected_descendants(rel_path):
            return Qt.CheckState.PartiallyChecked
        return Qt.CheckState.Unchecked

    # ---------------------------------------------------------------
    # VISIBILITY & SELECTION UTILITIES
    # ---------------------------------------------------------------
    def _has_visible_descendants(self, abs_dir: Path) -> bool:
        if self._is_visible is None:
            return False
        for root, _dirs, files in os.walk(abs_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), self._base_path)
                if self._is_visible(rel):
                    return True
        return False

    def _has_selected_descendants(self, rel_path: str) -> bool:
        base = normalize_path(rel_path)
        if base:
            base += os.sep
        for sel in self._selected_paths:
            if normalize_path(sel).startswith(base):
                return True
        return False

    # ------------------------------------------------------------------
    # CHECKBOX HANDLERS -------------------------------------------------
    # ------------------------------------------------------------------
    def handle_item_changed(self, item: QStandardItem) -> None:
        if not item.isCheckable():
            return

        rel_path = item.data(Qt.ItemDataRole.UserRole)
        state = item.checkState()

        if state == Qt.CheckState.Checked:
            self._add_path_recursive(rel_path, item)
        elif state == Qt.CheckState.Unchecked:
            self._remove_path_recursive(rel_path, item)

        # Recalcular estados de ancestros
        self._update_parent_state(item)

    def _add_path_recursive(self, rel_path: str, item: QStandardItem) -> None:
        self._selected_paths.add(rel_path)
        for i in range(item.rowCount()):
            child = item.child(i)
            if child.checkState() != Qt.CheckState.Checked:
                child.setCheckState(Qt.CheckState.Checked)
            self._add_path_recursive(child.data(Qt.ItemDataRole.UserRole), child)

    def _remove_path_recursive(self, rel_path: str, item: QStandardItem) -> None:
        self._selected_paths.discard(rel_path)
        for i in range(item.rowCount()):
            child = item.child(i)
            if child.checkState() != Qt.CheckState.Unchecked:
                child.setCheckState(Qt.CheckState.Unchecked)
            self._remove_path_recursive(child.data(Qt.ItemDataRole.UserRole), child)

    def _update_parent_state(self, item: QStandardItem) -> None:
        parent = item.parent()
        if parent is None:
            return
        checked = sum(1 for i in range(parent.rowCount()) if parent.child(i).checkState() == Qt.CheckState.Checked)
        partial = sum(1 for i in range(parent.rowCount()) if parent.child(i).checkState() == Qt.CheckState.PartiallyChecked)
        if checked == parent.rowCount():
            parent.setCheckState(Qt.CheckState.Checked)
        elif checked == 0 and partial == 0:
            parent.setCheckState(Qt.CheckState.Unchecked)
        else:
            parent.setCheckState(Qt.CheckState.PartiallyChecked)
        self._update_parent_state(parent)

    # ------------------------------------------------------------------
    # OTHER PUBLIC UTILITIES -------------------------------------------
    # ------------------------------------------------------------------
    def reset_selection(self) -> None:
        self._selected_paths.clear()
        root = self._model.invisibleRootItem()
        for i in range(root.rowCount()):
            self._uncheck_all(root.child(i))

    def _uncheck_all(self, item: QStandardItem) -> None:
        item.setCheckState(Qt.CheckState.Unchecked)
        for i in range(item.rowCount()):
            self._uncheck_all(item.child(i))
