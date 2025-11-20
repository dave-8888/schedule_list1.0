import tkinter as tk
from tkcalendar import DateEntry
from datetime import datetime

class TaskEditorDialog(tk.Toplevel):
    def __init__(self, master, title="任务编辑", name="", due_date=None, finish_time=None, callback=None):
        super().__init__(master)
        self.center_window()
        self.title(title)
        self.callback = callback
        self.resizable(False, False)

        # ---- 任务名称 ----
        tk.Label(self, text="任务名称").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.name_entry = tk.Entry(self, width=22, justify="left")
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.name_entry.insert(0, name)

        # ---- 截止日期 ----
        tk.Label(self, text="截止时间").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.due_entry = DateEntry(self, width=20, date_pattern="y-mm-dd")
        self.due_entry.grid(row=1, column=1, padx=5, pady=5)

        if due_date:
            self.due_entry.set_date(due_date)
        else:
            self.due_entry.set_date(datetime.today())
            self.due_entry.delete(0, 'end')  # 允许为空

        # ---- 完成时间 日期 + 时分 ----
        tk.Label(self, text="完成时间").grid(row=2, column=0, padx=10, pady=5, sticky="e")

        frame_finish = tk.Frame(self)
        frame_finish.grid(row=2, column=1, padx=5, pady=5)

        # 日期
        self.finish_date = DateEntry(frame_finish, width=12, date_pattern="y-mm-dd")
        self.finish_date.grid(row=0, column=0)

        # 时
        self.hour_spin = tk.Spinbox(frame_finish, from_=0, to=23, width=3, format="%02.0f")
        self.hour_spin.grid(row=0, column=1, padx=3)

        # 分
        self.minute_spin = tk.Spinbox(frame_finish, from_=0, to=59, width=3, format="%02.0f")
        self.minute_spin.grid(row=0, column=2, padx=3)

        # ---- 完成时间初始化 ----
        if finish_time:
            if isinstance(finish_time, str):
                dt = datetime.strptime(finish_time, "%Y-%m-%d %H:%M")
            else:  # 已经是 datetime 对象
                dt = finish_time
            self.finish_date.set_date(dt.date())
            self.hour_spin.delete(0, 'end')
            self.hour_spin.insert(0, dt.strftime("%H"))
            self.minute_spin.delete(0, 'end')
            self.minute_spin.insert(0, dt.strftime("%M"))
        else:
            # 默认留空
            self.finish_date.set_date(datetime.today())
            self.finish_date.delete(0, 'end')
            self.hour_spin.delete(0, 'end')
            self.minute_spin.delete(0, 'end')

        # ---- 按钮 ----
        self.bind("<Return>", lambda event: self.save())
        tk.Button(self, text=" 保 存 ", command=self.save).grid(row=3, column=0, columnspan=2, pady=10)

        self.name_entry.focus_set()

    def save(self):
        name = self.name_entry.get().strip()

        # 截止时间
        due_raw = self.due_entry.get()
        due = due_raw if due_raw else None

        # 完成日期
        finish_date_raw = self.finish_date.get()

        # 完成时间（可以为空）
        hour = self.hour_spin.get()
        minute = self.minute_spin.get()

        # 如果日期为空 → 完全为空
        if not finish_date_raw:
            finish = None
        else:
            # 如果时分为空 → 默认 00:00
            hour = hour if hour else "00"
            minute = minute if minute else "00"
            finish = f"{finish_date_raw} {hour}:{minute}"

        if name and self.callback:
            self.callback(name, due, finish)
            self.destroy()

    def center_window(self, w=360, h=230):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
