"""Native Windows GUI for converting selected PDFs to Markdown."""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import ConversionResult, convert_pdf


BG = "#F3F8F6"
WHITE = "#FFFFFF"
INK = "#173D39"
MUTED = "#68817C"
TEAL = "#0D9488"
BORDER = "#D9E8E3"


class DesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF para Markdown")
        self.geometry("1060x690")
        self.minsize(780, 540)
        self.configure(bg=BG)
        self.files: list[Path] = []
        self.results: dict[Path, ConversionResult] = {}
        self.events: queue.Queue = queue.Queue()
        self.busy = False
        self.output_dir = tk.StringVar(value=str(Path.home() / "Documents" / "Markdown"))
        self.status = tk.StringVar(value="Adicione PDFs para começar.")
        self._build()
        self.after(100, self._poll)

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Files.Treeview", background=WHITE, fieldbackground=WHITE, foreground=INK, rowheight=42, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Files.Treeview.Heading", background="#EAF5F1", foreground=INK, font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("Files.Treeview", background=[("selected", "#DCF2EC")], foreground=[("selected", INK)])
        style.configure("Teal.Horizontal.TProgressbar", troughcolor="#E0EEE9", background=TEAL, borderwidth=0)

        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True, padx=32, pady=24)
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x")
        tk.Label(header, text="pdf  →  md", bg=BG, fg=TEAL, font=("Segoe UI", 17, "bold")).pack(side="left")
        tk.Label(header, text="CONVERSÃO LOCAL", bg="#E5F4EF", fg="#0A746B", padx=13, pady=7, font=("Segoe UI", 9, "bold")).pack(side="right")

        tk.Label(root, text="Seus PDFs, em Markdown.", bg=BG, fg=INK, font=("Segoe UI", 27, "bold")).pack(anchor="w", pady=(36, 6))
        tk.Label(root, text="Selecione os documentos, escolha onde salvar e acompanhe a conversão.", bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 26))

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1, uniform="panel")
        body.grid_columnconfigure(1, weight=1, uniform="panel")
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=WHITE, highlightbackground=BORDER, highlightthickness=1, padx=20, pady=18)
        right = tk.Frame(body, bg=WHITE, highlightbackground=BORDER, highlightthickness=1, padx=20, pady=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(left, text="01   Arquivos PDF", bg=WHITE, fg=INK, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(left, text="Adicione um ou mais arquivos", bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 16))
        buttons = tk.Frame(left, bg=WHITE)
        buttons.pack(fill="x", pady=(0, 14))
        self.add_button = self._button(buttons, "+  Adicionar PDFs", self._add_files, primary=True)
        self.add_button.pack(side="left")
        self.remove_button = self._button(buttons, "Remover selecionado", self._remove_selected)
        self.remove_button.pack(side="right")

        tree_frame = tk.Frame(left, bg=WHITE)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("status",), show="tree headings", style="Files.Treeview", selectmode="extended")
        self.tree.heading("#0", text="Arquivo")
        self.tree.heading("status", text="Status")
        self.tree.column("#0", width=260, stretch=True)
        self.tree.column("status", width=92, stretch=False, anchor="center")
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._show_selected)

        tk.Label(left, text="PASTA DE DESTINO", bg=WHITE, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(19, 7))
        folder = tk.Frame(left, bg=WHITE)
        folder.pack(fill="x")
        self.folder_entry = tk.Entry(folder, textvariable=self.output_dir, fg=INK, bg="#F7FBF9", relief="flat", highlightthickness=1, highlightbackground=BORDER, font=("Segoe UI", 9))
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=9)
        self.folder_button = self._button(folder, "Escolher", self._choose_folder)
        self.folder_button.pack(side="left", padx=(8, 0))
        self.convert_button = self._button(left, "Converter PDFs  →", self._start, primary=True)
        self.convert_button.pack(fill="x", pady=(18, 0))

        tk.Label(right, text="02   Resultado", bg=WHITE, fg=INK, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(right, text="Selecione um arquivo convertido para visualizar", bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 17))
        self.preview = tk.Text(right, wrap="word", bg="#F7FBF9", fg=INK, relief="flat", padx=16, pady=15, font=("Consolas", 10), state="disabled", highlightthickness=1, highlightbackground=BORDER)
        self.preview.pack(fill="both", expand=True)
        self._set_preview("O Markdown convertido aparecerá aqui.\n\nSe o PDF contiver apenas imagens, pode ser necessário usar OCR.")
        bottom = tk.Frame(right, bg=WHITE)
        bottom.pack(fill="x", pady=(15, 0))
        self.copy_button = self._button(bottom, "Copiar Markdown", self._copy)
        self.copy_button.pack(side="left")
        self.open_button = self._button(bottom, "Abrir pasta", self._open_folder)
        self.open_button.pack(side="right")

        footer = tk.Frame(root, bg=BG)
        footer.pack(fill="x", pady=(20, 0))
        self.progress = ttk.Progressbar(footer, mode="determinate", style="Teal.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 10))
        tk.Label(footer, textvariable=self.status, bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")

    def _button(self, parent, label, command, primary=False):
        return tk.Button(parent, text=label, command=command, bg=TEAL if primary else "#EAF5F1", fg=WHITE if primary else "#0A746B", activebackground="#087A70" if primary else "#D8EEE7", activeforeground=WHITE if primary else INK, relief="flat", bd=0, padx=16, pady=10, font=("Segoe UI", 9, "bold"), cursor="hand2")

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
        self.files = [path for path in self.files if path not in selected]
        for path in selected:
            self.results.pop(path, None)
        self._render_files()

    def _choose_folder(self):
        folder = filedialog.askdirectory(parent=self, title="Escolher pasta de destino", initialdir=str(Path.home()))
        if folder:
            self.output_dir.set(folder)

    def _render_files(self):
        self.tree.delete(*self.tree.get_children())
        for index, path in enumerate(self.files):
            result = self.results.get(path)
            status = "Erro" if result and result.error else "Concluído" if result else "Pendente"
            self.tree.insert("", "end", iid=str(index), text=path.name, values=(status,))
        self.status.set(f"{len(self.files)} PDF(s) selecionado(s)." if self.files else "Adicione PDFs para começar.")

    def _set_preview(self, content: str):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", content)
        self.preview.configure(state="disabled")

    def _show_selected(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        result = self.results.get(self.files[int(selection[0])])
        if result:
            self._set_preview(result.error or result.markdown or result.warning or "Markdown vazio.")
        else:
            self._set_preview("Arquivo ainda não convertido.")

    def _start(self):
        if self.busy:
            return
        if not self.files:
            messagebox.showinfo("Nenhum PDF", "Adicione pelo menos um PDF para converter.", parent=self)
            return
        folder = Path(self.output_dir.get().strip())
        if not self.output_dir.get().strip():
            messagebox.showerror("Pasta inválida", "Escolha uma pasta de destino.", parent=self)
            return
        self.busy = True
        self.results.clear()
        self._render_files()
        self.progress.configure(maximum=len(self.files), value=0)
        for button in (self.add_button, self.remove_button, self.folder_button, self.convert_button):
            button.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        self.status.set("Convertendo PDFs...")
        threading.Thread(target=self._worker, args=(list(self.files), folder), daemon=True).start()

    def _worker(self, files: list[Path], folder: Path):
        for index, path in enumerate(files, start=1):
            self.events.put(("result", convert_pdf(path, folder), index))
        self.events.put(("done", None, len(files)))

    def _poll(self):
        try:
            while True:
                kind, result, count = self.events.get_nowait()
                if kind == "result":
                    self.results[result.source] = result
                    self.progress.configure(value=count)
                    self._render_files()
                    self.status.set(f"Convertendo: {count} de {len(self.files)}...")
                    self._show_selected()
                else:
                    self.busy = False
                    for button in (self.add_button, self.remove_button, self.folder_button, self.convert_button):
                        button.configure(state="normal")
                    self.folder_entry.configure(state="normal")
                    successes = sum(result.output is not None for result in self.results.values())
                    self.status.set(f"Concluído: {successes} de {count} PDF(s) convertido(s).")
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _copy(self):
        selection = self.tree.selection()
        if selection:
            result = self.results.get(self.files[int(selection[0])])
            if result and result.output:
                self.clipboard_clear()
                self.clipboard_append(result.markdown)
                self.status.set("Markdown copiado.")

    def _open_folder(self):
        folder = Path(self.output_dir.get().strip())
        if folder.is_dir():
            os.startfile(folder)
        else:
            messagebox.showinfo("Pasta ainda não criada", "Converta um PDF para criar a pasta de destino.", parent=self)


if __name__ == "__main__":
    DesktopApp().mainloop()

