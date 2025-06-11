import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
import datetime


class TaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("任务列表管理")

        self.conn = sqlite3.connect("tasks.db")
        self.create_tables()

        self.setup_ui()
        self.load_parent_lists()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                due_date TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER,
                name TEXT NOT NULL,
                due_date TEXT,
                FOREIGN KEY(list_id) REFERENCES task_lists(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def setup_ui(self):
        # 父任务区域
        frame_top = ttk.LabelFrame(self.root, text="父任务列表")
        frame_top.pack(fill="x", padx=10, pady=5)

        self.parent_name = tk.StringVar()
        self.parent_due = tk.StringVar()
        tk.Entry(frame_top, textvariable=self.parent_name, width=30).pack(side="left", padx=5)
        self.parent_due_picker = DateEntry(frame_top, textvariable=self.parent_due, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.parent_due_picker.pack(side="left", padx=5)
        tk.Button(frame_top, text="添加父任务", command=self.add_parent_task).pack(side="left", padx=5)

        # 父列表选择与子任务区域
        frame_middle = ttk.LabelFrame(self.root, text="子任务列表")
        frame_middle.pack(fill="both", expand=True, padx=10, pady=5)

        self.parent_combo = ttk.Combobox(frame_middle, state="readonly")
        self.parent_combo.pack(pady=5)
        self.parent_combo.bind("<<ComboboxSelected>>", lambda e: self.load_child_tasks())

        self.tree = ttk.Treeview(frame_middle, columns=("名称", "截止时间"), show="headings")
        self.tree.heading("名称", text="任务名称")
        self.tree.heading("截止时间", text="截止时间")
        self.tree.pack(fill="both", expand=True, pady=5)

        # 添加子任务输入
        self.child_name = tk.StringVar()
        self.child_due = tk.StringVar()

        tk.Entry(frame_middle, textvariable=self.child_name, width=30).pack(side="left", padx=5)
        self.child_due_picker = DateEntry(frame_middle, textvariable=self.child_due, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.child_due_picker.pack(side="left", padx=5)
        tk.Button(frame_middle, text="添加子任务", command=self.add_child_task).pack(side="left", padx=5)

    def add_parent_task(self):
        name = self.parent_name.get().strip()
        due = self.parent_due.get().strip()
        if not name:
            messagebox.showwarning("输入错误", "任务名称不能为空")
            return
        self.conn.execute("INSERT INTO task_lists (name, due_date) VALUES (?, ?)", (name, due))
        self.conn.commit()
        self.parent_name.set("")
        self.load_parent_lists()

    def load_parent_lists(self):
        cursor = self.conn.execute("SELECT id, name, due_date FROM task_lists")
        self.parent_data = cursor.fetchall()
        self.parent_combo['values'] = [f"{row[1]} (截至: {row[2]})" for row in self.parent_data]
        self.parent_combo.set("选择父任务")

    def load_child_tasks(self):
        self.tree.delete(*self.tree.get_children())
        idx = self.parent_combo.current()
        if idx < 0:
            return
        parent_id = self.parent_data[idx][0]
        cursor = self.conn.execute("SELECT name, due_date FROM tasks WHERE list_id = ?", (parent_id,))
        for row in cursor.fetchall():
            self.tree.insert('', tk.END, values=row)

    def add_child_task(self):
        idx = self.parent_combo.current()
        if idx < 0:
            messagebox.showwarning("请选择父任务", "请先选择一个父任务列表")
            return
        list_id = self.parent_data[idx][0]
        name = self.child_name.get().strip()
        due = self.child_due.get().strip()
        if not name:
            messagebox.showwarning("输入错误", "任务名称不能为空")
            return
        self.conn.execute("INSERT INTO tasks (list_id, name, due_date) VALUES (?, ?, ?)", (list_id, name, due))
        self.conn.commit()
        self.child_name.set("")
        self.load_child_tasks()


if __name__ == "__main__":
    try:
        import tkcalendar
    except ImportError:
        print("请先安装 tkcalendar：pip install tkcalendar")
        exit()

    root = tk.Tk()
    app = TaskApp(root)
    root.mainloop()
