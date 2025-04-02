import os
import fnmatch
from typing import List, Dict, Set, Callable, Optional

from path_utils import matches_pattern, normalize_path, is_subpath

class FilterEngine:
    """
    Motor de filtrado para incluir/excluir archivos según patrones.
    Implementado como clase para facilitar uso con PyQt6.
    """
    
    def __init__(self):
        """Inicializa un nuevo motor de filtro"""
        self.include_patterns = []
        self.exclude_patterns = []
        self._visible_items = set()  # Cache de items visibles
        self._base_path = ""
    
    def set_base_path(self, path: str) -> None:
        """
        Establece la ruta base para resolución de paths relativos
        
        Args:
            path: Ruta base para filtrado
        """
        self._base_path = path
        self._refresh_cache()
    
    def set_include_patterns(self, patterns: str) -> None:
        """
        Establece los patrones de inclusión
        
        Args:
            patterns: Cadena de patrones separados por coma
        """
        self.include_patterns = self._parse_patterns(patterns)
        self._refresh_cache()
    
    def set_exclude_patterns(self, patterns: str) -> None:
        """
        Establece los patrones de exclusión
        
        Args:
            patterns: Cadena de patrones separados por coma
        """
        self.exclude_patterns = self._parse_patterns(patterns)
        self._refresh_cache()
    
    def is_visible(self, path: str) -> bool:
        """
        Determina si una ruta debe ser visible según los filtros actuales
        
        Args:
            path: Ruta a comprobar (relativa a la base)
            
        Returns:
            bool: True si la ruta debe ser visible
        """
        # Si no hay filtros, todo es visible
        if not self.include_patterns and not self.exclude_patterns:
            return True
        
        # Normalizar la ruta para el sistema actual
        norm_path = normalize_path(path)
        
        # Comprobar si es exactamente uno de los items cacheados como visibles
        if norm_path in self._visible_items:
            return True
        
        # Comprobar si es padre de algún item visible
        for visible_item in self._visible_items:
            if is_subpath(norm_path, visible_item):
                return True
        
        return False
    
    def _parse_patterns(self, pattern_str: str) -> List[str]:
        """
        Convierte una cadena de patrones separados por coma en una lista
        
        Args:
            pattern_str: Cadena con patrones separados por coma
            
        Returns:
            List[str]: Lista de patrones normalizados
        """
        if not pattern_str or not pattern_str.strip():
            return []
        
        # Dividir por comas, eliminar espacios y normalizar separadores
        return [normalize_path(p.strip()) for p in pattern_str.split(',') if p.strip()]
    
    def _refresh_cache(self) -> None:
        """
        Reconstruye la caché de items visibles según los filtros actuales
        """
        self._visible_items = set()
        
        # Si no hay path base, no podemos aplicar filtros
        if not self._base_path:
            return
        
        # Si no hay patrones de inclusión, inicialmente incluimos todo
        if not self.include_patterns:
            self._collect_all_files(self._base_path)
        else:
            # Sino, solo incluimos lo que coincide con los patrones
            self._collect_matching_files(self._base_path, self.include_patterns)
        
        # Luego excluimos lo que coincide con los patrones de exclusión
        if self.exclude_patterns:
            self._exclude_matching_files(self._base_path, self.exclude_patterns)
    
    def _collect_all_files(self, dir_path: str) -> None:
        """
        Recoge recursivamente todos los archivos bajo un directorio
        
        Args:
            dir_path: Directorio a recorrer
        """
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self._base_path)
                    self._visible_items.add(normalize_path(rel_path))
        except Exception:
            # Ignorar errores de acceso a archivos/directorios
            pass
    
    def _collect_matching_files(self, dir_path: str, patterns: List[str]) -> None:
        """
        Recoge archivos que coinciden con los patrones de inclusión
        
        Args:
            dir_path: Directorio a recorrer
            patterns: Lista de patrones para comprobar
        """
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self._base_path)
                    norm_rel_path = normalize_path(rel_path)
                    
                    # Verificar si coincide con algún patrón
                    for pattern in patterns:
                        if matches_pattern(norm_rel_path, pattern):
                            self._visible_items.add(norm_rel_path)
                            break
        except Exception:
            # Ignorar errores de acceso a archivos/directorios
            pass
    
    def _exclude_matching_files(self, dir_path: str, patterns: List[str]) -> None:
        """
        Excluye archivos que coinciden con los patrones de exclusión
        
        Args:
            dir_path: Directorio a recorrer
            patterns: Lista de patrones para excluir
        """
        to_remove = set()
        
        for item in self._visible_items:
            for pattern in patterns:
                if matches_pattern(item, pattern):
                    to_remove.add(item)
                    break
        
        # Eliminar los items que coinciden con patrones de exclusión
        self._visible_items -= to_remove