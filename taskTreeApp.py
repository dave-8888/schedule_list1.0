import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from taskEditorDialog import TaskEditorDialog

class TaskTreeApp:
    def __init__(self, root):
        self.root = root
        self._dragging_item = None
        self._dragging_target = None
        self._hover_target_item = None  # 当前悬浮的 item
        self._completed_items = set()
        self.conn = sqlite3.connect("task_tree.db")
        self.create_tables()
        # 添加父任务按钮
        self.toolbar = tk.Frame(root)
        self.toolbar.pack(fill="x", pady=(5,0))
        tk.Button(self.toolbar, text="➕ 添加父任务", command=self.add_parent_task).pack(side="left", padx=20)
        tk.Button(self.toolbar, text="🔽 全部展开", command=self.expand_all).pack(side="left", padx=20)
        tk.Button(self.toolbar, text="🔼 全部折叠", command=self.collapse_all).pack(side="left", padx=20)

        # 创建 Treeview
        self.tree = ttk.Treeview(root, columns=("due","finish"), show="tree headings")
        self.tree.heading("#0", text="任务名称")
        self.tree.heading("due", text="截止时间")
        self.tree.heading("finish", text="完成时间")
        self.tree.column("#0", width=600)
        self.tree.column("due", width=150)
        self.tree.column("finish", width=180)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # 右键菜单
        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="✅ 标记为完成 / 未完成", command=self.toggle_task_completed)
        self.menu.add_command(label="🌱 设置为根任务", command=self.set_as_root_task)
        self.menu.add_separator()
        self.menu.add_command(label="➕ 添加子任务", command=self.add_child_task)
        self.menu.add_command(label="✏️ 修改任务", command=self.edit_task)
        self.menu.add_command(label="❌ 删除任务", command=self.delete_task)

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_drop_sort)
        self.tree.tag_configure("hover", background="#d0eaff")  # 浅蓝色背景
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.tree.bind("<<TreeviewClose>>", self.on_tree_close)

        self.load_tree()

    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                due_date TEXT,
                parent_id INTEGER,
                completed INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                expanded INTEGER DEFAULT 1,  -- 1=展开，0=折叠
                FOREIGN KEY(parent_id) REFERENCES tasks(id)
            )
        ''')
        self.conn.commit()
        # 若旧表中没有 sort_order 字段，尝试添加（避免报错）
        try:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN sort_order INTEGER DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # 字段已存在
        # 若旧表中没有 expanded 字段，尝试添加（避免报错）
        try:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN expanded INTEGER DEFAULT 1")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # 字段已存在
        # 若旧表中没有 finish_time 字段，尝试添加（避免报错）
        try:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN finish_time TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # 字段已存在

    def load_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._completed_items.clear()
        self._load_children(None, "")

    def _load_children(self, parent_id, tree_parent):
        query = """
                SELECT id, name, due_date,finish_time, completed,expanded
                FROM tasks
                WHERE parent_id IS NULL
                ORDER BY sort_order
                """ if parent_id is None else """
                SELECT id, name, due_date,finish_time, completed,expanded
                FROM tasks
                WHERE parent_id = ? 
                ORDER BY sort_order
                """
        cursor = self.conn.execute(query, () if parent_id is None else (parent_id,))
        tasks = cursor.fetchall()

        tasks.sort(key=lambda t: t[4])  # 根据是否完成排序

        for task_id, name, due, finish, completed, expanded in tasks:
            item_id = self.tree.insert(
                tree_parent,
                "end",
                iid=str(task_id),
                text=name,
                values=(due or '', finish or '')
            )
            if completed:
                self.tree.item(item_id, tags=("completed",))
                self._completed_items.add(item_id)  # 记录
            self.tree.item(item_id, open=bool(expanded))  # <---- 恢复展开状态
            # ✅ 修复关键：递归加载子任务
            self._load_children(task_id, item_id)

        self.tree.tag_configure("completed", foreground="gray")


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
        row = self.conn.execute("SELECT name, due_date,finish_time FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row:
            name, due,finish = row
            due_date = datetime.strptime(due, "%Y-%m-%d").date() if due else None
            finish_date = None
            if finish:
                try:
                    finish_date = datetime.strptime(finish, "%Y-%m-%d %H:%M")
                except:
                    finish_date = None
            self.open_task_dialog(title="修改任务", task_id=task_id, name=name, due_date=due_date,finish_date=finish_date)

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = int(selected[0])
        if messagebox.askyesno("确认删除", "是否删除该任务及其所有子任务？"):
            self._delete_recursive(task_id)
            self.conn.commit()
            self.load_tree()

    def set_as_root_task(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = int(selected[0])
        # 更新数据库，将 parent_id 设为 NULL
        self.conn.execute("UPDATE tasks SET parent_id = NULL WHERE id = ?", (task_id,))
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

    def open_task_dialog(self, title, parent_id=None, task_id=None, name="", due_date=None,finish_date=None):
        def on_save(new_name, new_due, new_finish):
            # =============== 日期格式验证 =================
            if new_due:
                try:
                    # 你可以改成其他格式，比如 "%Y/%m/%d"
                    datetime.strptime(new_due, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("截至日期格式错误", "请输入正确的日期格式：YYYY-MM-DD")
                    new_due = None

            if new_finish:
                try:
                    datetime.strptime(new_finish, "%Y-%m-%d %H:%M")
                except:
                    messagebox.showerror("完成日期格式错误", "请输入正确的日期格式：YYYY-MM-DD")
                    finish_date = None
            # =============================================
            if task_id:  # 编辑
                self.conn.execute("UPDATE tasks SET name = ?, due_date = ? , finish_time = ?  WHERE id = ?", (new_name, new_due,new_finish, task_id))
            else:  # 添加
                cursor = self.conn.execute(
                    "SELECT MAX(sort_order) FROM tasks WHERE parent_id IS ?", (parent_id,))
                max_order = cursor.fetchone()[0] or 0
                new_order = max_order + 1
                self.conn.execute("INSERT INTO tasks (name, due_date,finish_time, parent_id,sort_order) VALUES (?, ?, ?,?,?)",
                                  (new_name, new_due,new_finish, parent_id, new_order))
            self.conn.commit()
            self.load_tree()

        TaskEditorDialog(self.root, title=title, name=name, due_date=due_date,finish_time=finish_date, callback=on_save)

    def expand_all(self):
        for item in self.tree.get_children():
            self._expand_recursive(item)

    def _expand_recursive(self, item):
        self.tree.item(item, open=True)
        for child in self.tree.get_children(item):
            self._expand_recursive(child)

    def collapse_all(self):
        for item in self.tree.get_children():
            self._collapse_recursive(item)

    def _collapse_recursive(self, item):
        self.tree.item(item, open=False)
        for child in self.tree.get_children(item):
            self._collapse_recursive(child)




    def toggle_task_completed(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = int(selected[0])
        current = self.conn.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if current is not None:
            new_status = 0 if current[0] else 1
            self._set_task_completed_recursive(task_id, new_status)
            self.conn.commit()
            self.load_tree()

    def _set_task_completed_recursive(self, task_id, status):
        self.conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (status, task_id))
        cursor = self.conn.execute("SELECT id FROM tasks WHERE parent_id = ?", (task_id,))
        for row in cursor.fetchall():
            self._set_task_completed_recursive(row[0], status)

    def on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self._dragging_item = item

    def on_drag_motion(self, event):
        if not self._dragging_item:
            return

        # 找到鼠标当前位置下的 item
        hover_item = self.tree.identify_row(event.y)

        # 如果悬浮在新的目标上
        if hover_item != self._hover_target_item:
            # 清除旧目标的高亮
            if self._hover_target_item:
                self.tree.item(self._hover_target_item, tags=())

            # 设置新目标高亮（但不包括拖动源自己）
            if hover_item and hover_item != self._dragging_item:
                self.tree.item(hover_item, tags=("hover",))
                self._hover_target_item = hover_item
            else:
                self._hover_target_item = None

    def on_drag_drop(self, event):
        if not self._dragging_item:
            return

        target_item = self.tree.identify_row(event.y)
        if target_item and target_item != self._dragging_item:
            dragged_id = int(self._dragging_item)
            target_id = int(target_item)

            # 防止拖动到自己的子节点中，造成递归死循环
            if self._is_descendant(dragged_id, target_id):
                messagebox.showwarning("无效操作", "不能将任务拖动到其子任务下")
            else:
                # 更新数据库
                self.conn.execute("UPDATE tasks SET parent_id = ? WHERE id = ?", (target_id, dragged_id))
                self.conn.commit()
                self.load_tree()

        self._dragging_item = None
        self._dragging_target = None

    def _is_descendant(self, parent_id, possible_child_id):
        # 避免任务拖动到自己的后代节点下
        cursor = self.conn.execute("SELECT id FROM tasks WHERE parent_id = ?", (parent_id,))
        for row in cursor.fetchall():
            child_id = row[0]
            if child_id == possible_child_id:
                return True
            elif self._is_descendant(child_id, possible_child_id):
                return True
        return False


    def on_drag_drop_sort(self, event):
        if not self._dragging_item:
            return
        # 清除悬浮高亮
        if self._hover_target_item:
            self.tree.item(self._hover_target_item, tags=())
            self._hover_target_item = None

        target_item = self.tree.identify_row(event.y)
        if not target_item or target_item == self._dragging_item:
            self._dragging_item = None
            return

        drag_id = int(self._dragging_item)
        target_id = int(target_item)

        # 确保是同一父级
        drag_parent = self.conn.execute("SELECT parent_id FROM tasks WHERE id = ?", (drag_id,)).fetchone()[0]
        target_parent = self.conn.execute("SELECT parent_id FROM tasks WHERE id = ?", (target_id,)).fetchone()[0]
        if drag_parent != target_parent:
            # messagebox.showwarning("跨层级拖动无效", "只能在同一层级排序。")
            # self._dragging_item = None
            # return
            self.on_drag_drop(event)
            self._dragging_item = None
            return

        # 获取两者排序值并交换
        drag_order = self.conn.execute("SELECT sort_order FROM tasks WHERE id = ?", (drag_id,)).fetchone()[0]
        target_order = self.conn.execute("SELECT sort_order FROM tasks WHERE id = ?", (target_id,)).fetchone()[0]

        self.conn.execute("UPDATE tasks SET sort_order = ? WHERE id = ?", (target_order, drag_id))
        self.conn.execute("UPDATE tasks SET sort_order = ? WHERE id = ?", (drag_order, target_id))
        self.conn.commit()
        self.load_tree()
        self._dragging_item = None

    def _record_expanded_state(self):
        def record_recursive(item_id):
            task_id = int(item_id)
            is_open = int(self.tree.item(item_id, "open"))
            self.conn.execute("UPDATE tasks SET expanded = ? WHERE id = ?", (is_open, task_id))
            for child in self.tree.get_children(item_id):
                record_recursive(child)

        for top_item in self.tree.get_children():
            record_recursive(top_item)

        self.conn.commit()

    def on_tree_open(self, event):
        item_id = self.tree.focus()
        if item_id:
            self.conn.execute("UPDATE tasks SET expanded = 1 WHERE id = ?", (int(item_id),))
            self.conn.commit()

    def on_tree_close(self, event):
        item_id = self.tree.focus()
        if item_id:
            self.conn.execute("UPDATE tasks SET expanded = 0 WHERE id = ?", (int(item_id),))
            self.conn.commit()




