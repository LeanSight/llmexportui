import locale
import os

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
        'include_filter_label': 'Include:',
        'exclude_filter_label': 'Exclude:',
        'include_filter_placeholder': 'Patterns to include (e.g.: *.py, **/*.md)',
        'exclude_filter_placeholder': 'Patterns to exclude (e.g.: **/__pycache__/, *.log)',
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
        'filter_section': 'Filters',
        'showing_items': 'Showing {visible} of {total} items',
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
        'include_filter_label': 'Incluir:',
        'exclude_filter_label': 'Excluir:',
        'include_filter_placeholder': 'Patrones para incluir (ej: *.py, **/*.md)',
        'exclude_filter_placeholder': 'Patrones para excluir (ej: **/__pycache__/, *.log)',
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
        'filter_section': 'Filtros',
        'showing_items': 'Mostrando {visible} de {total} elementos',
    }
}

def get_system_language():
    """
    Detecta el idioma del sistema operativo.
    
    Returns:
        str: Código de idioma ('en' o 'es')
    """
    try:
        # Método actualizado para evitar advertencias de deprecación
        locale.setlocale(locale.LC_ALL, '')
        lang_code = locale.getlocale()[0]
        if lang_code and lang_code.startswith('es'):
            return 'es'
            
        # Alternativa para sistemas donde getlocale() podría no funcionar
        env_lang = os.environ.get('LANG', '') or os.environ.get('LANGUAGE', '') or os.environ.get('LC_ALL', '')
        if env_lang and env_lang.startswith('es'):
            return 'es'
    except Exception:
        pass
    return 'en'

def translate(key, language, **kwargs):
    """
    Traduce una clave al idioma especificado.
    
    Args:
        key (str): Clave de traducción
        language (str): Código de idioma
        **kwargs: Variables para interpolar en la cadena traducida
        
    Returns:
        str: Cadena traducida
    """
    try:
        text = TRANSLATIONS[language][key]
        # Soporte para interpolación de variables
        if kwargs and '{' in text:
            return text.format(**kwargs)
        return text
    except KeyError:
        return key