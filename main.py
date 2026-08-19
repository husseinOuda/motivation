import customtkinter as ctk
import json
from datetime import datetime
from datetime import datetime, date
from tkcalendar import DateEntry


DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = {}
            return data
    except:
        return {"users": {}}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = load_data()
current_user = None

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("نظام التحفيز – إدارة الفريق")
app.geometry("700x500")

selected_member_filter = ctk.StringVar(value="الكل")
selected_status_filter = ctk.StringVar(value="الكل")
search_text = ctk.StringVar(master=app)
show_completed = ctk.BooleanVar(value=True)

# ----------- اختيار المستخدم -----------
def select_user(name):
    global current_user
    current_user = name
    user_label.configure(text=f"المستخدم: {name}")
    refresh_team()
    refresh_tasks()

def add_user():
    name = user_entry.get()
    if name and name not in data["users"]:
        data["users"][name] = {"team": [], "tasks": []}
        save_data()
        user_menu.configure(values=list(data["users"].keys()))
        user_entry.delete(0, "end")

user_frame = ctk.CTkFrame(app)
user_frame.pack(pady=10)

user_label = ctk.CTkLabel(user_frame, text="اختر مستخدم")
user_label.pack()

user_menu = ctk.CTkOptionMenu(
    user_frame,
    values=list(data["users"].keys()),
    command=select_user
)
user_menu.pack()

user_entry = ctk.CTkEntry(user_frame, placeholder_text="مستخدم جديد")
user_entry.pack(pady=5)

ctk.CTkButton(user_frame, text="إضافة مستخدم", command=add_user).pack()

# ----------- الفريق -----------
team_frame = ctk.CTkFrame(app)
team_frame.pack(pady=10)

team_list = ctk.CTkLabel(team_frame, text="الفريق:")
team_list.pack()

team_entry = ctk.CTkEntry(team_frame, placeholder_text="اسم الشخص")
team_entry.pack()

def add_team_member():
    if current_user:
        name = team_entry.get()
        if name:
            data["users"][current_user]["team"].append(name)
            save_data()
            refresh_team()
            team_entry.delete(0, "end")

ctk.CTkButton(team_frame, text="إضافة شخص للفريق", command=add_team_member).pack()

def refresh_team():
    members = data["users"][current_user]["team"]
    team_list.configure(text="الفريق: " + ", ".join(members))

# ----------- المهام -----------
tasks_frame = ctk.CTkFrame(app)
tasks_frame.pack(pady=10)

task_entry = ctk.CTkEntry(tasks_frame, placeholder_text="عنوان المهمة")
task_entry.pack()

member_menu = ctk.CTkOptionMenu(tasks_frame, values=[])
member_menu.pack(pady=5)

date_entry = DateEntry(
    tasks_frame,
    date_pattern="yyyy-mm-dd",
    width=18,
    background="darkblue",
    foreground="white",
    borderwidth=2
)
date_entry.pack(pady=5)

def add_task():
    if current_user:
        task = {
            "title": task_entry.get(),
            "member": member_menu.get(),
            "deadline": date_entry.get(),
            "done": False,
            "completed_at": None,
            "status": "pending"
        }
        data["users"][current_user]["tasks"].append(task)
        save_data()
        refresh_tasks()


def complete_task(index):
    task = data["users"][current_user]["tasks"][index]

    today = date.today()

    try:
        deadline_date = datetime.strptime(
            task["deadline"].strip(),
            "%Y-%m-%d"
        ).date()
    except ValueError:
        # في حال كتب المستخدم التاريخ بشكل خاطئ
        task["status"] = "invalid_date"
        save_data()
        refresh_tasks()
        return

    task["done"] = True
    task["completed_at"] = today.strftime("%Y-%m-%d")

    if today <= deadline_date:
        task["status"] = "on_time"
    else:
        task["status"] = "late"

    save_data()
    refresh_tasks()

ctk.CTkButton(tasks_frame, text="إضافة مهمة", command=add_task).pack()

filter_frame = ctk.CTkFrame(tasks_frame)
filter_frame.pack(fill="x", padx=10, pady=5)

# فلترة حسب الشخص
member_filter_menu = ctk.CTkOptionMenu(
    filter_frame,
    values=["الكل"],
    variable=selected_member_filter,
    command=lambda _: refresh_tasks()
)
member_filter_menu.pack(side="left", padx=5)

# فلترة حسب الحالة
status_filter_menu = ctk.CTkOptionMenu(
    filter_frame,
    values=["الكل", "قيد التنفيذ", "في الوقت", "متأخرة"],
    variable=selected_status_filter,
    command=lambda _: refresh_tasks()
)
status_filter_menu.pack(side="left", padx=5)

# البحث
search_entry = ctk.CTkEntry(
    filter_frame,
    placeholder_text="🔍 بحث عن مهمة...",
    textvariable=search_text
)
search_entry.pack(side="left", padx=5, fill="x", expand=True)
search_entry.bind("<KeyRelease>", lambda e: refresh_tasks())



tasks_container = ctk.CTkScrollableFrame(
    tasks_frame,
    width=600,
    height=250
)
tasks_container.pack(pady=10, fill="both", expand=True)

def scroll_up(event):
    tasks_container._parent_canvas.yview_scroll(-1, "units")

def scroll_down(event):
    tasks_container._parent_canvas.yview_scroll(1, "units")

app.bind("<Up>", scroll_up)
app.bind("<Down>", scroll_down)

def refresh_tasks():
    clear_tasks_ui()

    # تحديث فلاتر الأشخاص
    members = ["الكل"] + data["users"][current_user]["team"]
    member_filter_menu.configure(values=members)

    if not current_user:
        return

    members = data["users"][current_user]["team"]
    member_menu.configure(values=members)

    for index, t in enumerate(data["users"][current_user]["tasks"]):

        t.setdefault("status", "pending")
        t.setdefault("done", False)
        t.setdefault("completed_at", None)

        # طيّ المهام المنجزة
        if not show_completed.get() and t["done"]:
            continue

        # فلترة حسب الشخص
        if selected_member_filter.get() != "الكل" and t["member"] != selected_member_filter.get():
            continue

        # فلترة حسب الحالة
        status_map = {
            "قيد التنفيذ": "pending",
            "في الوقت": "on_time",
            "متأخرة": "late"
        }
        if selected_status_filter.get() != "الكل":
            if t["status"] != status_map.get(selected_status_filter.get()):
                continue

        # البحث
        if search_text.get().lower() not in t["title"].lower():
            continue

        # تحديد الحالة
        if t["status"] == "on_time":
            status_text = "✅ أُنجزت في الوقت"
            color = "green"
        elif t["status"] == "late":
            status_text = "⚠️ أُنجزت متأخرة"
            color = "orange"
        else:
            status_text = "⏳ قيد التنفيذ"
            color = "gray"

        card = ctk.CTkFrame(tasks_container)
        card.pack(fill="x", pady=5, padx=5)

        label = ctk.CTkLabel(
            card,
            text=f"📌 {t['title']}\n👤 {t['member']} | 📅 {t['deadline']}\n{status_text}",
            justify="left"
        )
        label.pack(side="left", padx=10)

        if not t["done"]:
            ctk.CTkButton(
                card,
                text="✔ إنجاز",
                fg_color=color,
                command=lambda i=index: complete_task(i)
            ).pack(side="right", padx=10)

    save_data()

# إظهار / إخفاء المنجزة
show_done_checkbox = ctk.CTkCheckBox(
    filter_frame,
    text="إظهار المهام المنجزة",
    variable=show_completed,
    command=refresh_tasks
)
show_done_checkbox.pack(side="right", padx=5)

def clear_tasks_ui():
    for widget in tasks_container.winfo_children():
        widget.destroy()

app.mainloop()
