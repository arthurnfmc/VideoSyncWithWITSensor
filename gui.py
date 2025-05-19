import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
import cv2
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

import actionstart as action_start
import sensordataIO as sensor_data

class VideoGraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualizador de Vídeo e Gráfico")

        self.video_path = None
        self.data_path = None
        self.cap = None
        self.data = None
        self.selected_columns = []

        self.running = False
        self.paused = False

        self.video_start = 0
        self.video_duration = None
        self.data_start = 0
        self.data_duration = None

        self.last_update_time = time.time()
        self.frame_count = 0

        self.graph_canvas = None
        
        self.fps = None

        # Campos para entradas nos frames
        self.entry_video_start = None
        self.entry_video_duration = None
        self.entry_data_start = None
        self.entry_data_duration = None

        self.container = tk.Frame(self.root)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.frames = {}
        for F in (VideoCutFrame, DataCutFrame, MainViewFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(VideoCutFrame)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Vídeo MP4", "*.mp4"),
                                                      ("Vídeo AVI", "*.avi"),
                                                      ("Todos os arquivos", "*.*")])
        if path:
            self.video_path = path
            self.cap = cv2.VideoCapture(self.video_path)
            ret, frame = self.cap.read()
            if ret:
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.cap.get(cv2.CAP_PROP_FPS)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (400, 300))  # Redimensiona o frame para caber na tela
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.frames[VideoCutFrame].video_preview.imgtk = imgtk
                self.frames[VideoCutFrame].video_preview.configure(image=imgtk, width=400, height=300)
                self.frames[VideoCutFrame].scale.config(to=self.total_frames - 1)
                self.frames[VideoCutFrame].scale.set(0)
                self.update_video_time_label(0)

    def update_video_preview_at_frame(self, frame_index):
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (400, 300))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.frames[VideoCutFrame].video_preview.imgtk = imgtk
                self.frames[VideoCutFrame].video_preview.configure(image=imgtk, width=400, height=300)
                self.update_video_time_label(frame_index)

    def update_video_time_label(self, frame_index):
        if hasattr(self, 'fps') and self.fps:
            seconds = frame_index / self.fps
            self.frames[VideoCutFrame].time_label.config(text=f"Tempo: {seconds:.2f} s")

    def load_data(self):
        path = filedialog.askopenfilename(filetypes=[("TXT", "*.txt"),
                                                    ("Todos os arquivos", "*.*")])
        if path:
            self.data_path = path
            try:
                self.data = sensor_data.read_data(path, 'DeviceName', 'Version()', 'Battery level(%)')
                available_cols = [col for col in self.data.columns if col not in ['time', 'seconds_passed']]
                
                # Atualiza visualizações
                self.frames[DataCutFrame].update_graph()
                self.frames[MainViewFrame].update_column_selector(available_cols)
                self.frames[MainViewFrame].show_graph()

            except Exception as e:
                messagebox.showerror("Erro ao carregar dados", f"Erro: {str(e)}")


    def apply_cuts(self):
        try:
            self.video_start = float(self.entry_video_start.get() or 0)
            self.video_duration = float(self.entry_video_duration.get()) if self.entry_video_duration.get() else None
        except ValueError:
            messagebox.showerror("Erro", "Os tempos de corte do vídeo devem ser números.")
            return False

        if self.video_path:
            full_video = cv2.VideoCapture(self.video_path)
            if not full_video.isOpened():
                messagebox.showerror("Erro", "Erro ao abrir o vídeo.")
                return False

            fps = full_video.get(cv2.CAP_PROP_FPS)
            total_frames = int(full_video.get(cv2.CAP_PROP_FRAME_COUNT))
            start_frame = int(self.video_start * fps)
            self.end_frame = int((self.video_start + self.video_duration) * fps) if self.video_duration else total_frames

            self.cap = full_video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        try:
            self.data_start = float(self.entry_data_start.get() or 0)
            self.data_duration = float(self.entry_data_duration.get()) if self.entry_data_duration.get() else None
        except ValueError:
            messagebox.showerror("Erro", "Os tempos de corte dos dados devem ser números.")
            return False

        if self.data is not None:
            self.data = action_start.make_cuts_sensor(self.data, self.data_start, self.data_duration)

        return True

    def on_close(self):
        if self.cap:
            self.cap.release()
        self.root.quit()

class VideoCutFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Etapa 1: Corte do Vídeo").pack(pady=10)
        tk.Button(self, text="Carregar Vídeo", command=controller.load_video).pack(pady=5)

        tk.Label(self, text="Início vídeo (s):").pack()
        controller.entry_video_start = tk.Entry(self)
        controller.entry_video_start.pack()

        tk.Label(self, text="Duração vídeo (s):").pack()
        controller.entry_video_duration = tk.Entry(self)
        controller.entry_video_duration.pack()

        self.video_preview = tk.Label(self, width=400, height=300)
        self.video_preview.pack(pady=10)

        tk.Button(self, text="Próximo", command=lambda: controller.show_frame(DataCutFrame)).pack(pady=10)

class VideoCutFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Etapa 1: Corte do Vídeo").pack(pady=10)
        tk.Button(self, text="Carregar Vídeo", command=controller.load_video).pack(pady=5)

        tk.Label(self, text="Início vídeo (s):").pack()
        controller.entry_video_start = tk.Entry(self)
        controller.entry_video_start.pack()

        tk.Label(self, text="Duração vídeo (s):").pack()
        controller.entry_video_duration = tk.Entry(self)
        controller.entry_video_duration.pack()

        self.video_preview = tk.Label(self, width=400, height=300)
        self.video_preview.pack(pady=10)

        # Barra de rolagem de tempo (slider)
        self.scale = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL, length=400,
                              command=lambda val: controller.update_video_preview_at_frame(int(val)))
        self.scale.pack()

        # Rótulo do tempo atual
        self.time_label = tk.Label(self, text="Tempo: 0.00 s")
        self.time_label.pack(pady=5)

        tk.Button(self, text="Próximo", command=lambda: controller.show_frame(DataCutFrame)).pack(pady=10)

class DataCutFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Etapa 2: Corte dos Dados").pack(pady=10)
        tk.Button(self, text="Carregar Dados", command=controller.load_data).pack(pady=5)

        tk.Label(self, text="Início dados (s):").pack()
        controller.entry_data_start = tk.Entry(self)
        controller.entry_data_start.pack()

        tk.Label(self, text="Duração dados (s):").pack()
        controller.entry_data_duration = tk.Entry(self)
        controller.entry_data_duration.pack()

        # Frame para listbox + gráfico
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Listbox de colunas
        self.listbox = tk.Listbox(self.bottom_frame, selectmode='multiple', exportselection=False, height=8)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.listbox.bind('<<ListboxSelect>>', lambda e: self.preview_data_plot_from_selection())

        # Área do gráfico
        self.graph_frame = tk.Frame(self.bottom_frame)
        self.graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Cria a figura matplotlib
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        tk.Button(self, text="Próximo", command=lambda: controller.show_frame(MainViewFrame)).pack(pady=10)

    def update_graph(self):
        self.update_column_selector()
        self.preview_data_plot_from_selection()

    def update_column_selector(self):
        if self.controller.data is not None:
            self.listbox.delete(0, tk.END)
            available_cols = [col for col in self.controller.data.columns if col not in ['time', 'seconds_passed']]
            for col in available_cols:
                self.listbox.insert(tk.END, col)

    def preview_data_plot_from_selection(self):
        data = self.controller.data
        if data is None:
            return
        selected_cols = self.get_selected_columns()
        if not selected_cols:
            self.ax.clear()
            self.canvas.draw()
            return

        self.ax.clear()
        for col in selected_cols:
            self.ax.plot(data['seconds_passed'], data[col], label=col)
        self.ax.set_title("Pré-visualização dos Dados")
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Valor")
        self.ax.legend(fontsize="x-small")
        self.fig.tight_layout()
        self.canvas.draw()

    def get_selected_columns(self):
        selected = self.listbox.curselection()
        return [self.listbox.get(i) for i in selected]


class MainViewFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.btn_frame = tk.Frame(self)
        self.btn_frame.pack(fill=tk.X, pady=5)

        self.btn_control = tk.Button(self.btn_frame, text="Iniciar", command=self.toggle_control)
        self.btn_control.pack(side=tk.LEFT, padx=5)

        self.btn_save_graph = tk.Button(self.btn_frame, text="Salvar Gráfico", command=self.save_graph)
        self.btn_save_graph.pack(side=tk.LEFT, padx=5)

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(self.main_frame)
        self.video_label.pack(side=tk.LEFT, padx=10)

        self.right_panel = tk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        tk.Label(self.right_panel, text="Selecione as colunas para o gráfico:").pack(pady=(10, 2))
        self.listbox = tk.Listbox(self.right_panel, selectmode='multiple', exportselection=False, height=10)
        self.listbox.pack(pady=5, fill=tk.X)
        self.listbox.bind('<<ListboxSelect>>', lambda e: self.preview_data_plot_from_selection())

        self.slider = tk.Scale(self.right_panel, from_=0, to=100, orient=tk.HORIZONTAL, length=400,
                               label="Progresso do vídeo (%)", command=self.seek_video)
        self.slider.pack(pady=10)

    def update_column_selector(self, columns):
        self.listbox.delete(0, tk.END)
        for col in columns:
            self.listbox.insert(tk.END, col)

    def show_graph(self):
        if hasattr(self, 'graph_canvas'):
            return
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.graph_canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.graph_canvas.get_tk_widget().pack()

    def preview_data_plot_from_selection(self):
        data = self.controller.data
        if data is None:
            return
        selected_cols = self.get_selected_columns()
        if not selected_cols:
            return
        self.ax.clear()
        for col in selected_cols:
            self.ax.plot(data['seconds_passed'], data[col], label=col)
        self.ax.set_title("Pré-visualização das Métricas Selecionadas")
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Valor")
        self.ax.legend()
        self.graph_canvas.draw()

    def get_selected_columns(self):
        selected = self.listbox.curselection()
        return [self.listbox.get(i) for i in selected]

    def toggle_control(self):
        if not self.controller.running:
            if not self.controller.apply_cuts():
                return

            self.controller.selected_columns = self.get_selected_columns()
            if not self.controller.selected_columns:
                messagebox.showwarning("Aviso", "Selecione ao menos uma coluna para exibir no gráfico.")
                return

            self.controller.running = True
            self.controller.paused = False

            self.controller.fps = self.controller.cap.get(cv2.CAP_PROP_FPS)
            if not self.controller.fps or self.controller.fps <= 0 or self.controller.fps > 1000:
                self.controller.fps = 30
            self.controller.frame_duration_ms = int(1000 / self.controller.fps)

            self.controller.last_update_time = time.time()
            self.controller.frame_count = 0

            self.update_loop()
            self.btn_control.config(text="Pausar")
        else:
            self.controller.paused = not self.controller.paused
            self.btn_control.config(text="Retomar" if self.controller.paused else "Pausar")

    def update_loop(self):
        if not self.controller.running or not self.controller.cap or not self.controller.cap.isOpened():
            return

        if not self.controller.paused:
            current_frame = int(self.controller.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if hasattr(self.controller, "end_frame") and current_frame >= self.controller.end_frame:
                self.controller.running = False
                self.btn_control.config(text="Iniciar")
                return

            ret, frame = self.controller.cap.read()
            if not ret:
                self.controller.running = False
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            tempo_atual = self.controller.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            self.controller.frame_count += 1
            if self.controller.frame_count % 20 == 0:
                self.update_plot(tempo_atual)

            total_frames = int(self.controller.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = int(self.controller.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if total_frames > 0:
                percent = int((current_frame / total_frames) * 100)
                self.slider.set(percent)

        now = time.time()
        delay = max(1, int(self.controller.frame_duration_ms - (now - self.controller.last_update_time) * 1000))
        self.controller.last_update_time = now
        self.after(delay, self.update_loop)

    def update_plot(self, tempo_atual):
        self.ax.clear()
        selected_columns = self.get_selected_columns()
        for col in selected_columns:
            self.ax.plot(self.controller.data['seconds_passed'], self.controller.data[col], label=col)
        self.ax.axvline(tempo_atual, color='r', linestyle='--', label='Tempo Atual')
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Valor")
        self.ax.set_title("Métricas ao longo do tempo")
        self.ax.legend()
        self.graph_canvas.draw()

    def seek_video(self, value):
        cap = self.controller.cap
        if cap and cap.isOpened():
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            new_frame = int((int(value) / 100) * total_frames)
            cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)

            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

                if self.controller.running:
                    fps = cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) else 30
                    tempo_atual = new_frame / fps
                    self.update_plot(tempo_atual)

    def save_graph(self):
        if not self.controller.selected_columns:
            messagebox.showwarning("Aviso", "Nenhuma métrica selecionada para salvar.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG Image", "*.png"), ("Todos os arquivos", "*.*")])
        if file_path:
            self.fig.savefig(file_path)
            messagebox.showinfo("Sucesso", f"Gráfico salvo em:\n{file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoGraphApp(root)
    root.mainloop()
