# -*- coding: utf-8 -*-
"""
frontend.py
前端界面，只调用 backend.py 中的函数：
    - junction_parameters(type)
    - junction_layout(type, options)
    - gds_generator(name_list)
"""

import os
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import contextlib

# ======== 从后端导入你的函数 ========
try:
    from junction_generator import junction_parameters, junction_layout, gds_generator
except Exception as e:
    # 如果这里失败，整个界面都会提示错误
    raise RuntimeError(f"导入 backend 失败，请检查 backend.py：{e}")


class JunctionApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("约瑟夫森结 GDS 生成器")
        self.geometry("1100x700")

        self.current_type = None
        self.current_options = {}  # 初始化为空字典，而不是 None
        self.param_entries = {}
        self._photo_image = None

        self._build_ui()

        # 初始化时调用 junction_parameters 获取默认参数
        default_type = "Single_Manhattan"
        self.type_var.set(default_type)
        # 先设置 current_type
        self.current_type = default_type
        # 手动调用一次类型切换逻辑
        self.on_type_changed()

    # ================== UI ==================

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左侧
        left_frame = ttk.Frame(self, padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)

        # 右侧
        right_frame = ttk.Frame(self, padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=3)
        right_frame.grid_rowconfigure(1, weight=2)
        right_frame.grid_columnconfigure(0, weight=1)

        # ---- 左上：类型选择 ----
        type_frame = ttk.LabelFrame(left_frame, text="选择结类型", padding=10)
        type_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(type_frame, text="类型：").grid(row=0, column=0, sticky="w")

        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.type_var,
            state="readonly",
            values=[
                "Single_Manhattan",
                "Squid_Manhattan",
                "SquidFlip_Manhattan",
                "Single_Dolan",
            ],
        )
        self.type_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", self.on_type_changed)

        type_frame.grid_columnconfigure(1, weight=1)

        # ---- 左中：参数表 ----
        self.params_frame = ttk.LabelFrame(left_frame, text="参数设置", padding=10)
        self.params_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        self.params_frame.grid_columnconfigure(0, weight=0)
        self.params_frame.grid_columnconfigure(1, weight=1)

        # ---- 左下：按钮 ----
        button_frame = ttk.Frame(left_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=2, column=0, sticky="ew")

        self.run_button = ttk.Button(button_frame, text="生成 GDS", command=self.run_junction_layout)
        self.run_button.grid(row=0, column=0, padx=5)

        self.merge_button = ttk.Button(button_frame, text="合并 GDS 文件", command=self.merge_gds_files)
        self.merge_button.grid(row=0, column=1, padx=5)

        # ---- 右上：图片 ----
        preview_frame = ttk.LabelFrame(right_frame, text="shot.png 预览", padding=10)
        preview_frame.grid(row=0, column=0, sticky="nsew")
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ttk.Label(preview_frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # ---- 右下：日志 ----
        log_frame = ttk.LabelFrame(right_frame, text="输出信息", padding=10)
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", height=10)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

    # ================== 事件回调 ==================
    def _get_default_parameters(self, jj_type):
        """获取指定类型的默认参数"""
        try:
            options = junction_parameters(type=jj_type)
            # 确保转换为普通字典
            if hasattr(options, 'items'):
                self.current_options = dict(options)
            else:
                self.current_options = options
            self._log(f"[DEBUG] 获取到 {jj_type} 的默认参数: {self.current_options}\n")
        except Exception as e:
            self._log(f"[ERROR] 获取默认参数失败: {e}\n")
            self.current_options = {}

    def on_type_changed(self, event=None):
        """选择类型后：从 backend 获取默认参数，并显示在左侧表格"""
        jj_type = self.type_var.get()

        # 确保 self.current_type 被正确设置
        self.current_type = jj_type
        self._log(f"\n[DEBUG] 切换类型为：{jj_type}\n")

        try:
            options = junction_parameters(type=jj_type)
            self._log(f"[DEBUG] backend 返回的原始参数对象：{repr(options)}\n")
        except Exception as e:
            messagebox.showerror("错误", f"调用 junction_parameters(type='{jj_type}') 失败：\n{e}")
            self._log(f"[ERROR] 调 junction_parameters 失败：{e}\n")
            self.current_options = None
            self._build_param_entries()
            return

        # ====== 关键：把 backend 的 Dict 强制转成普通 dict ======
        try:
            # qiskit_metal.toolbox_metal.Dict 通常继承自 dict，这里保险全部转一次
            options_dict = dict(options)
        except Exception:
            # 如果不能直接 dict()，再尝试用 items()
            try:
                options_dict = {k: v for k, v in options.items()}
            except Exception as e:
                messagebox.showerror("错误", f"无法将返回的参数转换为字典：\n{e}")
                self._log(f"[ERROR] 转成 dict 失败：{e}\n")
                self.current_options = None
                self._build_param_entries()
                return

        self.current_options = options_dict
        self._log(f"[DEBUG] 转换成普通 dict 后的参数：{self.current_options}\n")

        # 用这些参数更新左侧 Entry
        self._build_param_entries()

    def _clear_param_entries(self):
        """清空参数输入框"""
        for child in self.params_frame.winfo_children():
            child.destroy()
        self.param_entries.clear()

    def _build_param_entries(self):
        """根据 self.current_options 生成/更新参数输入框"""
        self._clear_param_entries()

        if not self.current_options:
            ttk.Label(self.params_frame, text="暂无参数").grid(row=0, column=0, sticky="w", pady=2)
            self._log("[INFO] 当前类型没有参数配置\n")
            return

        for row_index, (key, value) in enumerate(self.current_options.items()):
            # 显示参数名称
            ttk.Label(self.params_frame, text=f"{key}：").grid(
                row=row_index, column=0, sticky="w", pady=2, padx=(0, 10)
            )

            # 创建输入框并设置默认值
            var = tk.StringVar()
            entry = ttk.Entry(self.params_frame, textvariable=var)
            entry.grid(row=row_index, column=1, sticky="ew", pady=2)

            # 设置默认值
            var.set(str(value))
            self.param_entries[key] = (entry, var)  # 同时存储entry和var

            # 添加标签显示值类型（可选，用于调试）
            type_label = ttk.Label(self.params_frame, text=f"({type(value).__name__})", foreground="gray")
            type_label.grid(row=row_index, column=2, sticky="w", pady=2, padx=(5, 0))

        self.params_frame.grid_columnconfigure(1, weight=1)
        self._log(f"[INFO] 已创建 {len(self.current_options)} 个参数输入框\n")

    def _update_options_from_entries(self):
        """读取用户在 Entry 中修改后的参数，写回 self.current_options"""
        if not self.current_options:
            return

        for key, (entry, var) in self.param_entries.items():
            try:
                # 保持原始类型转换
                old_value = self.current_options[key]
                new_value_str = var.get()

                # 根据原始类型进行转换
                if isinstance(old_value, (int, float)):
                    # 尝试转换为数字
                    if isinstance(old_value, int):
                        self.current_options[key] = int(float(new_value_str))
                    else:
                        self.current_options[key] = float(new_value_str)
                else:
                    self.current_options[key] = new_value_str
            except Exception as e:
                self._log(f"[WARNING] 参数 {key} 转换失败: {e}\n")
                # 保持原值
                pass

    def run_junction_layout(self):
        """生成单个结的 GDS，并截图"""
        # 添加调试信息
        self._log(f"\n[DEBUG] 开始运行 run_junction_layout\n")
        self._log(f"[DEBUG] self.current_type = {self.current_type}\n")
        self._log(f"[DEBUG] self.type_var.get() = {self.type_var.get()}\n")

        if not self.current_type:
            # 如果 self.current_type 为空，尝试从下拉框获取
            self.current_type = self.type_var.get()
            self._log(f"[DEBUG] 重新获取 self.current_type = {self.current_type}\n")

        if not self.current_type:
            messagebox.showwarning("提示", "请先选择一种约瑟夫森结类型。")
            return

        if self.current_options is None:
            messagebox.showwarning("提示", "当前类型没有有效参数。")
            return

        self._update_options_from_entries()

        stdout_buffer = io.StringIO()
        self._log("\n====== 生成 GDS 开始 ======\n")
        self._log(f"[INFO] 使用类型: {self.current_type}\n")
        self._log(f"[INFO] 使用参数: {self.current_options}\n")

        try:
            with contextlib.redirect_stdout(stdout_buffer):
                # 明确传递参数
                design, gui = junction_layout(type=self.current_type, options=self.current_options)
                # try:
                #     gui.screenshot("shot.png")
                #     print("Screenshot saved as shot.png")
                # except Exception as e:
                #     print(f"截图 shot.png 失败：{e}")
        except Exception as e:
            self._log(stdout_buffer.getvalue())
            self._log(f"\n发生错误：\n{e}\n")
            # 特别检查错误信息
            if "未找到" in str(e) or "not found" in str(e).lower():
                self._log("[ERROR] 可能类型不匹配，请检查类型名称是否正确\n")
        else:
            self._log(stdout_buffer.getvalue())
            self._log("====== 生成 GDS 完成 ======\n")
            self._update_image_preview("shot.png")

    def merge_gds_files(self):
        """选择多个 gds 文件，调用后端合并"""
        initial_dir = os.path.abspath("gds")
        if not os.path.isdir(initial_dir):
            initial_dir = os.getcwd()

        file_paths = filedialog.askopenfilenames(
            title="选择要合并的 GDS 文件",
            initialdir=initial_dir,
            filetypes=[("GDS 文件", "*.gds"), ("所有文件", "*.*")]
        )
        if not file_paths:
            return

        name_list = [os.path.splitext(os.path.basename(p))[0] for p in file_paths]

        stdout_buffer = io.StringIO()
        self._log("\n====== 合并 GDS 开始 ======\n")
        self._log(f"选中的文件名：{name_list}\n")

        try:
            with contextlib.redirect_stdout(stdout_buffer):
                gds_generator(name_list)
        except Exception as e:
            self._log(stdout_buffer.getvalue())
            self._log(f"\n合并时发生错误：\n{e}\n")
        else:
            self._log(stdout_buffer.getvalue())
            self._log("====== 合并 GDS 完成 ======\n")
            self._log("输出文件：Fake_Junctions.GDS\n")

    # ================== 辅助 ==================

    def _log(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def _update_image_preview(self, image_path):
        if not os.path.exists(image_path):
            self._log(f"图片文件 {image_path} 不存在，无法预览。\n")
            return
        try:
            img = Image.open(image_path)
            img.thumbnail((500, 400))
            self._photo_image = ImageTk.PhotoImage(img)
            self.image_label.configure(image=self._photo_image)
        except Exception as e:
            self._log(f"加载图片 {image_path} 失败：{e}\n")


if __name__ == "__main__":
    app = JunctionApp()
    app.mainloop()
