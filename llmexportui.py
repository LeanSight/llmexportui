import os
import sys
import argparse
from PyQt6.QtWidgets import QApplication

from main_window import LLMExportApp

def main():
    """Punto de entrada principal de la aplicación"""
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

if __name__ == "__main__":
    main()