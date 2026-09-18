from tkinter import Menu
from src.data.project import Project
from src.data.entry import Entry
from src.data.database import Database

import customtkinter as ctk

db = Database()

projects = [Project(db, id) for id in db.get_all_project_ids()]


class Progressbar(ctk.CTkProgressBar):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

class ProjectSelector(ctk.CTkOptionMenu):
    def __init__(self, master, **kwargs):

        self.selected_project = ctk.StringVar()
        self.selected_project.set(projects[2].name)
        self.values = [project.name for project in projects]
        super().__init__(master,
                         values=self.values,
                         variable=self.selected_project,
                         **kwargs)

        print(self.selected_project)


class Header(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=2)

        self.project_selector = ProjectSelector(self)
        self.project_selector.grid(column=1, row=0)
        self.headerlbl = ctk.CTkLabel(self, text="Project")
        self.headerlbl.grid(column=0, row=0)



class ContentFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master,**kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.dashboard = Dashboard(self)
        self.dashboard.grid(column=0, row=0, sticky="nsew")
        self.entries = Entries(self)
        self.entries.grid(column=1, row=0, sticky="nsew")
        self.history = History(self)
        self.history.grid(column=2, row=0, sticky="nsew")
        self.settings = Settings(self)
        self.settings.grid(column=3, row=0, sticky="nsew")

    def show_page(self, page):
        self.dashboard.grid_remove()
        self.entries.grid_remove()
        self.history.grid_remove()
        self.settings.grid_remove()

        match page:
            case "Dashboard":
                self.dashboard.grid()
            case "Entries":
                self.entries.grid()
            case "History":
                self.history.grid()
            case "Settings":
                self.settings.grid()


class Dashboard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.progress_bar = Progressbar(self)
        self.progress_bar.grid(column=0, row=0)

class Entries(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=2)

        self.label = ctk.CTkLabel(self, text="Entries")
        self.label.grid(column=0, row=0)
        self.entry_list = EntryList(self)
        self.entry_list.grid(column=0, row=1, sticky="nsew")

class EntryList(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.entry_boxes = []

        for entry in projects[0].entry_list:
            self.entry_boxes.append(EntryBox(self, entry))

        i = 0
        for box in self.entry_boxes:
            box.grid(column=0, row=i, sticky="nsew")
            i += 1

class EntryBox(ctk.CTkFrame):
    def __init__(self, master, entry, **kwargs):
        super().__init__(master, **kwargs)
        self.name = ctk.CTkLabel(self, text=entry.entry_type)
        self.name.grid(column=0, sticky="nsew")
        self.duration = ctk.CTkLabel(self, text=entry.duration)
        self.duration.grid(column=1, sticky="nsew")
        self.date = ctk.CTkLabel(self, text=entry.entry_date)


class History(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="History")

class Settings(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Settings")




class MenuBar(ctk.CTkSegmentedButton):
    def __init__(self, master, **kwargs):
        self.selected_menu_item = ctk.StringVar()
        super().__init__(master,
                         values=["Dashboard", "Entries", "History", "Settings"],
                         variable=self.selected_menu_item,
                         command=master.on_menubar_selection,
                         **kwargs)


class App(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__()

        self.title("Zeiterfassung")
        self.resizable(True, True)
        self.geometry("600x800")
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=10)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.header = Header(self)
        self.header.grid(sticky="new")

        self.contentFrame = ContentFrame(self)
        self.contentFrame.grid()

        self.menu_bar = MenuBar(self)
        self.menu_bar.grid(sticky="sew",pady=10, padx=10) #column=0, row=20, columnspan=3,
        self.menu_bar.set("Dashboard")
        self.contentFrame.show_page("Dashboard")

    def on_menubar_selection(self, value):
        self.contentFrame.show_page(page=value)



if __name__ == '__main__':
    app = App()
    app.mainloop()
