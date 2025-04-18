import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
import cv2
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

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

        self.create_widgets()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Botões superiores
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Carregar Vídeo", command=self.load_video).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Carregar Dados (.txt)", command=self.load_data).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Iniciar", command=self.start_display).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Pausar / Retomar", command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Salvar Gráfico", command=self.save_graph).pack(side=tk.LEFT, padx=5)

        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Área do vídeo
        self.video_label = tk.Label(main_frame)
        self.video_label.pack(side=tk.LEFT, padx=10)

        # Área do gráfico + seleção de colunas
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack()

        # Listbox para colunas
        tk.Label(right_panel, text="Selecione as colunas para o gráfico:").pack(pady=(10, 2))
        self.listbox = tk.Listbox(right_panel, selectmode='multiple', exportselection=False, height=10)
        self.listbox.pack(pady=5, fill=tk.X)

        # Slider de tempo
        self.slider = tk.Scale(right_panel, from_=0, to=100, orient=tk.HORIZONTAL, length=400,
                               label="Progresso do vídeo (%)", command=self.seek_video)
        self.slider.pack(pady=10)

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Vídeo MP4", "*.mp4"),
                                                    ("Vídeo AVI", "*.avi"),
                                                    ("Todos os arquivos", "*.*")])
        if path:
            self.video_path = path
            self.cap = cv2.VideoCapture(self.video_path)

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
            except Exception as e:
                messagebox.showerror("Erro ao carregar dados", f"Erro: {str(e)}")

    def update_column_selector(self, columns):
        self.listbox.delete(0, tk.END)
        for col in columns:
            self.listbox.insert(tk.END, col)

    def get_selected_columns(self):
        selected = self.listbox.curselection()
        return [self.listbox.get(i) for i in selected]

    def start_display(self):
        if not self.cap or self.data is None:
            messagebox.showwarning("Aviso", "Você precisa carregar o vídeo e os dados primeiro.")
            return
        self.selected_columns = self.get_selected_columns()
        if not self.selected_columns:
            messagebox.showwarning("Aviso", "Selecione ao menos uma coluna para exibir no gráfico.")
            return

        self.running = True
        self.paused = False

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.frame_duration_ms = int(1000 / self.fps)

        self.update_loop()

    def update_loop(self):
        if not self.running or not self.cap or not self.cap.isOpened():
            return

        if not self.paused:
            ret, frame = self.cap.read()
            if not ret:
                self.running = False
                return

            # Exibe frame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            # Tempo atual do vídeo
            tempo_atual = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            # Atualiza gráfico com linha vertical indicando tempo atual
            self.ax.clear()
            for col in self.selected_columns:
                self.ax.plot(self.data['seconds_passed'], self.data[col], label=col)

            self.ax.axvline(tempo_atual, color='r', linestyle='--', label='Tempo Atual')
            self.ax.set_xlabel("Tempo (s)")
            self.ax.set_ylabel("Valor")
            self.ax.set_title("Métricas ao longo do tempo")
            self.ax.legend()
            self.canvas.draw()

            # Atualiza slider
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if total_frames > 0:
                percent = int((current_frame / total_frames) * 100)
                self.slider.set(percent)

        # Chama próxima iteração
        self.root.after(self.frame_duration_ms, self.update_loop)

    def toggle_pause(self):
        if not self.cap:
            return
        self.paused = not self.paused

    def seek_video(self, value):
        if self.cap and self.cap.isOpened():
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            new_frame = int((int(value) / 100) * total_frames)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)

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
        """Lida com o evento de fechamento da janela."""
        if self.cap:
            self.cap.release()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoGraphApp(root)
    root.mainloop()
