import customtkinter as ctk
from typing import Callable, List, Optional
from datetime import datetime, date, timedelta
from pathlib import Path
import sys

# Add path for data model imports
sys.path.append(str(Path(__file__).parent.parent))

from src.data.database import Database
from src.data.entry import Entry
from src.data.project import Project
from src.constants import EntryType, HourType, DATABASE, Tables


# ==================== LOGIC SECTION ====================

class PrototypeLogic:
    """UI Logic - separated from UI for later extraction to logic module"""
    
    def __init__(self, db_path: Path = DATABASE):
        self.db = Database(db_path)
        self.current_active_entry: Optional[Entry] = None
        self.current_viewed_entry: Optional[Entry] = None
    
    def get_all_projects(self) -> List[Project]:
        """Get all projects from the database."""
        try:
            with Database.database_cursor(self.db.database_path) as cursor:
                cursor.execute("SELECT id FROM projects")
                project_ids = [row[0] for row in cursor.fetchall()]
            return [Project(self.db, project_id) for project_id in project_ids]
        except Exception:
            return []
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get a project by its ID."""
        try:
            return Project(self.db, project_id)
        except Exception:
            return None
    
    def get_all_entries(self) -> List[Entry]:
        """Get all entries from the database, sorted by begin_at descending."""
        try:
            with Database.database_cursor(self.db.database_path) as cursor:
                cursor.execute("SELECT id FROM entries ORDER BY begin_at DESC")
                entry_ids = [row[0] for row in cursor.fetchall()]
            return [Entry(self.db, entry_id) for entry_id in entry_ids]
        except Exception:
            return []
    
    def get_entries_by_date_range(self, start_date: date, end_date: date) -> List[Entry]:
        """Get entries within a specific date range."""
        try:
            with Database.database_cursor(self.db.database_path) as cursor:
                cursor.execute(
                    "SELECT id FROM entries WHERE entry_date BETWEEN ? AND ? ORDER BY begin_at DESC",
                    (start_date, end_date)
                )
                entry_ids = [row[0] for row in cursor.fetchall()]
            return [Entry(self.db, entry_id) for entry_id in entry_ids]
        except Exception:
            return []
    
    def get_entries_for_week(self) -> List[Entry]:
        """Get entries for the current week."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return self.get_entries_by_date_range(start_of_week, end_of_week)
    
    def get_entries_for_month(self) -> List[Entry]:
        """Get entries for the current month."""
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        
        if today.month == 12:
            end_of_month = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        return self.get_entries_by_date_range(start_of_month, end_of_month)
    
    def get_entries_for_year(self) -> List[Entry]:
        """Get entries for the current year."""
        today = date.today()
        start_of_year = date(today.year, 1, 1)
        end_of_year = date(today.year, 12, 31)
        return self.get_entries_by_date_range(start_of_year, end_of_year)
    
    def start_new_entry(self, project_id: int, entry_type: EntryType = EntryType.ARBEIT) -> Entry:
        """Start a new time entry."""
        if self.current_active_entry is not None:
            self.stop_current_entry()
        
        new_entry = Entry(
            self.db,
            project_id=project_id,
            entry_type=entry_type,
            is_active=True,
            entry_date=date.today(),
            begin_at=datetime.now()
        )
        
        self.current_active_entry = new_entry
        return new_entry
    
    def stop_current_entry(self) -> Optional[Entry]:
        """Stop the currently active entry."""
        if self.current_active_entry is None:
            return None
        
        entry = self.current_active_entry
        entry.end_at = datetime.now()
        entry.is_active = False
        self.current_active_entry = None
        return entry
    
    def is_entry_running(self) -> bool:
        """Check if there's currently an active entry."""
        return self.current_active_entry is not None
    
    def get_weekly_hours(self) -> float:
        """Get the total hours worked this week."""
        entries = self.get_entries_for_week()
        total_seconds = 0
        
        for entry in entries:
            try:
                duration = entry.duration
                total_seconds += duration.total_seconds()
            except Exception:
                pass
        
        return total_seconds / 3600
    
    def get_project_stats(self, project_id: int) -> dict:
        """Get statistics for a specific project."""
        project = self.get_project_by_id(project_id)
        if project is None:
            return {
                "name": "Unknown",
                "target_hours": 0,
                "hour_type": HourType.WEEKLY,
                "worked_hours": 0,
                "open_hours": 0,
                "overtime": 0
            }
        
        try:
            entry_ids = self.db.get_entry_ids_from_project_id(project_id)
            entries = [Entry(self.db, entry_id) for entry_id in entry_ids]
        except Exception:
            entries = []
        
        total_worked_seconds = 0
        for entry in entries:
            try:
                duration = entry.duration
                total_worked_seconds += duration.total_seconds()
            except Exception:
                pass
        
        total_worked_hours = total_worked_seconds / 3600
        target_hours = project.target_hours
        hour_type = project.hour_type
        
        open_hours = max(0, target_hours - total_worked_hours)
        overtime = max(0, total_worked_hours - target_hours)
        
        return {
            "name": project.name,
            "target_hours": target_hours,
            "hour_type": hour_type,
            "worked_hours": total_worked_hours,
            "open_hours": open_hours,
            "overtime": overtime
        }
    
    def set_current_viewed_entry(self, entry: Entry):
        """Set the entry that is currently being viewed in detail."""
        self.current_viewed_entry = entry
    
    def get_current_viewed_entry(self) -> Optional[Entry]:
        """Get the entry that is currently being viewed in detail."""
        return self.current_viewed_entry
    
    def on_entry_clicked(self, entry_id: int):
        """Callback for when an entry is clicked to view details."""
        try:
            entry = Entry(self.db, entry_id)
            self.set_current_viewed_entry(entry)
            return entry
        except Exception:
            return None
    
    def get_entries_for_filter(self, filter_type: str) -> List[dict]:
        """Get entries based on the selected filter."""
        if filter_type == "All":
            entries = self.get_all_entries()
        elif filter_type == "Year":
            entries = self.get_entries_for_year()
        elif filter_type == "Month":
            entries = self.get_entries_for_month()
        elif filter_type == "Week":
            entries = self.get_entries_for_week()
        else:
            entries = self.get_all_entries()
        
        entry_data = []
        for entry in entries:
            try:
                project = self.get_project_by_id(entry.project_id)
                project_name = project.name if project else "Unknown"
                
                entry_data.append({
                    "id": entry.id,
                    "project_name": project_name,
                    "type": entry.entry_type.value,
                    "duration": str(entry.duration),
                    "date": entry.entry_date.isoformat() if entry.entry_date else "N/A",
                    "begin_at": entry.begin_at.isoformat() if entry.begin_at else "N/A"
                })
            except Exception:
                continue
        
        return entry_data


# ==================== UI SECTION ====================

class Progressbar(ctk.CTkProgressBar):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class ProjectInfoLabel(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class HoursLabel(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class StartEntryButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class StopEntryButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class ProjectSelector(ctk.CTkOptionMenu):
    def __init__(self, master, logic: PrototypeLogic, **kwargs):
        super().__init__(master, **kwargs)
        self.logic = logic
        self._update_projects()
    
    def _update_projects(self):
        projects = self.logic.get_all_projects()
        project_names = [f"{p.id}: {p.name}" for p in projects]
        if project_names:
            self.configure(values=project_names)
            self.set(project_names[0])
    
    def get_selected_project_id(self) -> int:
        selected = self.get()
        if ": " in selected:
            return int(selected.split(": ")[0])
        return 1


class EntryStartFrame(ctk.CTkFrame):
    def __init__(self, master, logic: PrototypeLogic, **kwargs):
        super().__init__(master, **kwargs)
        
        self.logic = logic
        
        self.project_selector = ProjectSelector(self, logic=self.logic)
        self.project_selector.pack(fill="x", padx=5, pady=5)
        
        self.start_button = StartEntryButton(
            self, 
            text="Start Entry",
            command=self._on_start_entry
        )
        self.start_button.pack(fill="x", padx=5, pady=5)
    
    def _on_start_entry(self):
        project_id = self.project_selector.get_selected_project_id()
        self.logic.start_new_entry(project_id)


class DashboardStatsFrame(ctk.CTkFrame):
    def __init__(self, master, logic: PrototypeLogic, **kwargs):
        super().__init__(master, **kwargs)
        
        self.logic = logic
        
        self.project_name_label = ProjectInfoLabel(self, text="Project: ")
        self.project_name_label.pack(fill="x", padx=5, pady=2)
        
        self.hours_model_label = ProjectInfoLabel(self, text="Hours Model: ")
        self.hours_model_label.pack(fill="x", padx=5, pady=2)
        
        self.worked_hours_label = HoursLabel(self, text="Worked Hours: ")
        self.worked_hours_label.pack(fill="x", padx=5, pady=2)
        
        self.open_hours_label = HoursLabel(self, text="Open Hours: ")
        self.open_hours_label.pack(fill="x", padx=5, pady=2)
        
        self.overtime_label = HoursLabel(self, text="Overtime: ")
        self.overtime_label.pack(fill="x", padx=5, pady=2)
    
    def update_stats(self, project_id: int):
        stats = self.logic.get_project_stats(project_id)
        self.project_name_label.configure(text=f"Project: {stats['name']}")
        self.hours_model_label.configure(text=f"Hours Model: {stats['hour_type'].value} - {stats['target_hours']}h")
        self.worked_hours_label.configure(text=f"Worked Hours: {stats['worked_hours']:.2f}h")
        self.open_hours_label.configure(text=f"Open Hours: {stats['open_hours']:.2f}h")
        self.overtime_label.configure(text=f"Overtime: {stats['overtime']:.2f}h")


class Dashboard(ctk.CTkFrame):
    def __init__(self, master, logic: PrototypeLogic, **kwargs):
        super().__init__(master, **kwargs)
        
        self.logic = logic
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.progress_bar = Progressbar(self)
        self.progress_bar.grid(column=0, row=0, sticky="ew", padx=10, pady=10)
        
        self.stats_frame = DashboardStatsFrame(self, logic=self.logic)
        self.stats_frame.grid(column=0, row=1, sticky="nsew", padx=10, pady=10)
        
        self.entry_start_frame = EntryStartFrame(self, logic=self.logic)
        self.entry_start_frame.grid(column=0, row=2, sticky="ew", padx=10, pady=10)
        
        self._update_dashboard()
    
    def _update_dashboard(self):
        projects = self.logic.get_all_projects()
        if projects:
            project = projects[0]
            self.stats_frame.update_stats(project.id)
            weekly_progress = min(1.0, self.logic.get_weekly_hours() / 40)
            self.progress_bar.set(weekly_progress)


class FilterSegmentedButton(ctk.CTkSegmentedButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class EntryFrame(ctk.CTkFrame):
    def __init__(self, master, entry_data: dict, on_click: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.entry_data = entry_data
        self.on_click = on_click
        
        self.project_label = ProjectInfoLabel(self, text=f"Project: {entry_data.get('project_name', 'N/A')}")
        self.project_label.pack(side="left", padx=5, pady=5)
        
        self.type_label = ProjectInfoLabel(self, text=f"Type: {entry_data.get('type', 'N/A')}")
        self.type_label.pack(side="left", padx=5, pady=5)
        
        self.duration_label = HoursLabel(self, text=f"Duration: {entry_data.get('duration', 'N/A')}")
        self.duration_label.pack(side="left", padx=5, pady=5)
        
        self.date_label = HoursLabel(self, text=f"Date: {entry_data.get('date', 'N/A')}")
        self.date_label.pack(side="left", padx=5, pady=5)
        
        # Make the entire frame clickable
        self.bind("<Button-1>", self._on_frame_click)
        self.project_label.bind("<Button-1>", self._on_frame_click)
        self.type_label.bind("<Button-1>", self._on_frame_click)
        self.duration_label.bind("<Button-1>", self._on_frame_click)
        self.date_label.bind("<Button-1>", self._on_frame_click)
    
    def _on_frame_click(self, event):
        if self.on_click:
            self.on_click(self.entry_data.get("id"))


class EntryListFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, logic: PrototypeLogic, **kwargs):
        super().__init__(master, **kwargs)
        
        self.logic = logic
        self.entry_frames = []
    
    def add_entry(self, entry_data: dict, on_click: Optional[Callable] = None):
        entry_frame = EntryFrame(self, entry_data=entry_data, on_click=on_click)
        self.entry_frames.append(entry_frame)
        entry_frame.pack(fill="x", padx=5, pady=5)
    
    def clear_entries(self):
        for entry_frame in self.entry_frames:
            entry_frame.destroy()
        self.entry_frames = []
    
    def load_entries(self, filter_type: str = "All", on_click: Optional[Callable] = None):
        self.clear_entries()
        entries = self.logic.get_entries_for_filter(filter_type)
        for entry_data in entries:
            self.add_entry(entry_data, on_click=on_click)


class EntriesPage(ctk.CTkFrame):
    def __init__(self, master, logic: PrototypeLogic, **kwargs):
        super().__init__(master, **kwargs)
        
        self.logic = logic
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.filter_segmented = FilterSegmentedButton(
            self, 
            values=["All", "Year", "Month", "Week"],
            command=self._on_filter_change
        )
        self.filter_segmented.grid(column=0, row=0, sticky="ew", padx=10, pady=10)
        
        self.entry_list = EntryListFrame(self, logic=self.logic)
        self.entry_list.grid(column=0, row=1, sticky="nsew", padx=10, pady=10)
        
        self.entry_list.load_entries("All", on_click=self._on_entry_clicked)
    
    def _on_filter_change(self, value):
        self.entry_list.load_entries(value, on_click=self._on_entry_clicked)
    
    def _on_entry_clicked(self, entry_id: int):
        entry = self.logic.on_entry_clicked(entry_id)
        if entry:
            print(f"Viewing entry: {entry.id}")


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


class MenuSegmentedButton(ctk.CTkSegmentedButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class PageFrame(ctk.CTkFrame):
    def __init__(self, master, logic: PrototypeLogic, **kwargs):
        super().__init__(master, **kwargs)
        
        self.logic = logic
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.dashboard = Dashboard(self, logic=self.logic)
        self.entries = EntriesPage(self, logic=self.logic)
        self.settings = SettingsPage(self)
        
        self.dashboard.grid(column=0, row=0, sticky="nsew")
        self.entries.grid(column=0, row=0, sticky="nsew")
        self.settings.grid(column=0, row=0, sticky="nsew")
        
        self.show_page("dashboard")
    
    def show_page(self, page_name):
        self.dashboard.grid_forget()
        self.entries.grid_forget()
        self.settings.grid_forget()
        
        if page_name == "dashboard":
            self.dashboard.grid(column=0, row=0, sticky="nsew")
            self.dashboard._update_dashboard()
        elif page_name == "entries":
            self.entries.grid(column=0, row=0, sticky="nsew")
            self.entries._on_filter_change("All")
        elif page_name == "settings":
            self.settings.grid(column=0, row=0, sticky="nsew")


class App(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize logic - integrated into UI but separated for later extraction
        self.logic = PrototypeLogic()
        
        self.title("Zeiterfassung")
        self.resizable(True, True)
        self.geometry("600x800")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        self.pages = PageFrame(self, logic=self.logic)
        self.pages.grid(column=0, row=0, sticky="nsew")
        
        self.menu_button = MenuSegmentedButton(
            self, 
            values=["Dashboard", "Entries", "Settings"],
            command=self.on_menu_select
        )
        self.menu_button.grid(column=0, row=1, sticky="ew", padx=20, pady=20)
    
    def on_menu_select(self, value):
        if value == "Dashboard":
            self.pages.show_page("dashboard")
        elif value == "Entries":
            self.pages.show_page("entries")
        elif value == "Settings":
            self.pages.show_page("settings")


if __name__ == '__main__':
    app = App()
    app.mainloop()