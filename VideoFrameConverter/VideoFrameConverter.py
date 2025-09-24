#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转序列帧工具
基于FFmpeg的可视化界面工具，用于将视频文件批量转换为序列帧
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinterdnd2 as tkdnd
import subprocess
import os
import threading
import re
import json
from pathlib import Path


class VideoFrameConverter:
    def __init__(self):
        self.root = tkdnd.Tk()  # 支持拖拽的根窗口
        self.root.title("视频转序列帧工具")
        self.root.geometry("800x700")
        self.root.configure(bg='#f5f5f5')
        
        # 设置窗口图标和样式
        self.setup_styles()
        
        # 变量初始化
        self.video_file = None
        self.original_fps = None
        self.conversion_process = None
        self.is_converting = False
        
        # 创建变量
        self.setup_variables()
        
        # 检查FFmpeg
        self.check_ffmpeg()
        
        # 创建界面
        self.create_interface()
        
        # 绑定事件
        self.bind_events()
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 设置主题
        style.theme_use('clam')
        
        # 自定义样式
        style.configure('Title.TFrame', background='#2c3e50')
        style.configure('Title.TLabel', background='#2c3e50', foreground='white', 
                       font=('Microsoft YaHei', 12))
        style.configure('Section.TFrame', background='white', relief='solid', borderwidth=1)
        style.configure('Config.TLabel', font=('Microsoft YaHei', 9))
        style.configure('Start.TButton', font=('Microsoft YaHei', 11, 'bold'))
    
    def setup_variables(self):
        """初始化界面变量"""
        self.fps_var = tk.StringVar(value="30")
        self.format_var = tk.StringVar(value="png")
        self.prefix_var = tk.StringVar(value="")
        self.start_num_var = tk.StringVar(value="1")
        self.digits_var = tk.StringVar(value="3")
        self.output_folder_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="等待开始转换")
        self.progress_var = tk.DoubleVar(value=0)
    
    def check_ffmpeg(self):
        """检查FFmpeg是否安装"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("FFmpeg检测成功")
            else:
                raise FileNotFoundError
        except (FileNotFoundError, subprocess.TimeoutExpired):
            messagebox.showerror("错误", "请先安装FFmpeg并配置环境变量\n"
                               "下载地址: https://ffmpeg.org/download.html")
    
    def create_interface(self):
        """创建主界面"""
        # 标题栏
        self.create_title_bar()
        
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 视频导入区
        self.create_import_section(main_frame)
        
        # 参数配置区
        self.create_config_section(main_frame)
        
        # 操作状态区
        self.create_action_section(main_frame)
    
    def create_title_bar(self):
        """创建标题栏"""
        title_frame = ttk.Frame(self.root, style='Title.TFrame')
        title_frame.pack(fill='x', padx=0, pady=0)
        
        title_label = ttk.Label(title_frame, text="视频转序列帧工具", 
                               style='Title.TLabel')
        title_label.pack(side='left', padx=15, pady=10)
        
        # 窗口控制按钮（装饰性）
        controls_frame = ttk.Frame(title_frame, style='Title.TFrame')
        controls_frame.pack(side='right', padx=15, pady=10)
        
        minimize_btn = tk.Button(controls_frame, text="—", width=3, height=1,
                                relief='flat', bg='#f39c12', fg='white',
                                command=self.root.iconify)
        minimize_btn.pack(side='left', padx=2)
        
        close_btn = tk.Button(controls_frame, text="✕", width=3, height=1,
                             relief='flat', bg='#e74c3c', fg='white',
                             command=self.root.quit)
        close_btn.pack(side='left', padx=2)
    
    def create_import_section(self, parent):
        """创建视频导入区"""
        import_frame = ttk.Frame(parent, style='Section.TFrame')
        import_frame.pack(fill='both', expand=True, pady=10)
        
        # 拖拽区域
        self.drop_frame = tk.Frame(import_frame, bg='#f8f9fa', 
                                  relief='solid', bd=2, height=150)
        self.drop_frame.pack(fill='x', padx=20, pady=20)
        self.drop_frame.pack_propagate(False)
        
        # 拖拽提示文字
        self.drop_label = tk.Label(self.drop_frame, 
                                  text="拖放视频文件到此处，或点击下方按钮选择",
                                  bg='#f8f9fa', fg='#7f8c8d', 
                                  font=('Microsoft YaHei', 10))
        self.drop_label.pack(expand=True)
        
        # 选择文件按钮
        select_btn = ttk.Button(import_frame, text="选择视频文件",
                               command=self.select_video_file)
        select_btn.pack(pady=10)
        
        # 导入成功显示区
        self.success_frame = ttk.Frame(import_frame)
        self.success_frame.pack(pady=10)
        
        self.filename_label = ttk.Label(self.success_frame, text="", 
                                       font=('Microsoft YaHei', 10, 'bold'))
        self.filename_label.pack()
        
        self.fps_label = ttk.Label(self.success_frame, text="", 
                                  font=('Microsoft YaHei', 9), foreground='#7f8c8d')
        self.fps_label.pack()
        
        # 配置拖拽
        self.drop_frame.drop_target_register(tkdnd.DND_FILES)
        self.drop_frame.dnd_bind('<<DropEnter>>', self.on_drag_enter)
        self.drop_frame.dnd_bind('<<DropLeave>>', self.on_drag_leave)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
    
    def create_config_section(self, parent):
        """创建参数配置区"""
        config_frame = ttk.Frame(parent, style='Section.TFrame')
        config_frame.pack(fill='both', expand=True, pady=10)
        
        # 配置网格
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 左侧参数
        left_frame = ttk.Frame(config_grid)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        # 帧率设置
        self.create_fps_config(left_frame)
        
        # 文件名前缀
        self.create_prefix_config(left_frame)
        
        # 序号设置
        self.create_sequence_config(left_frame)
        
        # 右侧参数
        right_frame = ttk.Frame(config_grid)
        right_frame.pack(side='right', fill='both', expand=True, padx=(15, 0))
        
        # 输出格式
        self.create_format_config(right_frame)
        
        # 输出文件夹
        self.create_folder_config(right_frame)
        
        # 参数预览
        self.create_preview_section(right_frame)
    
    def create_fps_config(self, parent):
        """创建帧率配置"""
        fps_frame = ttk.LabelFrame(parent, text="帧率设置", padding=10)
        fps_frame.pack(fill='x', pady=5)
        
        fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_var, width=15)
        fps_entry.pack(side='left')
        
        ttk.Label(fps_frame, text="fps").pack(side='left', padx=(5, 0))
    
    def create_prefix_config(self, parent):
        """创建前缀配置"""
        prefix_frame = ttk.LabelFrame(parent, text="文件名前缀", padding=10)
        prefix_frame.pack(fill='x', pady=5)
        
        prefix_entry = ttk.Entry(prefix_frame, textvariable=self.prefix_var)
        prefix_entry.pack(fill='x')
    
    def create_sequence_config(self, parent):
        """创建序号配置"""
        seq_frame = ttk.LabelFrame(parent, text="序号设置", padding=10)
        seq_frame.pack(fill='x', pady=5)
        
        # 起始序号
        start_frame = ttk.Frame(seq_frame)
        start_frame.pack(fill='x', pady=2)
        
        ttk.Label(start_frame, text="起始序号:").pack(side='left')
        start_entry = ttk.Entry(start_frame, textvariable=self.start_num_var, width=10)
        start_entry.pack(side='right')
        
        # 序号位数
        digits_frame = ttk.Frame(seq_frame)
        digits_frame.pack(fill='x', pady=2)
        
        ttk.Label(digits_frame, text="序号位数:").pack(side='left')
        digits_combo = ttk.Combobox(digits_frame, textvariable=self.digits_var,
                                   values=['2', '3', '4', '5'], width=8, state='readonly')
        digits_combo.pack(side='right')
    
    def create_format_config(self, parent):
        """创建格式配置"""
        format_frame = ttk.LabelFrame(parent, text="输出格式", padding=10)
        format_frame.pack(fill='x', pady=5)
        
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var,
                                   values=['png', 'jpg', 'jpeg'], state='readonly')
        format_combo.pack(fill='x')
    
    def create_folder_config(self, parent):
        """创建文件夹配置"""
        folder_frame = ttk.LabelFrame(parent, text="输出文件夹", padding=10)
        folder_frame.pack(fill='x', pady=5)
        
        folder_entry_frame = ttk.Frame(folder_frame)
        folder_entry_frame.pack(fill='x')
        
        self.folder_entry = ttk.Entry(folder_entry_frame, textvariable=self.output_folder_var)
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        browse_btn = ttk.Button(folder_entry_frame, text="浏览", 
                               command=self.select_output_folder)
        browse_btn.pack(side='right', padx=(5, 0))
        
        # 提示信息
        self.folder_tip = ttk.Label(folder_frame, text="请选择输出文件夹", 
                                   foreground='red', font=('Microsoft YaHei', 8))
        self.folder_tip.pack(anchor='w', pady=(5, 0))
    
    def create_preview_section(self, parent):
        """创建预览区"""
        preview_frame = ttk.LabelFrame(parent, text="参数预览", padding=10)
        preview_frame.pack(fill='x', pady=5)
        
        preview_bg = tk.Frame(preview_frame, bg='#f8f9fa', relief='solid', bd=1)
        preview_bg.pack(fill='x', pady=5)
        
        ttk.Label(preview_bg, text="文件名示例:", background='#f8f9fa',
                 font=('Microsoft YaHei', 8)).pack(anchor='w', padx=10, pady=(5, 0))
        
        self.preview_label = ttk.Label(preview_bg, text="001.png", background='#f8f9fa',
                                      font=('Microsoft YaHei', 10, 'bold'))
        self.preview_label.pack(anchor='w', padx=10, pady=(0, 5))
    
    def create_action_section(self, parent):
        """创建操作状态区"""
        action_frame = ttk.Frame(parent, style='Section.TFrame')
        action_frame.pack(fill='both', expand=True, pady=10)
        
        # 进度条
        self.progress_frame = ttk.Frame(action_frame)
        self.progress_frame.pack(pady=20)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, 
                                          mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(pady=5)
        
        # 状态文字
        self.status_label = ttk.Label(action_frame, textvariable=self.status_var,
                                     font=('Microsoft YaHei', 9))
        self.status_label.pack(pady=10)
        
        # 按钮组
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(button_frame, text="开始转换", 
                                   style='Start.TButton', command=self.start_conversion)
        self.start_btn.pack(side='left', padx=10)
        
        self.cancel_btn = ttk.Button(button_frame, text="取消转换", 
                                    command=self.cancel_conversion, state='disabled')
        self.cancel_btn.pack(side='left', padx=10)
        
        # 初始状态
        self.progress_frame.pack_forget()
    
    def bind_events(self):
        """绑定事件"""
        # 参数变化时更新预览
        for var in [self.prefix_var, self.start_num_var, self.digits_var, 
                   self.format_var]:
            var.trace('w', self.update_preview)
        
        # 输出文件夹变化时检查按钮状态
        self.output_folder_var.trace('w', self.check_start_button)
        
        # 初始预览
        self.update_preview()
        self.check_start_button()
    
    def on_drag_enter(self, event):
        """拖拽进入"""
        self.drop_frame.configure(bg='#ebf3fd', relief='solid', bd=2)
        self.drop_label.configure(bg='#ebf3fd')
    
    def on_drag_leave(self, event):
        """拖拽离开"""
        self.drop_frame.configure(bg='#f8f9fa', relief='solid', bd=2)
        self.drop_label.configure(bg='#f8f9fa')
    
    def on_drop(self, event):
        """拖拽释放"""
        files = self.root.tk.splitlist(event.data)
        if files:
            self.load_video_file(files[0])
        self.on_drag_leave(event)
    
    def select_video_file(self):
        """选择视频文件"""
        filetypes = [
            ('视频文件', '*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm'),
            ('所有文件', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=filetypes
        )
        
        if filename:
            self.load_video_file(filename)
    
    def load_video_file(self, filepath):
        """加载视频文件"""
        self.video_file = filepath
        
        # 显示文件名
        filename = os.path.basename(filepath)
        self.filename_label.configure(text=filename)
        
        # 获取视频信息
        try:
            fps = self.get_video_fps(filepath)
            if fps:
                self.original_fps = fps
                self.fps_var.set(str(fps))
                self.fps_label.configure(text=f"原视频帧率：{fps}fps")
            else:
                self.fps_label.configure(text="无法获取视频帧率")
        except Exception as e:
            self.fps_label.configure(text=f"获取视频信息失败：{str(e)}")
        
        # 更新界面状态
        self.check_start_button()
    
    def get_video_fps(self, filepath):
        """获取视频帧率"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0',
                filepath
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                fps_str = result.stdout.strip()
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den)
                else:
                    fps = float(fps_str)
                return round(fps, 2)
        except Exception as e:
            print(f"获取帧率失败：{e}")
        
        return None
    
    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder_var.set(folder)
    
    def update_preview(self, *args):
        """更新参数预览"""
        try:
            prefix = self.prefix_var.get()
            start_num = int(self.start_num_var.get() or 1)
            digits = int(self.digits_var.get())
            format_ext = self.format_var.get()
            
            # 生成序号
            padded_num = str(start_num).zfill(digits)
            
            # 生成文件名
            filename = f"{prefix}{padded_num}.{format_ext}"
            self.preview_label.configure(text=filename)
        except ValueError:
            self.preview_label.configure(text="参数错误")
    
    def check_start_button(self, *args):
        """检查开始按钮状态"""
        if self.video_file and self.output_folder_var.get().strip():
            self.start_btn.configure(state='normal')
            self.folder_tip.pack_forget()
        else:
            self.start_btn.configure(state='disabled')
            if not self.output_folder_var.get().strip():
                self.folder_tip.pack(anchor='w', pady=(5, 0))
    
    def start_conversion(self):
        """开始转换"""
        if self.is_converting:
            return
        
        # 验证参数
        if not self.validate_parameters():
            return
        
        # 更新界面状态
        self.is_converting = True
        self.start_btn.configure(state='disabled')
        self.cancel_btn.configure(state='normal')
        self.progress_frame.pack(pady=20)
        self.progress_var.set(0)
        self.status_var.set("准备转换...")
        
        # 在新线程中执行转换
        conversion_thread = threading.Thread(target=self.run_conversion)
        conversion_thread.daemon = True
        conversion_thread.start()
    
    def validate_parameters(self):
        """验证转换参数"""
        try:
            fps = float(self.fps_var.get())
            if fps <= 0:
                messagebox.showerror("参数错误", "帧率必须大于0")
                return False
            
            start_num = int(self.start_num_var.get())
            if start_num < 0:
                messagebox.showerror("参数错误", "起始序号不能为负数")
                return False
            
            # 检查输出文件夹是否存在
            output_folder = self.output_folder_var.get()
            if not os.path.exists(output_folder):
                try:
                    os.makedirs(output_folder)
                except Exception as e:
                    messagebox.showerror("错误", f"创建输出文件夹失败：{str(e)}")
                    return False
            
            return True
            
        except ValueError as e:
            messagebox.showerror("参数错误", "请检查数字参数的格式")
            return False
    
    def run_conversion(self):
        """执行转换（在后台线程中运行）"""
        try:
            # 构建FFmpeg命令
            output_pattern = self.build_output_pattern()
            fps = self.fps_var.get()
            
            cmd = [
                'ffmpeg', '-i', self.video_file,
                '-r', fps,
                '-y',  # 覆盖输出文件
                output_pattern
            ]
            
            # 获取视频总帧数用于进度计算
            total_frames = self.get_total_frames()
            
            # 设置环境变量以处理中文编码
            my_env = os.environ.copy()
            my_env["PYTHONIOENCODING"] = "utf-8"
            
            # 启动FFmpeg进程，使用utf-8编码处理输出
            self.conversion_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=my_env,
                encoding='utf-8',
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # 隐藏命令行窗口
            )
            
            # 添加额外的FFmpeg参数来处理ICC配置
            cmd.extend([
                '-sws_flags', 'spline+accurate_rnd+full_chroma_int',
                '-pix_fmt', 'rgb24'  # 使用标准RGB颜色空间
            ])
            
            # 监控进度
            self.monitor_progress(total_frames)
            
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))
    
    def build_output_pattern(self):
        """构建输出文件名模式"""
        output_folder = self.output_folder_var.get()
        prefix = self.prefix_var.get()
        start_num = int(self.start_num_var.get())
        digits = int(self.digits_var.get())
        format_ext = self.format_var.get()
        
        # FFmpeg的序号从1开始，我们需要调整
        pattern = f"{prefix}%0{digits}d.{format_ext}"
        if start_num != 1:
            # 如果起始序号不是1，需要特殊处理
            pattern = f"{prefix}{start_num:0{digits}d}.{format_ext}"
        
        return os.path.join(output_folder, pattern)
    
    def get_total_frames(self):
        """获取视频总帧数"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=nb_frames', '-of', 'csv=p=0',
                self.video_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
        except:
            pass
        
        return 0
    
    def monitor_progress(self, total_frames):
        """监控转换进度"""
        frame_count = 0
        
        while self.conversion_process and self.conversion_process.poll() is None:
            try:
                output = self.conversion_process.stdout.readline()
                if output:
                    # 解析FFmpeg输出中的帧数信息
                    frame_match = re.search(r'frame=\s*(\d+)', output)
                    if frame_match:
                        frame_count = int(frame_match.group(1))
                        
                        if total_frames > 0:
                            progress = (frame_count / total_frames) * 100
                            progress = min(progress, 100)
                        else:
                            progress = 0
                        
                        # 更新界面
                        self.root.after(0, lambda: self.update_progress(progress, frame_count))
                
            except Exception as e:
                print(f"监控进度错误：{e}")
                break
        
        # 转换完成
        if self.conversion_process:
            return_code = self.conversion_process.returncode
            self.root.after(0, lambda: self.conversion_finished(return_code, frame_count))
    
    def update_progress(self, progress, frame_count):
        """更新进度显示"""
        self.progress_var.set(progress)
        self.status_var.set(f"转换中... {progress:.1f}% (已处理 {frame_count} 帧)")
    
    def conversion_finished(self, return_code, frame_count):
        """转换完成"""
        self.is_converting = False
        self.conversion_process = None
        
        if return_code == 0:
            self.status_var.set(f"转换完成，共生成 {frame_count} 帧")
            self.progress_var.set(100)
            
            # 显示完成对话框
            result = messagebox.showinfo(
                "转换完成", 
                f"转换完成，共生成 {frame_count} 帧\n是否打开输出文件夹？",
                type='yesno'
            )
            
            if result == 'yes':
                self.open_output_folder()
        else:
            self.status_var.set("转换失败")
            messagebox.showerror("转换失败", "FFmpeg转换过程中出现错误")
        
        # 重置界面状态
        self.start_btn.configure(state='normal')
        self.cancel_btn.configure(state='disabled')
    
    def conversion_error(self, error_msg):
        """转换出错"""
        self.is_converting = False
        self.conversion_process = None
        self.status_var.set("转换失败")
        messagebox.showerror("转换失败", f"转换过程中出现错误：\n{error_msg}")
        
        # 重置界面状态
        self.start_btn.configure(state='normal')
        self.cancel_btn.configure(state='disabled')
    
    def cancel_conversion(self):
        """取消转换"""
        if self.conversion_process:
            try:
                self.conversion_process.terminate()
                self.conversion_process = None
            except:
                pass
        
        self.is_converting = False
        self.status_var.set("转换已取消")
        self.start_btn.configure(state='normal')
        self.cancel_btn.configure(state='disabled')
        self.progress_var.set(0)
    
    def open_output_folder(self):
        """打开输出文件夹"""
        output_folder = self.output_folder_var.get()
        if os.path.exists(output_folder):
            if os.name == 'nt':  # Windows
                os.startfile(output_folder)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.Popen(['open', output_folder])
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


if __name__ == "__main__":
    app = VideoFrameConverter()
    app.run()
