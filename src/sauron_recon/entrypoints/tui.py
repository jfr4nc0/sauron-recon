from __future__ import annotations

import curses
import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

from .cli import main as cli_main


_FIELDS = (
    ("Operación", "operation", "rent"),
    ("Tipo de inmueble", "property_type", "local"),
    ("Zonas (separadas por coma)", "zones", "Caballito"),
    ("Superficie mínima m2", "min_area_m2", ""),
    ("Superficie máxima m2", "max_area_m2", ""),
    ("Fuentes (separadas por coma)", "sources", "zonaprop,argenprop"),
)


class SauronTUI:
    def __init__(self, stdscr) -> None:
        self.stdscr = stdscr
        self.values = {key: default for _, key, default in _FIELDS}
        self.live = False
        self.scrape_details = False
        self.status = "Listo. Enter para editar; F2 buscar; F10 salir."
        self.output: list[str] = []
        self.selected = 0
        self.editing = False

    def run(self) -> None:
        curses.curs_set(1)
        self.stdscr.keypad(True)
        self.stdscr.timeout(-1)
        while True:
            self.draw()
            key = self.stdscr.get_wch()
            if self.editing:
                if self.handle_edit(key):
                    self.editing = False
                continue
            if key in (curses.KEY_F10, "q", "Q"):
                return
            if key in (curses.KEY_UP, "k"):
                self.selected = max(0, self.selected - 1)
            elif key in (curses.KEY_DOWN, "j"):
                self.selected = min(len(_FIELDS) - 1, self.selected + 1)
            elif key in (curses.KEY_ENTER, "\n", "\r"):
                self.editing = True
            elif key == curses.KEY_F2:
                self.search()
            elif key in ("l", "L"):
                self.live = not self.live
                self.status = f"Modo {'live' if self.live else 'offline'} seleccionado."
            elif key in ("d", "D"):
                self.scrape_details = not self.scrape_details
                self.status = f"Detalle {'activado' if self.scrape_details else 'desactivado'}."
            elif key in ("c", "C"):
                self.output = []
                self.status = "Salida limpiada."

    def draw(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(0, 2, "SAURON RECON", curses.A_BOLD)
        self.stdscr.addstr(1, 2, "TUI de reconocimiento inmobiliario")
        self.stdscr.addstr(3, 2, "Criterios de búsqueda", curses.A_UNDERLINE)
        row = 5
        for index, (label, key, _) in enumerate(_FIELDS):
            marker = ">" if index == self.selected else " "
            value = self.values[key]
            text = f"{marker} {label}: {value}"
            self.stdscr.addnstr(row + index, 2, text, max(1, width - 4))
        options_row = row + len(_FIELDS) + 2
        self.stdscr.addstr(options_row, 2, f"[L]ive: {'sí' if self.live else 'no'}   [D]etalles: {'sí' if self.scrape_details else 'no'}")
        self.stdscr.addstr(options_row + 1, 2, "F2 buscar   F10/Q salir   C limpiar salida")
        separator = options_row + 3
        self.stdscr.addnstr(separator, 2, "─" * max(1, width - 4), max(1, width - 4))
        self.stdscr.addstr(separator + 1, 2, self.status[: max(1, width - 4)])
        output_start = separator + 3
        for offset, line in enumerate(self.output[-max(1, height - output_start - 1):]):
            self.stdscr.addnstr(output_start + offset, 2, line, max(1, width - 4))
        self.stdscr.refresh()

    def handle_edit(self, key) -> bool:
        label, field, _ = _FIELDS[self.selected]
        current = self.values[field]
        if key in (curses.KEY_ENTER, "\n", "\r"):
            self.values[field] = current.strip()
            self.status = f"{label} actualizado."
            return True
        if key == "\x1b":
            return True
        if key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            self.values[field] = current[:-1]
            return False
        if isinstance(key, str) and key.isprintable():
            self.values[field] += key
        return False

    def search(self) -> None:
        criteria = {
            "operation": self.values["operation"] or "rent",
            "property_type": self.values["property_type"] or "local",
            "zones": [zone.strip() for zone in self.values["zones"].split(",") if zone.strip()],
        }
        for key in ("min_area_m2", "max_area_m2"):
            if self.values[key].strip():
                criteria[key] = self.values[key].strip()
        args = ["search", "--criteria", json.dumps(criteria, ensure_ascii=False)]
        if self.live:
            args.extend(["--live", "--sources", self.values["sources"] or "zonaprop,argenprop"])
        else:
            args.append("--dry-run")
        if self.scrape_details:
            args.append("--scrape-details")
        buffer = io.StringIO()
        self.status = "Ejecutando búsqueda..."
        self.draw()
        try:
            with redirect_stdout(buffer):
                code = cli_main(args)
            self.output = buffer.getvalue().splitlines()[-18:]
            self.status = "Búsqueda finalizada." if code == 0 else f"La búsqueda terminó con código {code}."
        except Exception as exc:
            self.output = [f"Error: {type(exc).__name__}: {exc}"]
            self.status = "La búsqueda falló; revisá la salida."


def main() -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("sauron requiere una terminal interactiva; use `sauron-recon` para el CLI.", file=sys.stderr)
        return 2
    curses.wrapper(lambda stdscr: SauronTUI(stdscr).run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
