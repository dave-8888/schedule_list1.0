import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime

class TaskTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("任务树管理器")

        self.conn = sqlite3.connect("task_tree.db")
        self.create_tables()

        # 设置 Treeview 两列：任务名称、截止时间
        self.tree = ttk.Treeview(root, columns=("due",), show="tree headings")
        self.tree.heading("#0", text="任务名称")  # Tree 列（左侧带缩进）
        self.tree.heading("due", text="截止时间")  # 第二列
        self.tree.column("#0", width=200)
        self.tree.column("due", width=100)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # 添加右侧输入框
        self.form_frame = tk.Frame(root)
        self.form_frame.pack(side="right", fill="y", padx=5, pady=5)

        tk.Label(self.form_frame, text="任务名称").pack()
        self.task_name = tk.Entry(self.form_frame)
        self.task_name.pack()

        tk.Label(self.form_frame, text="截止时间").pack()
        self.task_due = DateEntry(self.form_frame, width=16)
        self.task_due.pack()

        tk.Button(self.form_frame, text="添加为父任务", command=self.add_parent_task).pack(pady=5)
        tk.Button(self.form_frame, text="添加为子任务", command=self.add_child_task).pack(pady=5)
        tk.Button(self.form_frame, text="保存修改", command=self.update_task).pack(pady=5)
        tk.Button(self.form_frame, text="删除任务", command=self.delete_task).pack(pady=5)

        self.selected_item_id = None
        self.load_tree()

    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                due_date TEXT,
                parent_id INTEGER,
                FOREIGN KEY(parent_id) REFERENCES tasks(id)
            )
        ''')
        self.conn.commit()

    def load_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._load_children(None, "")

    def _load_children(self, parent_id, tree_parent):
        query = "SELECT id, name, due_date FROM tasks WHERE parent_id IS NULL" if parent_id is None \
            else "SELECT id, name, due_date FROM tasks WHERE parent_id = ?"
        cursor = self.conn.execute(query, () if parent_id is None else (parent_id,))
        for row in cursor.fetchall():
            task_id, name, due = row
            item_id = self.tree.insert(tree_parent, "end", iid=str(task_id), text=name, values=(due,))
            self._load_children(task_id, item_id)

    def add_parent_task(self):
        name = self.task_name.get().strip()
        due = self.task_due.get_date().isoformat()
        if not name:
            return
        self.conn.execute("INSERT INTO tasks (name, due_date, parent_id) VALUES (?, ?, NULL)", (name, due))
        self.conn.commit()
        self.load_tree()

    def add_child_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个父任务节点")
            return
        parent_id = int(selected[0])
        name = self.task_name.get().strip()
        due = self.task_due.get_date().isoformat()
        if not name:
            return
        self.conn.execute("INSERT INTO tasks (name, due_date, parent_id) VALUES (?, ?, ?)", (name, due, parent_id))
        self.conn.commit()
        self.load_tree()

    def on_tree_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        self.selected_item_id = item_id
        name = self.tree.item(item_id, "text")
        due_str = self.conn.execute("SELECT due_date FROM tasks WHERE id = ?", (item_id,)).fetchone()[0]

        self.task_name.delete(0, tk.END)
        self.task_name.insert(0, name)
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
            self.task_due.set_date(due_date)
        except Exception as e:
            print("日期解析错误:", due_str, e)

    def update_task(self):
        if not self.selected_item_id:
            return
        name = self.task_name.get().strip()
        due = self.task_due.get_date().isoformat()
        self.conn.execute("UPDATE tasks SET name = ?, due_date = ? WHERE id = ?", (name, due, self.selected_item_id))
        self.conn.commit()
        self.selected_item_id = None
        self.load_tree()

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = int(selected[0])
        if messagebox.askyesno("确认", "删除任务将同时删除其所有子任务，是否继续？"):
            self._delete_recursive(task_id)
            self.conn.commit()
            self.load_tree()

    def _delete_recursive(self, task_id):
        cursor = self.conn.execute("SELECT id FROM tasks WHERE parent_id = ?", (task_id,))
        for row in cursor.fetchall():
            self._delete_recursive(row[0])
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


if __name__ == "__main__":
    try:
        import tkcalendar
    except ImportError:
        print("请先安装 tkcalendar：pip install tkcalendar")
        exit()

    root = tk.Tk()
    app = TaskTreeApp(root)
    root.mainloop()
