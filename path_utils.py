import os

def normalize_path(path):
    """
    Normaliza una ruta de archivo para asegurar consistencia en comparaciones.
    Convierte todos los separadores a formato unificado.
    
    Args:
        path (str): La ruta a normalizar
        
    Returns:
        str: Ruta normalizada
    """
    # Normalizar a backslash (estilo Windows) para consistencia
    return path.replace('/', '\\')

def get_relative_path(base_path, full_path):
    """
    Obtiene la ruta relativa desde una ruta base hasta una ruta completa.
    
    Args:
        base_path (str): La ruta base
        full_path (str): La ruta completa
        
    Returns:
        str: Ruta relativa o cadena vacía si la ruta completa no contiene la base
    """
    try:
        return os.path.relpath(full_path, base_path)
    except ValueError:
        # En caso de que las rutas estén en diferentes unidades
        return ""

def is_subpath(parent, child):
    """
    Determina si una ruta es subpath de otra.
    
    Args:
        parent (str): La ruta padre
        child (str): La ruta a verificar si es subpath
        
    Returns:
        bool: True si child es subpath de parent
    """
    parent = os.path.normpath(parent)
    child = os.path.normpath(child)
    
    # Verificar si child comienza con parent y hay un separador después
    return child.startswith(parent) and (
        len(child) == len(parent) or
        child[len(parent)] == os.path.sep
    )

def matches_pattern(path, pattern):
    """
    Verifica si una ruta coincide con un patrón glob.
    Esta es una implementación simple que soporta * y ** para coincidencias.
    
    Args:
        path (str): La ruta a verificar
        pattern (str): El patrón glob a comprobar
        
    Returns:
        bool: True si la ruta coincide con el patrón
    """
    # Implementación básica - en producción usaríamos pathlib o glob
    import fnmatch
    
    # Normalizar separadores para tener consistencia
    norm_path = normalize_path(path)
    norm_pattern = normalize_path(pattern)
    
    # Caso especial para **/ que significa cualquier nivel de directorios
    if "**" in norm_pattern:
        parts = norm_pattern.split("**")
        if len(parts) == 2:
            # Caso simple de un solo **
            return norm_path.startswith(parts[0]) and norm_path.endswith(parts[1])
    
    # Para patrones simples usar fnmatch
    return fnmatch.fnmatch(norm_path, norm_pattern)