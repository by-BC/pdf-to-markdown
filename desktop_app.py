"""Native Windows interface for the local PDF to Markdown converter."""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import ConversionResult, convert_pdf


BG = "#F5F6FA"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F8FAFC"
INK = "#1E293B"
MUTED = "#64748B"
BORDER = "#DCE1EB"
BLUE = "#4F46E5"
BLUE_DARK = "#3730A3"
BLUE_LIGHT = "#EEF2FF"
ERROR = "#B42318"

OCR_MODES = {
    "Automático — recomendado": "auto",
    "Forçar OCR em todas as páginas": "force",
    "Sem OCR — apenas texto selecionável": "off",
}


def asset_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "assets" / name


class DesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF para Markdown")
        self.geometry("1100x720")
        self.minsize(900, 620)
        self.configure(bg=BG)
        self.files: list[Path] = []
        self.results: dict[Path, ConversionResult] = {}
        self.events: queue.Queue = queue.Queue()
        self.busy = False
        self.output_dir = tk.StringVar(value=str(Path.home() / "Documents" / "Markdown"))
        self.ocr_choice = tk.StringVar(value="Automático — recomendado")
        self.status = tk.StringVar(value="Adicione PDFs para começar.")
        self._set_icon()
        self._build()
        self.after(100, self._poll)

    def _set_icon(self):
        try:
            self.iconbitmap(default=str(asset_path("app.ico")))
            self._icon_image = tk.PhotoImage(file=str(asset_path("app.png"))).subsample(8, 8)
            self.iconphoto(True, self._icon_image)
        except (OSError, tk.TclError):
            self._icon_image = None

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Files.Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=INK, rowheight=38, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Files.Treeview.Heading", background=SURFACE_ALT, foreground=MUTED, font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("Files.Treeview", background=[("selected", BLUE_LIGHT)], foreground=[("selected", INK)])
        style.configure("Blue.Horizontal.TProgressbar", troughcolor="#E5E7EB", background=BLUE, borderwidth=0)
        style.configure("Ocr.TCombobox", padding=6, fieldbackground=SURFACE_ALT, background=SURFACE, foreground=INK)

        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True, padx=26, pady=19)

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x")
        if self._icon_image:
            tk.Label(header, image=self._icon_image, bg=BG).pack(side="left", padx=(0, 9))
        tk.Label(header, text="PDF para Markdown", bg=BG, fg=INK, font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(header, text="Arquivos processados neste computador", bg=BLUE_LIGHT, fg=BLUE_DARK, padx=12, pady=7, font=("Segoe UI", 9)).pack(side="right")

        intro = tk.Frame(root, bg=BG)
        intro.pack(fill="x", pady=(16, 14))
        tk.Label(intro, text="Converta seus PDFs em Markdown", bg=BG, fg=INK, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(intro, text="Adicione arquivos, escolha a pasta e clique em Converter PDFs.", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        self._build_settings(root)

        # Pack the action bar before the resizable content so it always stays visible.
        footer = tk.Frame(root, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=18, pady=12)
        footer.pack(side="bottom", fill="x", pady=(16, 0))
        self.convert_button = self._button(footer, "Converter PDFs", self._start, primary=True)
        self.convert_button.pack(side="right", padx=(18, 0))
        self.convert_button.configure(state="disabled")
        footer_info = tk.Frame(footer, bg=SURFACE)
        footer_info.pack(side="left", fill="both", expand=True)
        tk.Label(footer_info, textvariable=self.status, bg=SURFACE, fg=INK, font=("Segoe UI", 10)).pack(anchor="w")
        self.progress = ttk.Progressbar(footer_info, mode="determinate", style="Blue.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(8, 0))

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1, uniform="panel")
        body.grid_columnconfigure(1, weight=1, uniform="panel")
        body.grid_rowconfigure(0, weight=1)

        left = self._card(body)
        right = self._card(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._build_files(left)
        self._build_preview(right)

    def _card(self, parent):
        return tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=19, pady=17)

    def _button(self, parent, label, command, *, primary=False):
        return tk.Button(
            parent, text=label, command=command,
            bg=BLUE if primary else BLUE_LIGHT,
            fg=SURFACE if primary else BLUE_DARK,
            activebackground=BLUE_DARK if primary else "#E0E7FF",
            activeforeground=SURFACE if primary else BLUE_DARK,
            disabledforeground="#8B95A7", relief="flat", bd=0,
            padx=16, pady=9, font=("Segoe UI", 10, "bold"), cursor="hand2",
            takefocus=True,
        )

    def _build_settings(self, root):
        settings = tk.Frame(root, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=18, pady=12)
        settings.pack(fill="x", pady=(0, 14))
        settings.grid_columnconfigure(0, weight=3, uniform="settings")
        settings.grid_columnconfigure(1, weight=2, uniform="settings")
        tk.Label(settings, text="PASTA DE DESTINO DOS ARQUIVOS .MD", bg=SURFACE, fg=MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        tk.Label(settings, text="OCR", bg=SURFACE, fg=MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=1, sticky="w", padx=(18, 0), pady=(0, 6))
        folder = tk.Frame(settings, bg=SURFACE)
        folder.grid(row=1, column=0, sticky="ew")
        self.folder_entry = tk.Entry(folder, textvariable=self.output_dir, fg=INK, bg=SURFACE_ALT, relief="flat", highlightthickness=1, highlightbackground=BORDER, highlightcolor=BLUE, font=("Segoe UI", 9))
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.folder_button = self._button(folder, "Escolher…", self._choose_folder)
        self.folder_button.pack(side="left", padx=(7, 0))
        self.ocr_selector = ttk.Combobox(settings, textvariable=self.ocr_choice, values=tuple(OCR_MODES), state="readonly", style="Ocr.TCombobox", font=("Segoe UI", 9))
        self.ocr_selector.grid(row=1, column=1, sticky="ew", padx=(18, 0))

    def _build_files(self, parent):
        heading = tk.Frame(parent, bg=SURFACE)
        heading.pack(fill="x")
        tk.Label(heading, text="Arquivos PDF", bg=SURFACE, fg=INK, font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(parent, text="Adicione os documentos que deseja converter.", bg=SURFACE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(7, 11))

        buttons = tk.Frame(parent, bg=SURFACE)
        buttons.pack(fill="x", pady=(0, 12))
        self.add_button = self._button(buttons, "+  Adicionar PDFs", self._add_files)
        self.add_button.pack(side="left")
        self.remove_button = self._button(buttons, "Remover", self._remove_selected)
        self.remove_button.pack(side="right")
        self.remove_button.configure(state="disabled")

        tree_frame = tk.Frame(parent, bg=SURFACE)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("status",), show="tree headings", style="Files.Treeview", selectmode="extended")
        self.tree.heading("#0", text="Arquivo", anchor="w")
        self.tree.heading("status", text="Status", anchor="center")
        self.tree.column("#0", width=260, stretch=True)
        self.tree.column("status", width=88, stretch=False, anchor="center")
        self.tree.tag_configure("error", foreground=ERROR)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._show_selected)

    def _build_preview(self, parent):
        heading = tk.Frame(parent, bg=SURFACE)
        heading.pack(fill="x")
        tk.Label(heading, text="Prévia do Markdown", bg=SURFACE, fg=INK, font=("Segoe UI", 13, "bold")).pack(side="left")
        self.copy_button = self._button(heading, "Copiar", self._copy)
        self.copy_button.pack(side="right")
        self.copy_button.configure(state="disabled")

        self.preview = tk.Text(parent, wrap="word", bg=SURFACE_ALT, fg=INK, relief="flat", padx=13, pady=12, font=("Consolas", 9), state="disabled", highlightthickness=1, highlightbackground=BORDER)
        self.preview.pack(fill="both", expand=True, pady=(8, 0))
        self._set_preview("Depois da conversão, selecione um PDF na lista para ver o Markdown aqui.")
        self.open_button = self._button(parent, "Abrir pasta de destino", self._open_folder)
        self.open_button.pack(anchor="e", pady=(9, 0))

    def _add_files(self):
        paths = filedialog.askopenfilenames(parent=self, title="Selecionar PDFs", filetypes=[("Arquivos PDF", "*.pdf")])
        known = {str(path).casefold() for path in self.files}
        for value in paths:
            path = Path(value)
            if str(path).casefold() not in known:
                self.files.append(path)
                known.add(str(path).casefold())
        self._render_files()

    def _remove_selected(self):
        selected = {self.files[int(item)] for item in self.tree.selection()}
        self.tree.selection_remove(self.tree.selection())
        self.files = [path for path in self.files if path not in selected]
        for path in selected:
            self.results.pop(path, None)
        self._render_files()
        self._show_selected()

    def _choose_folder(self):
        folder = filedialog.askdirectory(parent=self, title="Escolher pasta dos arquivos Markdown", initialdir=str(Path.home()))
        if folder:
            self.output_dir.set(folder)

    def _render_files(self):
        selected_paths = {self.files[int(item)] for item in self.tree.selection() if int(item) < len(self.files)}
        self.tree.delete(*self.tree.get_children())
        for index, path in enumerate(self.files):
            result = self.results.get(path)
            status = "Erro" if result and result.error else "OCR" if result and result.ocr_pages else "Concluído" if result else "Pendente"
            tags = ("error",) if result and result.error else ()
            self.tree.insert("", "end", iid=str(index), text=path.name, values=(status,), tags=tags)
            if path in selected_paths:
                self.tree.selection_add(str(index))
        count = len(self.files)
        if not self.busy:
            self.convert_button.configure(state="normal" if count else "disabled", text=f"Converter {count} PDF{'s' if count != 1 else ''}  →" if count else "Converter PDFs  →")
            self.status.set(f"{count} PDF{'s' if count != 1 else ''} pronto{'s' if count != 1 else ''} para converter." if count else "Adicione PDFs para começar.")
        self.remove_button.configure(state="normal" if self.tree.selection() and not self.busy else "disabled")

    def _set_preview(self, content: str):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", content)
        self.preview.configure(state="disabled")

    def _show_selected(self, _event=None):
        selection = self.tree.selection()
        self.remove_button.configure(state="normal" if selection and not self.busy else "disabled")
        if not selection:
            self.copy_button.configure(state="disabled", text="Copiar")
            self._set_preview("Depois da conversão, selecione um PDF na lista para ver o Markdown aqui.")
            return
        result = self.results.get(self.files[int(selection[0])])
        if result:
            self.copy_button.configure(state="normal", text="Copiar erro" if result.error else "Copiar")
            self._set_preview(result.error or result.markdown or result.warning or "Markdown vazio.")
            if result.warning and result.markdown:
                self.status.set(result.warning)
        else:
            self.copy_button.configure(state="disabled", text="Copiar")
            self._set_preview("Este PDF está pronto. Clique em “Converter PDFs” na barra inferior.")

    def _start(self):
        if self.busy or not self.files:
            return
        folder_name = self.output_dir.get().strip()
        if not folder_name:
            messagebox.showerror("Pasta inválida", "Escolha uma pasta de destino.", parent=self)
            return
        folder = Path(folder_name)
        self.busy = True
        self.results.clear()
        self._render_files()
        self.progress.configure(maximum=len(self.files), value=0)
        for button in (self.add_button, self.remove_button, self.folder_button, self.convert_button):
            button.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        self.ocr_selector.configure(state="disabled")
        self.convert_button.configure(text="Convertendo…")
        self.status.set(f"Convertendo 0 de {len(self.files)} PDFs…")
        threading.Thread(target=self._worker, args=(list(self.files), folder, OCR_MODES[self.ocr_choice.get()]), daemon=True).start()

    def _worker(self, files: list[Path], folder: Path, ocr_mode: str):
        for index, path in enumerate(files, start=1):
            self.events.put(("result", convert_pdf(path, folder, ocr_mode=ocr_mode), index))
        self.events.put(("done", None, len(files)))

    def _poll(self):
        try:
            while True:
                kind, result, count = self.events.get_nowait()
                if kind == "result":
                    self.results[result.source] = result
                    self.progress.configure(value=count)
                    self._render_files()
                    if not self.tree.selection():
                        self.tree.selection_set(str(self.files.index(result.source)))
                    self._show_selected()
                    self.status.set(f"Convertendo {count} de {len(self.files)} PDFs…")
                else:
                    self.busy = False
                    for button in (self.add_button, self.folder_button):
                        button.configure(state="normal")
                    self.folder_entry.configure(state="normal")
                    self.ocr_selector.configure(state="readonly")
                    self._render_files()
                    successes = sum(item.output is not None for item in self.results.values())
                    ocr_pages = sum(item.ocr_pages for item in self.results.values())
                    self.status.set(f"Concluído: {successes} de {count} PDFs. OCR em {ocr_pages} página(s). Arquivos salvos na pasta escolhida.")
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _copy(self):
        selection = self.tree.selection()
        if selection:
            result = self.results.get(self.files[int(selection[0])])
            if result:
                self.clipboard_clear()
                self.clipboard_append(result.error or result.markdown)
                self.status.set("Mensagem de erro copiada." if result.error else "Markdown copiado para a área de transferência.")

    def _open_folder(self):
        folder = Path(self.output_dir.get().strip())
        if folder.is_dir():
            os.startfile(folder)
        else:
            messagebox.showinfo("Pasta ainda não criada", "Converta um PDF para criar a pasta de destino.", parent=self)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        from packaged_smoke import run

        raise SystemExit(run(Path(sys.argv[2])))
    DesktopApp().mainloop()

