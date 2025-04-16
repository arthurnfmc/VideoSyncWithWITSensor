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

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill=tk.X, pady=5)

        self.btn_load_video = tk.Button(self.btn_frame, text="Carregar Vídeo", command=self.load_video)
        self.btn_load_video.pack(side=tk.LEFT, padx=5)

        self.btn_load_data = tk.Button(self.btn_frame, text="Carregar Dados (.txt)", command=self.load_data)
        self.btn_load_data.pack(side=tk.LEFT, padx=5)

        self.btn_control = tk.Button(self.btn_frame, text="Iniciar", command=self.toggle_control, state='disabled')
        self.btn_control.pack(side=tk.LEFT, padx=5)

        self.btn_save_graph = tk.Button(self.btn_frame, text="Salvar Gráfico", command=self.save_graph)
        self.btn_save_graph.pack(side=tk.LEFT, padx=5)

        cut_frame = tk.Frame(self.root)
        cut_frame.pack(pady=5)

        tk.Label(cut_frame, text="Início vídeo (s):").grid(row=0, column=0)
        self.entry_video_start = tk.Entry(cut_frame, width=5)
        self.entry_video_start.grid(row=0, column=1)

        tk.Label(cut_frame, text="Duração vídeo (s):").grid(row=0, column=2)
        self.entry_video_duration = tk.Entry(cut_frame, width=5)
        self.entry_video_duration.grid(row=0, column=3)

        tk.Label(cut_frame, text="Início dados (s):").grid(row=1, column=0)
        self.entry_data_start = tk.Entry(cut_frame, width=5)
        self.entry_data_start.grid(row=1, column=1)

        tk.Label(cut_frame, text="Duração dados (s):").grid(row=1, column=2)
        self.entry_data_duration = tk.Entry(cut_frame, width=5)
        self.entry_data_duration.grid(row=1, column=3)

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(self.main_frame)
        self.video_label.pack(side=tk.LEFT, padx=10)

        self.right_panel = tk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        tk.Label(self.right_panel, text="Selecione as colunas para o gráfico:").pack(pady=(10, 2))
        self.listbox = tk.Listbox(self.right_panel, selectmode='multiple', exportselection=False, height=10)
        self.listbox.pack(pady=5, fill=tk.X)
        self.listbox.bind('<<ListboxSelect>>', lambda e: self.preview_data_plot_from_selection())

        # Slider de tempo
        self.slider = tk.Scale(self.right_panel, from_=0, to=100, orient=tk.HORIZONTAL, length=400,
                               label="Progresso do vídeo (%)", command=self.seek_video)
        self.slider.pack(pady=10)

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Vídeo MP4", "*.mp4"),
                                                      ("Vídeo AVI", "*.avi"),
                                                      ("Todos os arquivos", "*.*")])
        if path:
            self.video_path = path
            self.cap = cv2.VideoCapture(self.video_path)
            self.btn_load_video.pack_forget()
            self.check_ready()
        
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    def preview_data_plot_from_selection(self):
        if self.data is None:
            return

        selected_cols = self.get_selected_columns()
        if not selected_cols:
            return  # não plota nada se nada for selecionado

        self.ax.clear()
        for col in selected_cols:
            self.ax.plot(self.data['seconds_passed'], self.data[col], label=col)

        self.ax.set_title("Pré-visualização das Métricas Selecionadas")
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Valor")
        self.ax.legend()
        self.graph_canvas.draw()

    def load_data(self):
        path = filedialog.askopenfilename(filetypes=[("TXT", "*.txt"),
                                                      ("Todos os arquivos", "*.*")])
        if path:
            self.data_path = path
            try:
                self.data = sensor_data.read_data(
                    path,
                    'DeviceName', 'Version()', 'Battery level(%)'
                )
                available_cols = [col for col in self.data.columns if col not in ['time', 'seconds_passed']]
                self.update_column_selector(available_cols)
                self.show_graph()
                self.preview_data_plot_from_selection()
                self.btn_load_data.pack_forget()
                self.check_ready()
            except Exception as e:
                messagebox.showerror("Erro ao carregar dados", f"Erro: {str(e)}")

    def update_column_selector(self, columns):
        self.listbox.delete(0, tk.END)
        for col in columns:
            self.listbox.insert(tk.END, col)

    def show_graph(self):
        if self.graph_canvas:
            return  # já foi criado
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.graph_canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.graph_canvas.get_tk_widget().pack()

    def check_ready(self):
        if self.video_path and self.data is not None:
            self.btn_control.config(state='normal')

    def get_selected_columns(self):
        selected = self.listbox.curselection()
        return [self.listbox.get(i) for i in selected]

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

    def toggle_control(self):
        if not self.running:
            self.start_display()
            self.btn_control.config(text="Pausar")
        else:
            self.paused = not self.paused
            self.btn_control.config(text="Retomar" if self.paused else "Pausar")

    def start_display(self):
        if not self.apply_cuts():
            return

        self.selected_columns = self.get_selected_columns()
        if not self.selected_columns:
            messagebox.showwarning("Aviso", "Selecione ao menos uma coluna para exibir no gráfico.")
            return

        self.running = True
        self.paused = False

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if not self.fps or self.fps <= 0 or self.fps > 1000:
            self.fps = 30
        self.frame_duration_ms = int(1000 / self.fps)

        self.last_update_time = time.time()
        self.frame_count = 0

        self.update_loop()

    def update_plot(self, tempo_atual):
        self.ax.clear()
        for col in self.selected_columns:
            self.ax.plot(self.data['seconds_passed'], self.data[col], label=col)

        self.ax.axvline(tempo_atual, color='r', linestyle='--', label='Tempo Atual')
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Valor")
        self.ax.set_title("Métricas ao longo do tempo")
        self.ax.legend()
        self.graph_canvas.draw()

    def update_loop(self):
        if not self.running or not self.cap or not self.cap.isOpened():
            return

        if not self.paused:
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if hasattr(self, "end_frame") and current_frame >= self.end_frame:
                self.running = False
                self.btn_control.config(text="Iniciar")
                return

            ret, frame = self.cap.read()
            if not ret:
                self.running = False
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            tempo_atual = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            self.frame_count += 1
            if self.frame_count % 20 == 0:
                self.update_plot(tempo_atual)

            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if total_frames > 0:
                percent = int((current_frame / total_frames) * 100)
                self.slider.set(percent)

        now = time.time()
        delay = max(1, int(self.frame_duration_ms - (now - self.last_update_time) * 1000))
        self.last_update_time = now
        self.root.after(delay, self.update_loop)

    def seek_video(self, value):
        if self.cap and self.cap.isOpened():
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            new_frame = int((int(value) / 100) * total_frames)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)

            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

                # Só atualiza o gráfico se o controle já foi iniciado
                if self.running:
                    fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap.get(cv2.CAP_PROP_FPS) else 30
                    tempo_atual = new_frame / fps
                    self.update_plot(tempo_atual)

    def save_graph(self):
        if not self.selected_columns:
            messagebox.showwarning("Aviso", "Nenhuma métrica selecionada para salvar.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG Image", "*.png"), ("Todos os arquivos", "*.*")])
        if file_path:
            self.fig.savefig(file_path)
            messagebox.showinfo("Sucesso", f"Gráfico salvo em:\n{file_path}")

    def on_close(self):
        if self.cap:
            self.cap.release()
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoGraphApp(root)
    root.mainloop()
