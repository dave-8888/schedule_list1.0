import tkinter as tk
from tkcalendar import DateEntry
from datetime import datetime

class TaskEditorDialog(tk.Toplevel):
    def __init__(self, master, title="任务编辑", name="", due_date=None, callback=None):
        super().__init__(master)
        self.title(title)
        self.callback = callback
        self.resizable(False, False)

        tk.Label(self, text="任务名称：").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.name_entry = tk.Entry(self, width=30)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)
        self.name_entry.insert(0, name)

        tk.Label(self, text="截止时间：").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.due_entry = DateEntry(self, width=27, date_pattern="y-mm-dd")
        self.due_entry.grid(row=1, column=1, padx=10, pady=5)

        if due_date:
            self.due_entry.set_date(due_date)
        else:
            self.due_entry.set_date(datetime.today())  # 临时默认填今天（后面我们改成允许为空）
            self.due_entry.delete(0, 'end')  # 让它显示为空

        self.bind("<Return>", lambda event: self.save())

        tk.Button(self, text="保存", command=self.save).grid(row=2, column=0, columnspan=2, pady=10)

        # ✅ 设置焦点和居中
        self.name_entry.focus_set()
        self.center_window()


    def save(self):
        name = self.name_entry.get().strip()
        due_raw = self.due_entry.get()
        due = due_raw if due_raw else None
        if name and self.callback:
            self.callback(name, due)
            self.destroy()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

