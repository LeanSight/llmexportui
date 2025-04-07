import os
from typing import Set, List, Dict, Optional


def generate_export_content(base_folder: str, selected_paths: Set[str]) -> str:
    """
    Genera el contenido exportado en formato LLM-friendly
    
    Args:
        base_folder: Carpeta base para resolución de rutas
        selected_paths: Conjunto de rutas seleccionadas (relativas a base_folder)
        
    Returns:
        str: Contenido formateado para exportación
    """
    # Formato similar a Gitingest
    result = ["Directory structure:"]
    
    # Generar estructura de directorios
    dir_structure = _generate_directory_structure(base_folder, selected_paths)
    result.append(dir_structure)
    result.append("")  # Línea en blanco
    
    # Generar contenido de archivos
    file_contents = _generate_file_contents(base_folder, selected_paths)
    result.append(file_contents)
    
    return "\n".join(result)


def _generate_directory_structure(base_folder: str, selected_paths: Set[str]) -> str:
    """
    Genera representación en árbol de la estructura de directorios
    
    Args:
        base_folder: Carpeta base para resolución de rutas
        selected_paths: Conjunto de rutas seleccionadas
        
    Returns:
        str: Representación en texto de la estructura de directorios
    """
    lines = []
    
    # Nombre de la carpeta base
    base_name = os.path.basename(base_folder)
    lines.append(f"└── {base_name}/")
    
    # Organizar rutas por nivel para construir el árbol
    paths_by_level = {}
    for path in sorted(selected_paths):
        parts = path.split(os.sep)
        level = len(parts)
        
        if level not in paths_by_level:
            paths_by_level[level] = []
        
        paths_by_level[level].append(path)
    
    # Construir árbol de forma iterativa por niveles
    _build_tree_structure(lines, paths_by_level, base_folder, "", 1, "    ")
    
    return "\n".join(lines)


def _build_tree_structure(
    lines: List[str], 
    paths_by_level: Dict[int, List[str]], 
    base_folder: str, 
    parent_path: str, 
    level: int,
    prefix: str = ""
) -> None:
    """
    Construye la estructura de árbol recursivamente
    
    Args:
        lines: Lista de líneas de salida
        paths_by_level: Rutas organizadas por nivel de profundidad
        base_folder: Carpeta base para resolución de rutas
        parent_path: Ruta padre actual
        level: Nivel actual en la jerarquía
        prefix: Prefijo para la indentación actual
    """
    if level not in paths_by_level:
        return
    
    # Filtrar elementos en este nivel que pertenecen al padre actual
    current_level_items = []
    for path in paths_by_level[level]:
        # Verificar si este elemento pertenece directamente al padre actual
        path_parent = os.path.dirname(path)
        if path_parent == parent_path:
            current_level_items.append(path)
    
    # Si no hay elementos en este nivel para este padre, salir
    if not current_level_items:
        return
    
    # Ordenar: primero carpetas, luego archivos
    current_level_items.sort(key=lambda p: (
        not os.path.isdir(os.path.join(base_folder, p)), 
        os.path.basename(p).lower()
    ))
    
    # Índice para el último elemento
    last_idx = len(current_level_items) - 1
    
    # Procesar cada elemento
    for i, item in enumerate(current_level_items):
        is_last = i == last_idx
        
        # Construir prefijo para este elemento
        item_prefix = prefix
        item_prefix += "└── " if is_last else "├── "
        
        # Nombre base del elemento
        item_name = os.path.basename(item)
        
        # Es un directorio?
        is_dir = os.path.isdir(os.path.join(base_folder, item))
        
        # Añadir a la salida
        if is_dir:
            lines.append(f"{item_prefix}{item_name}/")
        else:
            lines.append(f"{item_prefix}{item_name}")
        
        # Recursión para subdirectorios
        if is_dir:
            # Prefijo para los hijos
            child_prefix = prefix
            child_prefix += "    " if is_last else "│   "
            
            # Procesar nivel siguiente para este directorio
            _build_tree_structure(lines, paths_by_level, base_folder, item, level + 1, child_prefix)


def _generate_file_contents(base_folder: str, selected_paths: Set[str]) -> str:
    """
    Genera el contenido de archivos seleccionados
    
    Args:
        base_folder: Carpeta base para resolución de rutas
        selected_paths: Conjunto de rutas seleccionadas
        
    Returns:
        str: Contenido formateado de los archivos
    """
    content = []
    
    # Procesar archivos seleccionados
    for rel_path in sorted(selected_paths):
        full_path = os.path.join(base_folder, rel_path)
        
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