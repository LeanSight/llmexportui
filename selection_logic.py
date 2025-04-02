from typing import Dict, Set, List, Callable, Any, Tuple, Optional
import os
from path_utils import normalize_path, is_subpath, matches_pattern

# Tipo para representar el estado de un item
# PathState = Dict[str, bool]  # {"selected": bool, "partial": bool}

def create_empty_state() -> Dict[str, Dict[str, bool]]:
    """
    Crea un estado de selección vacío
    
    Returns:
        Un diccionario vacío para almacenar estados
    """
    return {}

def get_item_state(state: Dict[str, Dict[str, bool]], path: str) -> Dict[str, bool]:
    """
    Obtiene el estado de un item, o un estado por defecto si no existe
    
    Args:
        state: Estado global de selección
        path: Ruta del item
    
    Returns:
        Estado del item (selected, partial)
    """
    norm_path = normalize_path(path)
    if norm_path not in state:
        state[norm_path] = {"selected": False, "partial": False}
    return state[norm_path]

def set_item_state(
    state: Dict[str, Dict[str, bool]], 
    path: str, 
    selected: bool, 
    partial: bool = False
) -> Dict[str, Dict[str, bool]]:
    """
    Establece el estado de un item
    
    Args:
        state: Estado global de selección
        path: Ruta del item
        selected: Si está seleccionado
        partial: Si está parcialmente seleccionado
    
    Returns:
        Estado actualizado
    """
    # Crear una copia para mantener inmutabilidad
    new_state = state.copy()
    norm_path = normalize_path(path)
    new_state[norm_path] = {"selected": selected, "partial": partial}
    return new_state

def is_selected(state: Dict[str, Dict[str, bool]], path: str) -> bool:
    """
    Comprueba si un item está seleccionado
    
    Args:
        state: Estado global de selección
        path: Ruta del item
    
    Returns:
        True si está seleccionado
    """
    item_state = get_item_state(state, path)
    return item_state["selected"]

def is_partially_selected(state: Dict[str, Dict[str, bool]], path: str) -> bool:
    """
    Comprueba si un item está parcialmente seleccionado
    
    Args:
        state: Estado global de selección
        path: Ruta del item
    
    Returns:
        True si está parcialmente seleccionado
    """
    item_state = get_item_state(state, path)
    return item_state["partial"]

def get_parent_path(path: str) -> str:
    """
    Obtiene la ruta del directorio padre
    
    Args:
        path: Ruta del item
    
    Returns:
        Ruta del directorio padre o cadena vacía si está en la raíz
    """
    if not path:
        return ""
    
    parent = os.path.dirname(path)
    return parent

def get_selected_paths(state: Dict[str, Dict[str, bool]]) -> Set[str]:
    """
    Obtiene el conjunto de rutas seleccionadas
    
    Args:
        state: Estado global de selección
    
    Returns:
        Conjunto de rutas seleccionadas
    """
    return {
        path for path, item_state in state.items() 
        if item_state["selected"] and not item_state["partial"]
    }

# Comportamientos de selección (funciones de orden superior)

def standard_behavior() -> Dict[str, Callable]:
    """
    Comportamiento estándar para selección de items:
    - Seleccionar propaga hacia abajo (padres a hijos)
    - Estado de padres refleja el de sus hijos
    
    Returns:
        Diccionario con funciones de comportamiento
    """
    return {
        "propagate_down": lambda _state, _path: True,  # Siempre propaga hacia abajo
        "recalculate_up": lambda children_states: all(children_states)  # Todos seleccionados
    }

def filter_aware_behavior(is_visible_fn: Callable[[str], bool]) -> Dict[str, Callable]:
    """
    Comportamiento que respeta filtros:
    - Solo propaga a elementos visibles
    - Solo considera elementos visibles al determinar estado de padres
    
    Args:
        is_visible_fn: Función que determina si un item es visible
    
    Returns:
        Diccionario con funciones de comportamiento
    """
    return {
        "propagate_down": lambda _state, path: is_visible_fn(path),
        "recalculate_up": lambda children_states, visibilities: (
            any(children_states) if any(visibilities) else False
        )
    }

def pattern_selection_behavior(pattern_matches_fn: Callable[[str], bool]) -> Dict[str, Callable]:
    """
    Comportamiento que selecciona según un patrón específico
    
    Args:
        pattern_matches_fn: Función que comprueba si una ruta coincide con el patrón
    
    Returns:
        Diccionario con funciones de comportamiento
    """
    return {
        "propagate_down": lambda _state, _path: True,
        "transform": lambda _current_state, path: pattern_matches_fn(path)
    }

def inverse_selection_behavior() -> Dict[str, Callable]:
    """
    Comportamiento que invierte la selección actual
    
    Returns:
        Diccionario con funciones de comportamiento
    """
    return {
        "propagate_down": lambda _state, _path: True,
        "transform": lambda current_state, _path: not current_state["selected"]
    }

# Funciones principales de selección

def toggle_selection(
    state: Dict[str, Dict[str, bool]], 
    path: str, 
    children: List[str], 
    behavior: Dict[str, Callable],
    is_visible_fn: Optional[Callable[[str], bool]] = None
) -> Dict[str, Dict[str, bool]]:
    """
    Alterna el estado de selección de un item y propaga según el comportamiento
    
    Args:
        state: Estado actual de selección
        path: Ruta del item a alternar
        children: Lista de rutas hijas
        behavior: Comportamiento de selección a aplicar
        is_visible_fn: Función opcional para determinar visibilidad
    
    Returns:
        Nuevo estado con la selección actualizada
    """
    # Obtenemos el estado actual y lo invertimos
    item_state = get_item_state(state, path)
    new_selected = not item_state["selected"]
    
    # Aplicar transformación personalizada si existe
    if "transform" in behavior:
        new_selected = behavior["transform"](item_state, path)
    
    # Comenzamos con un nuevo estado actualizado para este item
    new_state = set_item_state(state, path, new_selected)
    
    # Propagar hacia abajo si el comportamiento lo indica
    if new_selected and behavior.get("propagate_down", lambda _s, _p: True)(state, path):
        for child in children:
            # Verificar si debemos propagar a este hijo según la visibilidad
            should_propagate = True
            if is_visible_fn:
                should_propagate = is_visible_fn(child)
            
            if should_propagate:
                child_children = []  # Aquí se debería pasar la lista real de hijos
                new_state = toggle_selection(
                    new_state, 
                    child, 
                    child_children, 
                    behavior,
                    is_visible_fn
                )
    
    # Propagar hacia arriba (actualizar estado del padre)
    parent = get_parent_path(path)
    if parent:
        # Si tenemos función de visibilidad, filtrar hijos no visibles
        siblings = []  # Aquí se debería pasar la lista real de hermanos
        
        # Obtener estados de los hermanos
        sibling_states = [get_item_state(new_state, s)["selected"] for s in siblings]
        sibling_visibility = [True] * len(siblings)
        if is_visible_fn:
            sibling_visibility = [is_visible_fn(s) for s in siblings]
        
        # Calcular nuevo estado del padre según el comportamiento
        all_selected = behavior.get("recalculate_up", lambda s: all(s))(sibling_states)
        any_selected = any(s and v for s, v in zip(sibling_states, sibling_visibility))
        
        # Actualizar estado del padre
        if all_selected:
            new_state = set_item_state(new_state, parent, True, False)
        elif any_selected:
            new_state = set_item_state(new_state, parent, True, True)
        else:
            new_state = set_item_state(new_state, parent, False, False)
    
    return new_state

def apply_pattern_selection(
    state: Dict[str, Dict[str, bool]], 
    pattern: str, 
    all_paths: List[str]
) -> Dict[str, Dict[str, bool]]:
    """
    Aplica una selección basada en patrón a todos los items
    
    Args:
        state: Estado actual de selección
        pattern: Patrón glob a aplicar
        all_paths: Lista de todas las rutas disponibles
    
    Returns:
        Nuevo estado con la selección basada en patrón
    """
    # Crear un nuevo estado vacío
    new_state = create_empty_state()
    
    # Función que comprueba si una ruta coincide con el patrón
    def matches(p: str) -> bool:
        return matches_pattern(p, pattern)
    
    # Crear comportamiento de selección por patrón
    behavior = pattern_selection_behavior(matches)
    
    # Aplicar a todas las rutas
    for path in all_paths:
        item_state = get_item_state(state, path)
        should_select = behavior["transform"](item_state, path)
        new_state = set_item_state(new_state, path, should_select)
    
    return new_state

def combine_behaviors(*behaviors):
    """
    Combina múltiples comportamientos, aplicando sus reglas en secuencia
    
    Args:
        *behaviors: Comportamientos a combinar
    
    Returns:
        Comportamiento combinado
    """
    combined = {}
    
    # Combinar propagate_down (AND lógico: solo propaga si todos lo permiten)
    if any("propagate_down" in b for b in behaviors):
        propagate_fns = [b.get("propagate_down", lambda _s, _p: True) for b in behaviors]
        combined["propagate_down"] = lambda state, path: all(fn(state, path) for fn in propagate_fns)
    
    # Combinar recalculate_up (usar el último comportamiento con esta función)
    for b in reversed(behaviors):
        if "recalculate_up" in b:
            combined["recalculate_up"] = b["recalculate_up"]
            break
    
    # Combinar transform (aplicar transformaciones en secuencia)
    transform_fns = [b.get("transform") for b in behaviors if "transform" in b]
    if transform_fns:
        def combined_transform(current_state, path):
            result = current_state["selected"]
            for fn in transform_fns:
                result = fn({"selected": result}, path)
            return result
        combined["transform"] = combined_transform
    
    return combined