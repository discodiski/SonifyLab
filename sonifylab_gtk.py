#!/usr/bin/env python3
"""
SonifyLab Pro - Conversor de Audio (GTK4 + Libadwaita)
=======================================================

Una aplicación de escritorio moderna para convertir archivos de audio
entre múltiples formatos utilizando FFmpeg como motor de conversión.

Autor: Discaury Salas
Licencia: GPL-3.0
Repositorio: https://github.com/discodiski/SonifyLab
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, GObject, Pango
import subprocess
import threading
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Información de la aplicación
__version__ = "2.0.0"
__author__ = "Discaury Salas"
__app_name__ = "SonifyLab Pro"
__app_id__ = "com.discodiski.sonifylab"

# Directorio de la aplicación
APP_DIR: Path = Path(__file__).parent.resolve()
LOG_FILE: Path = APP_DIR / 'conversion.log'
CONVERSION_LOG: Path = APP_DIR / 'conversion_history.jsonl'

# Configuración del registro
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Formatos y bitrates soportados
SUPPORTED_FORMATS: List[str] = [
    "mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "alac"
]

BITRATE_OPTIONS: List[str] = ["128k", "192k", "256k", "320k"]


class FileItem(GObject.Object):
    """Modelo de datos para un archivo en la lista."""
    
    __gtype_name__ = 'FileItem'
    
    def __init__(self, path: str, name: str):
        super().__init__()
        self._path = path
        self._name = name
        self._status = "En espera"
        self._progress = 0.0
        self._info = ""
    
    @GObject.Property(type=str)
    def path(self) -> str:
        return self._path
    
    @GObject.Property(type=str)
    def name(self) -> str:
        return self._name
    
    @GObject.Property(type=str)
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
    
    @GObject.Property(type=float)
    def progress(self) -> float:
        return self._progress
    
    @progress.setter
    def progress(self, value: float):
        self._progress = value
    
    @GObject.Property(type=str)
    def info(self) -> str:
        return self._info
    
    @info.setter
    def info(self, value: str):
        self._info = value


class SonifyLabWindow(Adw.ApplicationWindow):
    """Ventana principal de SonifyLab Pro."""
    
    def __init__(self, app):
        super().__init__(application=app, title=__app_name__)
        self.set_default_size(950, 700)
        self.set_size_request(800, 650)
        
        # Estado de la aplicación
        self.files: List[FileItem] = []
        self.output_folder: str = ""
        self.is_converting: bool = False
        self.conversion_threads: List[threading.Thread] = []
        self.completed_count: int = 0
        self.total_count: int = 0
        
        # Crear el modelo de lista
        self.list_store = Gio.ListStore.new(FileItem)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Contenedor principal con HeaderBar
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # === HEADER BAR ===
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(
            title=__app_name__,
            subtitle="Conversor de audio profesional"
        ))
        
        # Botón de menú
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append("Acerca de", "app.about")
        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)
        
        main_box.append(header)
        
        # === CONTENIDO PRINCIPAL (sin scroll) ===
        content = Adw.Clamp()
        content.set_maximum_size(1200)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        content.set_margin_start(15)
        content.set_margin_end(15)
        content.set_vexpand(True)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_child(content_box)
        main_box.append(content)
        
        # === SECCIÓN: ARCHIVOS DE ENTRADA ===
        files_group = Adw.PreferencesGroup()
        files_group.set_title("Archivos de entrada")
        content_box.append(files_group)
        
        # Lista de archivos
        self.files_listbox = Gtk.ListBox()
        self.files_listbox.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.files_listbox.add_css_class("boxed-list")
        self.files_listbox.set_placeholder(self.create_placeholder())
        files_group.add(self.files_listbox)
        
        # Botones de archivos
        files_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        files_buttons.set_halign(Gtk.Align.START)
        files_buttons.set_margin_top(10)
        
        add_btn = Gtk.Button(label="Añadir archivos")
        add_btn.add_css_class("suggested-action")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self.on_add_files)
        files_buttons.append(add_btn)
        
        add_folder_btn = Gtk.Button(label="Añadir carpeta")
        add_folder_btn.set_icon_name("folder-open-symbolic")
        add_folder_btn.connect("clicked", self.on_add_folder)
        files_buttons.append(add_folder_btn)
        
        remove_btn = Gtk.Button(label="Eliminar")
        remove_btn.set_icon_name("list-remove-symbolic")
        remove_btn.connect("clicked", self.on_remove_files)
        files_buttons.append(remove_btn)
        
        clear_btn = Gtk.Button(label="Limpiar")
        clear_btn.set_icon_name("edit-clear-all-symbolic")
        clear_btn.connect("clicked", self.on_clear_files)
        files_buttons.append(clear_btn)
        
        files_group.add(files_buttons)
        
        # === SECCIÓN: CONFIGURACIÓN ===
        config_group = Adw.PreferencesGroup()
        config_group.set_title("Configuración")
        content_box.append(config_group)
        
        # Carpeta de salida
        output_row = Adw.ActionRow()
        output_row.set_title("Carpeta de salida")
        
        self.output_label = Gtk.Label(label="No seleccionada")
        self.output_label.add_css_class("dim-label")
        self.output_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.output_label.set_max_width_chars(30)
        output_row.add_suffix(self.output_label)
        
        output_btn = Gtk.Button(icon_name="folder-open-symbolic")
        output_btn.set_valign(Gtk.Align.CENTER)
        output_btn.add_css_class("flat")
        output_btn.connect("clicked", self.on_select_output)
        output_row.add_suffix(output_btn)
        output_row.set_activatable_widget(output_btn)
        config_group.add(output_row)
        
        # Formato de salida
        format_row = Adw.ComboRow()
        format_row.set_title("Formato")
        format_model = Gtk.StringList.new(SUPPORTED_FORMATS)
        format_row.set_model(format_model)
        format_row.set_selected(0)  # mp3 por defecto
        self.format_row = format_row
        config_group.add(format_row)
        
        # Bitrate
        bitrate_row = Adw.ComboRow()
        bitrate_row.set_title("Calidad")
        bitrate_model = Gtk.StringList.new(BITRATE_OPTIONS)
        bitrate_row.set_model(bitrate_model)
        bitrate_row.set_selected(1)  # 192k por defecto
        self.bitrate_row = bitrate_row
        config_group.add(bitrate_row)
        
        # Sobrescribir archivos
        overwrite_row = Adw.SwitchRow()
        overwrite_row.set_title("Sobrescribir existentes")
        self.overwrite_row = overwrite_row
        config_group.add(overwrite_row)
        
        # === SECCIÓN: CONVERSIÓN ===
        conversion_group = Adw.PreferencesGroup()
        conversion_group.set_title("Conversión")
        content_box.append(conversion_group)
        
        # Botones de conversión
        conversion_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        conversion_buttons.set_halign(Gtk.Align.START)
        
        self.convert_btn = Gtk.Button(label="Iniciar Conversión")
        self.convert_btn.add_css_class("suggested-action")
        self.convert_btn.add_css_class("pill")
        self.convert_btn.set_icon_name("media-playback-start-symbolic")
        self.convert_btn.connect("clicked", self.on_start_conversion)
        conversion_buttons.append(self.convert_btn)
        
        self.stop_btn = Gtk.Button(label="Detener")
        self.stop_btn.add_css_class("destructive-action")
        self.stop_btn.add_css_class("pill")
        self.stop_btn.set_icon_name("media-playback-stop-symbolic")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", self.on_stop_conversion)
        conversion_buttons.append(self.stop_btn)
        
        conversion_group.add(conversion_buttons)
        
        # Barra de progreso
        progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        progress_box.set_margin_top(8)
        
        self.progress_label = Gtk.Label(label="Listo")
        self.progress_label.add_css_class("dim-label")
        self.progress_label.set_width_chars(12)
        progress_box.append(self.progress_label)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_hexpand(True)
        progress_box.append(self.progress_bar)
        
        conversion_group.add(progress_box)
        
        # === SECCIÓN: REGISTRO (compacto) ===
        log_expander = Adw.ExpanderRow()
        log_expander.set_title("Registro")
        log_expander.set_subtitle("Ver actividad")
        log_expander.set_expanded(False)
        
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_min_content_height(80)
        log_scroll.set_max_content_height(100)
        
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_view.set_monospace(True)
        self.log_view.set_margin_top(5)
        self.log_view.set_margin_bottom(5)
        self.log_view.set_margin_start(8)
        self.log_view.set_margin_end(8)
        self.log_buffer = self.log_view.get_buffer()
        
        log_scroll.set_child(self.log_view)
        log_expander.add_row(Adw.ActionRow())
        
        # Añadir al grupo de configuración para ahorrar espacio
        config_group.add(log_expander)
        
        # Guardar referencia para el log
        self.log_expander = log_expander
    
    def create_placeholder(self) -> Gtk.Widget:
        """Crea el placeholder compacto para la lista vacía."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_halign(Gtk.Align.CENTER)
        
        icon = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        icon.set_pixel_size(32)
        icon.add_css_class("dim-label")
        box.append(icon)
        
        label = Gtk.Label(label="No hay archivos – Añade archivos para comenzar")
        label.add_css_class("dim-label")
        box.append(label)
        
        return box
    
    def on_add_files(self, button):
        """Abre el diálogo para añadir archivos."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar archivos de audio")
        
        # Filtro de archivos de audio
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Archivos de audio")
        for fmt in SUPPORTED_FORMATS:
            filter_audio.add_pattern(f"*.{fmt}")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_audio)
        dialog.set_filters(filters)
        
        dialog.open_multiple(self, None, self.on_files_selected)
    
    def on_files_selected(self, dialog, result):
        """Callback cuando se seleccionan archivos."""
        try:
            files = dialog.open_multiple_finish(result)
            for gfile in files:
                path = gfile.get_path()
                if path and self.is_valid_audio(path):
                    self.add_file(path)
        except GLib.Error:
            pass
    
    def on_add_folder(self, button):
        """Abre el diálogo para añadir carpeta."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar carpeta")
        dialog.select_folder(self, None, self.on_folder_selected)
    
    def on_folder_selected(self, dialog, result):
        """Callback cuando se selecciona una carpeta."""
        try:
            folder = dialog.select_folder_finish(result)
            path = folder.get_path()
            if path:
                count = 0
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if any(file.lower().endswith(f".{fmt}") for fmt in SUPPORTED_FORMATS):
                            full_path = os.path.join(root, file)
                            if self.is_valid_audio(full_path):
                                self.add_file(full_path)
                                count += 1
                self.log(f"Se añadieron {count} archivos de la carpeta")
        except GLib.Error:
            pass
    
    def add_file(self, path: str):
        """Añade un archivo a la lista."""
        # Verificar si ya existe
        for item in self.files:
            if item.path == path:
                return
        
        name = os.path.basename(path)
        file_item = FileItem(path, name)
        self.files.append(file_item)
        self.list_store.append(file_item)
        
        # Crear fila visual
        row = Adw.ActionRow()
        row.set_title(name)
        row.set_subtitle(path)
        row.set_icon_name("audio-x-generic-symbolic")
        
        # Badge de estado
        status_label = Gtk.Label(label="En espera")
        status_label.add_css_class("dim-label")
        row.add_suffix(status_label)
        
        # Guardar referencia
        row.file_item = file_item
        row.status_label = status_label
        
        self.files_listbox.append(row)
    
    def is_valid_audio(self, path: str) -> bool:
        """Verifica si el archivo es un audio válido."""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_streams', '-select_streams', 'a', path],
                capture_output=True, text=True, timeout=10
            )
            return bool(result.stdout)
        except Exception:
            return False
    
    def on_remove_files(self, button):
        """Elimina los archivos seleccionados."""
        rows_to_remove = []
        row = self.files_listbox.get_first_child()
        while row:
            if row.is_selected():
                rows_to_remove.append(row)
            row = row.get_next_sibling()
        
        for row in rows_to_remove:
            if hasattr(row, 'file_item'):
                self.files.remove(row.file_item)
            self.files_listbox.remove(row)
    
    def on_clear_files(self, button):
        """Limpia la lista de archivos."""
        self.files.clear()
        while True:
            row = self.files_listbox.get_first_child()
            if row is None:
                break
            self.files_listbox.remove(row)
    
    def on_select_output(self, button):
        """Selecciona la carpeta de salida."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar carpeta de salida")
        dialog.select_folder(self, None, self.on_output_selected)
    
    def on_output_selected(self, dialog, result):
        """Callback cuando se selecciona la carpeta de salida."""
        try:
            folder = dialog.select_folder_finish(result)
            self.output_folder = folder.get_path()
            self.output_label.set_label(os.path.basename(self.output_folder))
            self.output_label.remove_css_class("dim-label")
        except GLib.Error:
            pass
    
    def on_start_conversion(self, button):
        """Inicia el proceso de conversión."""
        if not self.files:
            self.show_error("No hay archivos", "Añade archivos de audio para convertir")
            return
        
        if not self.output_folder:
            self.show_error("Sin carpeta de salida", "Selecciona una carpeta donde guardar los archivos")
            return
        
        self.is_converting = True
        self.convert_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.completed_count = 0
        self.total_count = len(self.files)
        
        # Obtener configuración
        format_idx = self.format_row.get_selected()
        output_format = SUPPORTED_FORMATS[format_idx]
        
        bitrate_idx = self.bitrate_row.get_selected()
        bitrate = BITRATE_OPTIONS[bitrate_idx]
        
        overwrite = self.overwrite_row.get_active()
        
        self.log(f"Iniciando conversión de {self.total_count} archivos a {output_format} ({bitrate})")
        
        # Iniciar conversiones en hilos
        for file_item in self.files:
            if not self.is_converting:
                break
            
            thread = threading.Thread(
                target=self.convert_file,
                args=(file_item, output_format, bitrate, overwrite)
            )
            self.conversion_threads.append(thread)
            thread.start()
    
    def convert_file(self, file_item: FileItem, output_format: str, bitrate: str, overwrite: bool):
        """Convierte un archivo en un hilo separado."""
        input_path = file_item.path
        output_name = os.path.splitext(file_item.name)[0] + f".{output_format}"
        output_path = os.path.join(self.output_folder, output_name)
        
        # Verificar si existe
        if os.path.exists(output_path) and not overwrite:
            GLib.idle_add(self.update_file_status, file_item, "Omitido", 100)
            GLib.idle_add(self.file_completed)
            return
        
        GLib.idle_add(self.update_file_status, file_item, "Convirtiendo...", 0)
        
        try:
            # Ejecutar FFmpeg
            cmd = [
                'ffmpeg', '-i', input_path,
                '-b:a', bitrate,
                '-y' if overwrite else '-n',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                GLib.idle_add(self.update_file_status, file_item, "✓ Completado", 100)
                GLib.idle_add(self.log, f"✓ {file_item.name} convertido")
            else:
                GLib.idle_add(self.update_file_status, file_item, "✗ Error", 0)
                GLib.idle_add(self.log, f"✗ Error en {file_item.name}")
                logging.error(f"Error convirtiendo {input_path}: {result.stderr}")
        
        except Exception as e:
            GLib.idle_add(self.update_file_status, file_item, "✗ Error", 0)
            GLib.idle_add(self.log, f"✗ Error en {file_item.name}: {str(e)}")
            logging.error(f"Excepción convirtiendo {input_path}: {e}")
        
        finally:
            GLib.idle_add(self.file_completed)
    
    def update_file_status(self, file_item: FileItem, status: str, progress: float):
        """Actualiza el estado visual de un archivo."""
        row = self.files_listbox.get_first_child()
        while row:
            if hasattr(row, 'file_item') and row.file_item == file_item:
                if hasattr(row, 'status_label'):
                    row.status_label.set_label(status)
                    if "✓" in status:
                        row.status_label.remove_css_class("dim-label")
                        row.status_label.add_css_class("success")
                    elif "✗" in status:
                        row.status_label.remove_css_class("dim-label")
                        row.status_label.add_css_class("error")
                break
            row = row.get_next_sibling()
    
    def file_completed(self):
        """Callback cuando un archivo termina de convertirse."""
        self.completed_count += 1
        progress = self.completed_count / self.total_count
        self.progress_bar.set_fraction(progress)
        self.progress_label.set_label(f"Progreso: {self.completed_count}/{self.total_count}")
        
        if self.completed_count >= self.total_count:
            self.conversion_finished()
    
    def conversion_finished(self):
        """Callback cuando toda la conversión termina."""
        self.is_converting = False
        self.convert_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.progress_label.set_label("¡Conversión completada!")
        self.log("✓ Conversión completada")
        
        # Guardar log
        self.save_conversion_log()
        
        # Mostrar notificación
        toast = Adw.Toast(title="¡Conversión completada!")
        toast.set_timeout(3)
        # Note: Would need toast overlay for this
    
    def on_stop_conversion(self, button):
        """Detiene la conversión."""
        self.is_converting = False
        self.convert_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.progress_label.set_label("Conversión detenida")
        self.log("Conversión detenida por el usuario")
    
    def log(self, message: str):
        """Añade un mensaje al registro."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = f"[{timestamp}] {message}\n"
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, text)
        
        # Scroll al final
        mark = self.log_buffer.get_insert()
        self.log_view.scroll_to_mark(mark, 0, True, 0, 1)
    
    def save_conversion_log(self):
        """Guarda el log de conversión."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "files_count": self.total_count,
            "output_folder": self.output_folder,
            "format": SUPPORTED_FORMATS[self.format_row.get_selected()],
            "bitrate": BITRATE_OPTIONS[self.bitrate_row.get_selected()]
        }
        try:
            with open(CONVERSION_LOG, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logging.error(f"Error guardando log: {e}")
    
    def show_error(self, title: str, message: str):
        """Muestra un diálogo de error."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=title,
            body=message
        )
        dialog.add_response("ok", "Aceptar")
        dialog.set_default_response("ok")
        dialog.present()


class SonifyLabApp(Adw.Application):
    """Aplicación principal de SonifyLab."""
    
    def __init__(self):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.window = None
    
    def do_activate(self):
        """Activa la aplicación."""
        if not self.window:
            self.window = SonifyLabWindow(self)
        self.window.present()
    
    def do_startup(self):
        """Inicializa la aplicación."""
        Adw.Application.do_startup(self)
        
        # Acción: Acerca de
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
        
        # Acción: Salir
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])
    
    def on_about(self, action, param):
        """Muestra el diálogo Acerca de."""
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name=__app_name__,
            application_icon="audio-x-generic",
            developer_name=__author__,
            version=__version__,
            copyright="© 2024 Discaury Salas",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/discodiski/SonifyLab",
            issue_url="https://github.com/discodiski/SonifyLab/issues",
            developers=[__author__],
            comments="Herramienta profesional de conversión de audio por lotes.\n\nUtiliza FFmpeg para conversiones de alta calidad."
        )
        about.present()


def main():
    """Punto de entrada principal."""
    app = SonifyLabApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
