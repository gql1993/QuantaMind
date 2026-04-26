import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
from quantum_chip_layout import *
from PIL import Image, ImageTk
from tkinter import scrolledtext
import sys
import io
import os
import json
import threading
import time

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


image_path = resource_path("image.png")


class TextRedirector(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.old_stdout = sys.stdout

    def write(self, string):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # 自动滚动到最新内容
        self.text_widget.configure(state='disabled')
        self.text_widget.update()

    def flush(self):
        pass


def generate_layout():
    global current_design, gui
    try:
        chip_size = float(entry_chip_size.get())
        pad_num = int(entry_pad_num.get())
        rotation_angle = float(entry_rotation_angle.get())
        qq_space = float(entry_qq_space.get())
        row = int(entry_row.get())
        column = int(entry_column.get())
        shift_x = float(entry_shift_x.get())
        shift_y = float(entry_shift_y.get())
    except ValueError:
        messagebox.showerror("输入错误", "请确保所有输入为正确的数字格式")
        return

    if chip_size <= 0 or pad_num <= 0 or qq_space <= 0 or row <= 0 or column <= 0:
        messagebox.showerror("输入错误", "芯片大小、引脚个数、比特间距、行数和列数必须为正数")
        return

    try:
        # 生成版图
        if current_design is not None:
            current_design = None  # 删除旧的设计数据

        # 手动释放图像资源（如果有）
        try:
            img.close()  # 关闭旧的图片资源
        except:
            pass

        current_design, gui = qubit_flipchip_layout(chip_size, pad_num, rotation_angle, qq_space, row, column, shift_x,
                                                    shift_y)
        print("版图生成成功！")

    except MemoryError:
        messagebox.showerror("内存错误", "内存不足，无法继续执行。请重启程序或释放资源。")
    except Exception as e:
        messagebox.showerror("生成失败", f"生成版图时发生错误: {str(e)}")
        print(f"生成版图时发生错误: {str(e)}")
        return


def export_forbidden_and_pins():
    if current_design is None:
        messagebox.showerror("错误", "请先生成版图设计！")
        return

    try:
        row = int(entry_row.get())
        column = int(entry_column.get())
    except ValueError:
        messagebox.showerror("输入错误", "行数和列数必须为整数")
        return

    forbidden_zone_and_pins(current_design, row, column,excluded_qubits_path)


def select_excluded_qubits_file():
    global excluded_qubits_path
    filename = filedialog.askopenfilename(
        title="选择要排除的量子比特文件",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
    )
    if filename:
        excluded_qubits_path = filename
        btn_select_excluded_qubits.config(text=f"已选择: {os.path.basename(filename)}")
        print(f"已选择排除量子比特文件: {filename}")
        messagebox.showinfo("加载成功", "排除比特文件已加载完成！")
    else:
        excluded_qubits_path = None
        btn_select_excluded_qubits.config(text="选择排除比特文件")




# 新增功能1：选择文件
def select_file():
    global selected_filename
    filename = filedialog.askopenfilename(
        title="选择布线文件",
        filetypes=[
            ("文本文件", "*.txt"),
            ("所有文件", "*.*")
        ]
    )
    if filename:
        selected_filename = filename
        # 更新文件选择按钮的文本显示文件名
        btn_select_file.config(text=f"已选择: {os.path.basename(filename)}")
        print(f"已选择文件: {filename}")
        # 新增：弹出信息提示文件加载完成
        messagebox.showinfo("加载成功", "布线文件已经加载完成！")
    else:
        selected_filename = None
        btn_select_file.config(text="选择布线文件")


# 进度条更新函数
def update_progress(value, text=""):
    """更新进度条和状态文本"""
    try:
        progress_var.set(value)
        if text:
            progress_label.config(text=text)
        root.update_idletasks()
    except Exception:
        pass  # 如果更新失败，静默处理


# 显示进度条
def show_progress_bar():
    """显示进度条"""
    try:
        progress_frame.pack(fill=tk.X, pady=(10, 5), padx=20)
        progress_var.set(0)
        progress_label.config(text="准备开始布线...")
    except Exception:
        pass


# 隐藏进度条
def hide_progress_bar():
    """隐藏进度条"""
    try:
        progress_frame.pack_forget()
    except Exception:
        pass


# 禁用布线相关按钮
def disable_routing_buttons():
    """禁用布线操作按钮"""
    try:
        btn_select_file.config(state='disabled')
        btn_parse_route.config(state='disabled')
        btn_delete_lines.config(state='disabled')
    except Exception:
        pass


# 启用布线相关按钮
def enable_routing_buttons():
    """启用布线操作按钮"""
    try:
        btn_select_file.config(state='normal')
        btn_parse_route.config(state='normal')
        btn_delete_lines.config(state='normal')
    except Exception:
        pass


# 布线成功完成的处理
def on_routing_success():
    """布线成功完成时的处理"""
    print("布线执行完成！")
    hide_progress_bar()
    enable_routing_buttons()


# 布线失败的处理
def on_routing_error(error_message):
    """布线失败时的处理"""
    messagebox.showerror("布线失败", f"执行布线时发生错误: {error_message}")
    print(f"执行布线时发生错误: {error_message}")
    hide_progress_bar()
    enable_routing_buttons()


# 布线线程函数
def routing_thread():
    """在单独线程中执行布线操作"""
    # global current_design, selected_filename
    try:
        # 初始化进度
        root.after(0, lambda: update_progress(0, "正在初始化布线..."))
        time.sleep(0.5)  # 模拟初始化时间

        # 开始布线
        root.after(0, lambda: update_progress(20, "正在解析布线文件..."))
        time.sleep(0.5)  # 模拟文件解析时间

        root.after(0, lambda: update_progress(40, "正在执行布线算法..."))
        print(f"开始执行布线，文件: {selected_filename}")

        # 模拟布线过程的不同阶段
        root.after(0, lambda: update_progress(60, "正在优化布线路径..."))
        time.sleep(1)  # 模拟布线计算时间

        root.after(0, lambda: update_progress(80, "正在生成布线结果..."))

        # 执行实际的布线函数
        parse_and_route(selected_filename, current_design, gui)

        root.after(0, lambda: update_progress(100, "布线完成！"))
        time.sleep(0.5)

        # 完成后的UI更新
        root.after(0, on_routing_success)


    except Exception as e:
        # 捕获错误信息
        error_msg = str(e)
        # 使用捕获的错误信息更新UI
        root.after(0, lambda msg=error_msg: on_routing_error(msg))


# 修改后的执行布线函数
def run_parse_and_route():
    global current_design, selected_filename

    if current_design is None:
        messagebox.showerror("错误", "请先生成版图设计！")
        return

    if selected_filename is None:
        messagebox.showerror("错误", "请先选择布线文件！")
        return

    # 显示进度条并禁用按钮
    show_progress_bar()
    disable_routing_buttons()

    # 在新线程中执行布线
    thread = threading.Thread(target=routing_thread, daemon=True)
    thread.start()


def run_delete_all_lines():
    if current_design is None:
        messagebox.showerror("错误", "请先生成版图设计！")
        return

    try:
        result = messagebox.askyesno("确认删除", "确定要删除所有布线吗？此操作不可撤销！")
        if result:
            delete_all_lines(current_design, gui)
            print("所有布线已删除！")
    except Exception as e:
        messagebox.showerror("删除失败", f"删除布线时发生错误: {str(e)}")
        print(f"删除布线时发生错误: {str(e)}")


def get_current_parameters():
    try:
        parameters = {
            "chip_size": float(entry_chip_size.get()),
            "pad_num": int(entry_pad_num.get()),
            "rotation_angle": float(entry_rotation_angle.get()),
            "qq_space": float(entry_qq_space.get()),
            "row": int(entry_row.get()),
            "column": int(entry_column.get()),
            "shift_x": float(entry_shift_x.get()),
            "shift_y": float(entry_shift_y.get())
        }
        return parameters
    except ValueError as e:
        raise ValueError("参数格式错误，请检查输入的数值是否正确")


def set_parameters(parameters):
    try:
        entry_chip_size.delete(0, tk.END)
        entry_chip_size.insert(0, str(parameters.get("chip_size", 33)))

        entry_pad_num.delete(0, tk.END)
        entry_pad_num.insert(0, str(parameters.get("pad_num", 42)))

        entry_rotation_angle.delete(0, tk.END)
        entry_rotation_angle.insert(0, str(parameters.get("rotation_angle", 45)))

        entry_qq_space.delete(0, tk.END)
        entry_qq_space.insert(0, str(parameters.get("qq_space", 2.5)))

        entry_row.delete(0, tk.END)
        entry_row.insert(0, str(parameters.get("row", 10)))

        entry_column.delete(0, tk.END)
        entry_column.insert(0, str(parameters.get("column", 6)))

        entry_shift_x.delete(0, tk.END)
        entry_shift_x.insert(0, str(parameters.get("shift_x", 0)))

        entry_shift_y.delete(0, tk.END)
        entry_shift_y.insert(0, str(parameters.get("shift_y", 0)))

    except Exception as e:
        raise Exception(f"设置参数时发生错误: {str(e)}")


def export_parameters():
    try:
        parameters = get_current_parameters()

        filename = filedialog.asksaveasfilename(
            title="保存参数文件",
            defaultextension=".json",
            filetypes=[
                ("JSON文件", "*.json"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(parameters, f, indent=4, ensure_ascii=False)

            print(f"参数已导出到: {filename}")
            messagebox.showinfo("导出成功", f"参数文件已保存到:\n{filename}")

    except ValueError as e:
        messagebox.showerror("导出失败", str(e))
    except Exception as e:
        messagebox.showerror("导出失败", f"导出参数时发生错误: {str(e)}")
        print(f"导出参数失败: {str(e)}")


def import_parameters():
    try:
        filename = filedialog.askopenfilename(
            title="选择参数文件",
            filetypes=[
                ("JSON文件", "*.json"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                parameters = json.load(f)

            required_keys = ["chip_size", "pad_num", "rotation_angle", "qq_space",
                             "row", "column", "shift_x", "shift_y"]

            missing_keys = [key for key in required_keys if key not in parameters]
            if missing_keys:
                raise ValueError(f"参数文件缺少必要的参数: {', '.join(missing_keys)}")

            set_parameters(parameters)

            print(f"参数已从文件导入: {filename}")
            messagebox.showinfo("导入成功", "参数文件已成功加载!")

    except FileNotFoundError:
        messagebox.showerror("导入失败", "找不到指定的文件")
    except json.JSONDecodeError:
        messagebox.showerror("导入失败", "文件格式错误，请确保是有效的JSON文件")
    except ValueError as e:
        messagebox.showerror("导入失败", str(e))
    except Exception as e:
        messagebox.showerror("导入失败", f"导入参数时发生错误: {str(e)}")
        print(f"导入参数失败: {str(e)}")


# 创建主窗口
root = tk.Tk()
root.title("量子芯片布局设计")
root.geometry("1400x780")
root.resizable(True, True)

style = ttk.Style()
style.theme_use('clam')
style.configure('Accent.TButton', font=('Helvetica', 12, 'bold'), padding=10,
                foreground='white', background='#0078d7')
style.map('Accent.TButton',
          background=[('active', '#005a9e')],
          foreground=[('disabled', '#a0a0a0')])

style.configure('File.TButton', font=('Helvetica', 11), padding=8,
                foreground='black', background='#f0f0f0')
style.map('File.TButton',
          background=[('active', '#e0e0e0')])

style.configure('Danger.TButton', font=('Helvetica', 11, 'bold'), padding=8,
                foreground='white', background='#dc3545')
style.map('Danger.TButton',
          background=[('active', '#c82333')])

style.configure('Param.TButton', font=('Helvetica', 11), padding=8,
                foreground='white', background='#28a745')
style.map('Param.TButton',
          background=[('active', '#218838')])

# 主框架
main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# 左侧控制面板
control_panel = ttk.Frame(main_frame)
control_panel.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 20))
control_panel.configure(width=450)

# 右侧区域 - 包含图片和输出
right_frame = ttk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# === 左侧控制面板内容 ===

# 参数输入区域
param_input_frame = ttk.LabelFrame(control_panel, text="参数设置", padding=15)
param_input_frame.pack(fill=tk.X, expand=False, pady=(0, 15))

labels_texts = [
    ("芯片大小 (mm)", "33"),
    ("引脚个数", "42"),
    ("旋转角度 (度)", "45"),
    ("比特间距 (mm)", "2.5"),
    ("行数", "10"),
    ("列数", "6"),
    ("X方向位移 (mm)", "0"),
    ("Y方向位移 (mm)", "0")
]

entries = []
for i, (label_text, default_value) in enumerate(labels_texts):
    ttk.Label(param_input_frame, text=label_text, font=('Helvetica', 11)).grid(
        row=i, column=0, sticky=tk.W, pady=6, padx=(0, 10))

    entry = ttk.Entry(param_input_frame, font=('Helvetica', 11), width=15)
    entry.grid(row=i, column=1, pady=6)
    entry.insert(0, default_value)
    entries.append(entry)

(entry_chip_size, entry_pad_num, entry_rotation_angle, entry_qq_space,
 entry_row, entry_column, entry_shift_x, entry_shift_y) = entries

# 使用选项卡组织功能按钮
notebook = ttk.Notebook(control_panel)
notebook.pack(fill=tk.BOTH, expand=True)

# === 选项卡1: 参数管理 ===
param_tab = ttk.Frame(notebook)
notebook.add(param_tab, text="参数管理")

btn_import_params = ttk.Button(param_tab, text="导入参数文件", style='Param.TButton', command=import_parameters)
btn_import_params.pack(fill=tk.X, pady=(20, 8), padx=20, ipady=8)

btn_export_params = ttk.Button(param_tab, text="导出参数文件", style='Param.TButton', command=export_parameters)
btn_export_params.pack(fill=tk.X, pady=8, padx=20, ipady=8)

# === 选项卡2: 版图生成 ===
layout_tab = ttk.Frame(notebook)
notebook.add(layout_tab, text="版图生成")

btn_generate = ttk.Button(layout_tab, text="生成版图", style='Accent.TButton', command=generate_layout)
btn_generate.pack(fill=tk.X, pady=(20, 8), padx=20, ipady=10)

btn_select_excluded_qubits = ttk.Button(
    layout_tab,
    text="选择排除比特文件",
    style='File.TButton',
    command=select_excluded_qubits_file
)
btn_select_excluded_qubits.pack(fill=tk.X, pady=8, padx=20, ipady=8)

btn_export = ttk.Button(layout_tab, text="导出不可布线区和引脚坐标", style='Accent.TButton',
                        command=export_forbidden_and_pins)
btn_export.pack(fill=tk.X, pady=8, padx=20, ipady=10)

# === 选项卡3: 布线操作 ===
routing_tab = ttk.Frame(notebook)
notebook.add(routing_tab, text="布线操作")

btn_select_file = ttk.Button(routing_tab, text="选择布线文件", style='File.TButton', command=select_file)
btn_select_file.pack(fill=tk.X, pady=(20, 8), padx=20, ipady=8)

btn_parse_route = ttk.Button(routing_tab, text="执行布线", style='Accent.TButton', command=run_parse_and_route)
btn_parse_route.pack(fill=tk.X, pady=8, padx=20, ipady=10)

btn_delete_lines = ttk.Button(routing_tab, text="删除所有布线", style='Danger.TButton', command=run_delete_all_lines)
btn_delete_lines.pack(fill=tk.X, pady=8, padx=20, ipady=8)

# 进度条区域（默认隐藏）
progress_frame = ttk.Frame(routing_tab)

progress_label = ttk.Label(progress_frame, text="", font=('Helvetica', 10))
progress_label.pack(pady=(0, 5))

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(progress_frame,
                               variable=progress_var,
                               maximum=100,
                               style='TProgressbar',
                               length=300)
progress_bar.pack(fill=tk.X)

# === 右侧内容 ===

# 右上方图片区域
image_frame = ttk.Frame(right_frame, relief=tk.RIDGE, borderwidth=2)
image_frame.pack(fill=tk.X, expand=False, pady=(0, 15))

# 图片区域标题
title_label = ttk.Label(image_frame, text="量子科技长三角产业创新中心",
                        font=('Helvetica', 18, 'bold'), anchor='center')
title_label.pack(pady=12)

# 加载图片
image_path = resource_path("image.png")
try:
    img = Image.open(image_path)
    img = img.resize((320, 320), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    image_label = ttk.Label(image_frame, image=photo)
    image_label.image = photo
    image_label.pack(pady=8)
except Exception as e:
    print(f"图片加载失败: {e}")
    image_label = ttk.Label(image_frame, text="图片加载失败", font=('Helvetica', 14))
    image_label.pack(pady=12)

# 右下方输出区域
output_frame = ttk.LabelFrame(right_frame, text="输出信息", relief=tk.RIDGE, borderwidth=2)
output_frame.pack(fill=tk.BOTH, expand=True)

# 输出文本框
output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=('Courier', 11),
                                        height=10, state='disabled')
output_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

# 重定向stdout到文本框
sys.stdout = TextRedirector(output_text)

# 全局变量
current_design = None
selected_filename = None

# 配置网格权重
param_input_frame.grid_columnconfigure(1, weight=1)


def on_closing():
    sys.stdout = sys.__stdout__
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
