import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

import utils
import config
from converter import load_image, process_single, save_image
from batch import process_batch


class MainWindow:
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ImageConverter")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # Переменные состояния
        self.current_image = None      # Исходное изображение (PIL Image)
        self.processed_image = None    # Сконвертированное изображение
        self.original_size = (0, 0)    # Исходные размеры (ширина, высота)
        self.config = config.load_config()
        
        # Переменные для виджетов
        self.format_var = tk.StringVar(value=self.config.get("last_format", "PNG"))
        self.width_var = tk.StringVar(value=self.config.get("last_width", ""))
        self.height_var = tk.StringVar(value=self.config.get("last_height", ""))
        self.keep_proportions_var = tk.BooleanVar(value=self.config.get("keep_proportions", True))
        self.quality_var = tk.IntVar(value=self.config.get("last_quality", 95))
        
        # Создание интерфейса
        self._create_widgets()
        self._setup_bindings()
        
    def _create_widgets(self):
        # Главная рамка
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая область - предпросмотр
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.preview_label = ttk.Label(left_frame, text="Предпросмотр", font=("Arial", 10, "bold"))
        self.preview_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.canvas = tk.Canvas(left_frame, bg="#f0f0f0", relief=tk.SUNKEN, bd=2)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Правая область - настройки
        right_frame = ttk.Frame(main_frame, width=280)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Заголовок
        ttk.Label(right_frame, text="Настройки конвертации", font=("Arial", 10, "bold")).pack(pady=(0, 10))
        
        # Кнопка загрузки
        self.load_btn = ttk.Button(right_frame, text="Открыть изображение", command=self.load_image)
        self.load_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Формат
        ttk.Label(right_frame, text="Целевой формат:").pack(anchor=tk.W, pady=(0, 2))
        self.format_combo = ttk.Combobox(right_frame, textvariable=self.format_var, 
                                          values=["PNG", "JPEG", "BMP", "WEBP"], state="readonly")
        self.format_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Размеры - размещаем в два ряда (исправлено)
        ttk.Label(right_frame, text="Размеры:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Ширина
        width_frame = ttk.Frame(right_frame)
        width_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(width_frame, text="Ширина:", width=8).pack(side=tk.LEFT)
        self.width_entry = ttk.Entry(width_frame, textvariable=self.width_var)
        self.width_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Высота
        height_frame = ttk.Frame(right_frame)
        height_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(height_frame, text="Высота:", width=8).pack(side=tk.LEFT)
        self.height_entry = ttk.Entry(height_frame, textvariable=self.height_var)
        self.height_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Чекбокс сохранения пропорций
        self.prop_check = ttk.Checkbutton(right_frame, text="Сохранять пропорции", 
                                          variable=self.keep_proportions_var)
        self.prop_check.pack(anchor=tk.W, pady=(5, 10))
        
        # Качество (для JPEG/WEBP)
        quality_frame = ttk.Frame(right_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(quality_frame, text="Качество (1-100):").pack(side=tk.LEFT, padx=(0, 10))
        self.quality_scale = ttk.Scale(quality_frame, from_=1, to=100, variable=self.quality_var,
                                        orient=tk.HORIZONTAL)
        self.quality_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.quality_label = ttk.Label(quality_frame, text=str(self.quality_var.get()))
        self.quality_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Кнопки конвертации
        self.convert_btn = ttk.Button(right_frame, text="Конвертировать", command=self.convert)
        self.convert_btn.pack(fill=tk.X, pady=(0, 5))
        
        self.save_btn = ttk.Button(right_frame, text="Сохранить как...", command=self.save, state=tk.DISABLED)
        self.save_btn.pack(fill=tk.X, pady=(0, 10))
        
        self.batch_btn = ttk.Button(right_frame, text="Пакетная конвертация", command=self.open_batch_window)
        self.batch_btn.pack(fill=tk.X)
        
        # Строка состояния
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе. Выберите изображение.")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _setup_bindings(self):
        self.width_entry.bind("<KeyRelease>", self._on_size_changed)
        self.height_entry.bind("<KeyRelease>", self._on_size_changed)
        self.quality_scale.configure(command=self._update_quality_label)
        
    def _update_quality_label(self, value):
        self.quality_label.config(text=str(int(float(value))))
        
    def _on_size_changed(self, event=None):
        if self.keep_proportions_var.get() and self.current_image:
            # Получаем текущие значения
            width_str = self.width_var.get()
            height_str = self.height_var.get()
            orig_w, orig_h = self.original_size
            
            if orig_w > 0 and orig_h > 0:
                # Определяем, какое поле было изменено
                if event and event.widget == self.width_entry:
                    width = utils.validate_positive_integer(width_str)
                    if width:
                        new_height = int(round(width * orig_h / orig_w))
                        self.height_var.set(str(new_height))
                elif event and event.widget == self.height_entry:
                    height = utils.validate_positive_integer(height_str)
                    if height:
                        new_width = int(round(height * orig_w / orig_h))
                        self.width_var.set(str(new_width))
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("Все файлы", "*.*")
            ]
        )
        if not file_path:
            return
        
        img = load_image(file_path)
        if img is None:
            self.status_var.set("Ошибка: не удалось загрузить изображение (неподдерживаемый формат или файл повреждён)")
            return
        
        self.current_image = img
        self.original_size = img.size
        
        # Устанавливаем размеры в поля ввода
        self.width_var.set(str(img.width))
        self.height_var.set(str(img.height))
        
        # Отображаем предпросмотр
        self._show_preview(img)
        
        # Сбрасываем обработанное изображение
        self.processed_image = None
        self.save_btn.config(state=tk.DISABLED)
        
        self.status_var.set(f"Загружено: {file_path} ({img.width}x{img.height})")
        
        # Сохраняем настройки
        config.update_setting("last_width", str(img.width))
        config.update_setting("last_height", str(img.height))
    
    def _show_preview(self, image: Image.Image):
        # Очищаем холст
        self.canvas.delete("all")
        
        # Получаем размеры холста
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1:  # Если холст ещё не отрисован
            canvas_width = 500
            canvas_height = 400
        
        # Масштабируем изображение под холст
        preview_img = image.copy()
        preview_img.thumbnail((canvas_width, canvas_height), Image.LANCZOS)
        
        # Конвертируем в формат Tkinter
        self.tk_image = ImageTk.PhotoImage(preview_img)
        
        # Центрируем изображение на холсте
        x = (canvas_width - self.tk_image.width()) // 2
        y = (canvas_height - self.tk_image.height()) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.tk_image)
    
    def convert(self):
        if self.current_image is None:
            self.status_var.set("Ошибка: сначала загрузите изображение")
            return
        
        # Получаем и валидируем размеры
        width = utils.validate_positive_integer(self.width_var.get())
        height = utils.validate_positive_integer(self.height_var.get())
        
        if width is None or height is None:
            self.status_var.set("Ошибка: введите корректные положительные размеры")
            return
        
        target_format = self.format_var.get()
        keep_proportions = self.keep_proportions_var.get()
        quality = self.quality_var.get()
        
        # Выбираем алгоритм интерполяции
        interpolation = self.config.get("interpolation", "LANCZOS")
        
        # Выполняем конвертацию
        self.processed_image = process_single(
            self.current_image, width, height, target_format,
            keep_proportions, interpolation, quality
        )
        
        if self.processed_image is None:
            self.status_var.set("Ошибка при конвертации")
            return
        
        self.save_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Конвертация выполнена. Формат: {target_format}, размер: {width}x{height}")
        
        # Сохраняем настройки
        config.update_setting("last_format", target_format)
        config.update_setting("last_quality", quality)
        config.update_setting("keep_proportions", keep_proportions)
    
    def save(self):
        if self.processed_image is None:
            self.status_var.set("Ошибка: сначала выполните конвертацию")
            return
        
        target_format = self.format_var.get()
        
        # Определяем расширение файла
        ext_map = {"PNG": ".png", "JPEG": ".jpg", "BMP": ".bmp", "WEBP": ".webp"}
        extension = ext_map.get(target_format, ".png")
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить изображение как...",
            defaultextension=extension,
            filetypes=[(f"{target_format} файлы", f"*{extension}"), ("Все файлы", "*.*")]
        )
        
        if not file_path:
            return
        
        quality = self.quality_var.get()
        
        if save_image(self.processed_image, file_path, target_format, quality):
            self.status_var.set(f"Сохранено: {file_path}")
        else:
            self.status_var.set("Ошибка при сохранении файла")
    
    def open_batch_window(self):
        BatchWindow(self.root, self.config)
    
    def run(self):
        # Обновляем холст после отрисовки
        self.root.update_idletasks()
        if self.current_image:
            self._show_preview(self.current_image)
        self.root.mainloop()


class BatchWindow:
    
    def __init__(self, parent, app_config):
        self.parent = parent
        self.config = app_config
        self.window = tk.Toplevel(parent)
        self.window.title("Пакетная конвертация")
        self.window.geometry("500x450")
        self.window.resizable(False, False)
        
        self.input_folder = ""
        self.output_folder = ""
        
        self._create_widgets()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Исходная папка
        ttk.Label(main_frame, text="Исходная папка:").pack(anchor=tk.W, pady=(0, 2))
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var, state="readonly")
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(input_frame, text="Обзор", command=self._select_input_folder).pack(side=tk.RIGHT)
        
        # Папка назначения
        ttk.Label(main_frame, text="Папка назначения:").pack(anchor=tk.W, pady=(0, 2))
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_var, state="readonly")
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Обзор", command=self._select_output_folder).pack(side=tk.RIGHT)
        
        # Формат
        ttk.Label(main_frame, text="Целевой формат:").pack(anchor=tk.W, pady=(0, 2))
        self.format_var = tk.StringVar(value=self.config.get("last_format", "PNG"))
        self.format_combo = ttk.Combobox(main_frame, textvariable=self.format_var,
                                          values=["PNG", "JPEG", "BMP", "WEBP"], state="readonly")
        self.format_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Изменение размера
        self.resize_var = tk.BooleanVar(value=False)
        self.resize_check = ttk.Checkbutton(main_frame, text="Изменить размер", 
                                            variable=self.resize_var, command=self._toggle_resize)
        self.resize_check.pack(anchor=tk.W, pady=(0, 5))
        
        # Рамка для размеров
        self.size_frame = ttk.Frame(main_frame)
        self.size_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.size_frame, text="Ширина:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.width_var = tk.StringVar()
        self.width_entry = ttk.Entry(self.size_frame, textvariable=self.width_var, width=10, state=tk.DISABLED)
        self.width_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(self.size_frame, text="Высота:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(self.size_frame, textvariable=self.height_var, width=10, state=tk.DISABLED)
        self.height_entry.grid(row=0, column=3)
        
        self.prop_var = tk.BooleanVar(value=True)
        self.prop_check = ttk.Checkbutton(self.size_frame, text="Сохранять пропорции", 
                                          variable=self.prop_var, state=tk.DISABLED)
        self.prop_check.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Качество
        quality_frame = ttk.Frame(main_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(quality_frame, text="Качество (1-100):").pack(side=tk.LEFT, padx=(0, 10))
        self.quality_var = tk.IntVar(value=self.config.get("last_quality", 95))
        self.quality_scale = ttk.Scale(quality_frame, from_=1, to=100, variable=self.quality_var,
                                        orient=tk.HORIZONTAL)
        self.quality_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Прогресс-бар
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                            maximum=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(10, 5))
        
        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Кнопка старта
        self.start_btn = ttk.Button(main_frame, text="Старт", command=self.start_batch)
        self.start_btn.pack(fill=tk.X)
        
    def _select_input_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с изображениями")
        if folder:
            self.input_folder = folder
            self.input_var.set(folder)
    
    def _select_output_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.output_folder = folder
            self.output_var.set(folder)
    
    def _toggle_resize(self):
        if self.resize_var.get():
            self.width_entry.config(state=tk.NORMAL)
            self.height_entry.config(state=tk.NORMAL)
            self.prop_check.config(state=tk.NORMAL)
        else:
            self.width_entry.config(state=tk.DISABLED)
            self.height_entry.config(state=tk.DISABLED)
            self.prop_check.config(state=tk.DISABLED)
    
    def _progress_callback(self, current, total, file_path, success):
        percent = int((current / total) * 100)
        self.progress_var.set(percent)
        status = "✓" if success else "✗"
        self.progress_label.config(text=f"{status} {current}/{total}: {file_path}")
        self.window.update_idletasks()
    
    def start_batch(self):
        # Проверка выбора папок
        if not self.input_folder or not self.output_folder:
            messagebox.showerror("Ошибка", "Выберите исходную папку и папку назначения")
            return
        
        target_format = self.format_var.get()
        quality = self.quality_var.get()
        
        width = None
        height = None
        keep_proportions = False
        
        if self.resize_var.get():
            width = utils.validate_positive_integer(self.width_var.get())
            height = utils.validate_positive_integer(self.height_var.get())
            if width is None or height is None:
                messagebox.showerror("Ошибка", "Введите корректные размеры")
                return
            keep_proportions = self.prop_var.get()
        
        # Блокируем кнопку на время выполнения
        self.start_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        # Выполняем пакетную обработку
        success, errors = process_batch(
            input_folder=self.input_folder,
            output_folder=self.output_folder,
            target_format=target_format,
            width=width,
            height=height,
            keep_proportions=keep_proportions,
            interpolation=self.config.get("interpolation", "LANCZOS"),
            quality=quality,
            progress_callback=self._progress_callback
        )
        
        # Разблокируем кнопку
        self.start_btn.config(state=tk.NORMAL)
        
        # Выводим результат
        messagebox.showinfo("Завершено", 
                           f"Пакетная конвертация завершена.\n"
                           f"Успешно: {success}\n"
                           f"Ошибок: {errors}")
        
        self.progress_label.config(text=f"Готово. Успешно: {success}, Ошибок: {errors}")