import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import sqlite3
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

        # ✅ 绑定回车键
        self.bind("<Return>", lambda event: self.save())

        tk.Button(self, text="保存", command=self.save).grid(row=2, column=0, columnspan=2, pady=10)

    def save(self):
        name = self.name_entry.get().strip()
        due = self.due_entry.get_date().isoformat()
        if name and self.callback:
            self.callback(name, due)
            self.destroy()


class TaskTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("任务列表树")

        self.conn = sqlite3.connect("task_tree.db")
        self.create_tables()

        # 添加父任务按钮
        self.toolbar = tk.Frame(root)
        self.toolbar.pack(fill="x", pady=(5, 0))
        tk.Button(self.toolbar, text="➕ 添加父任务", command=self.add_parent_task).pack(side="left", padx=10)

        # 创建 Treeview
        self.tree = ttk.Treeview(root, columns=("due",), show="tree headings")
        self.tree.heading("#0", text="任务名称")
        self.tree.heading("due", text="截止时间")
        self.tree.column("#0", width=200)
        self.tree.column("due", width=100)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # 右键菜单
        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="➕ 添加子任务", command=self.add_child_task)
        self.menu.add_command(label="✏️ 修改任务", command=self.edit_task)
        self.menu.add_command(label="🗑️ 删除任务", command=self.delete_task)

        self.tree.bind("<Button-3>", self.show_context_menu)
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
        self.open_task_dialog(title="添加父任务", parent_id=None)

    def add_child_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个任务节点")
            return
        parent_id = int(selected[0])
        self.open_task_dialog(title="添加子任务", parent_id=parent_id)

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = int(selected[0])
        row = self.conn.execute("SELECT name, due_date FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row:
            name, due = row
            due_date = datetime.strptime(due, "%Y-%m-%d").date() if due else None
            self.open_task_dialog(title="修改任务", task_id=task_id, name=name, due_date=due_date)

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = int(selected[0])
        if messagebox.askyesno("确认删除", "是否删除该任务及其所有子任务？"):
            self._delete_recursive(task_id)
            self.conn.commit()
            self.load_tree()

    def _delete_recursive(self, task_id):
        cursor = self.conn.execute("SELECT id FROM tasks WHERE parent_id = ?", (task_id,))
        for row in cursor.fetchall():
            self._delete_recursive(row[0])
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def show_context_menu(self, event):
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            self.menu.post(event.x_root, event.y_root)

    def open_task_dialog(self, title, parent_id=None, task_id=None, name="", due_date=None):
        def on_save(new_name, new_due):
            if task_id:  # 编辑
                self.conn.execute("UPDATE tasks SET name = ?, due_date = ? WHERE id = ?", (new_name, new_due, task_id))
            else:  # 添加
                self.conn.execute("INSERT INTO tasks (name, due_date, parent_id) VALUES (?, ?, ?)",
                                  (new_name, new_due, parent_id))
            self.conn.commit()
            self.load_tree()

        TaskEditorDialog(self.root, title=title, name=name, due_date=due_date, callback=on_save)

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskTreeApp(root)
    root.mainloop()
