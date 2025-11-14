import tkinter as tk
from tkinter import font, ttk

from taskTreeApp import TaskTreeApp
from screeninfo import get_monitors





if __name__ == "__main__":
    for m in get_monitors():
        print(m)
    win_width = 800
    win_hegiht = 600
    root = tk.Tk()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - win_width) // 2
    y = (sh - win_hegiht) // 2
    root.geometry(f"{win_width}x{win_hegiht}+{x}+{y}")
    root.wm_minsize(win_width,win_hegiht)

    default_font = font.nametofont('TkDefaultFont')
    default_font.configure(size=12)
    root.option_add('*Font', default_font)
    root.title("任务清单")
    tree_style = ttk.Style()
    tree_style.configure("Treeview", font=default_font)
    tree_style.configure("Treeview.Heading", font=default_font)
    app = TaskTreeApp(root)
    root.mainloop()
