import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
from shared.task_manager import TaskManager

@dataclass
class TimeBlock:
    id: str
    start_time: str  # "HH:MM"
    duration: int    # minutes
    title: str
    task_id: Optional[str] = None
    status: str = "planned"  # planned, in_progress, done

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DayPlan:
    date_str: str  # "YYYY-MM-DD"
    blocks: List[TimeBlock] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date_str": self.date_str,
            "blocks": [b.to_dict() for b in self.blocks],
            "notes": self.notes
        }

class DayPlannerManager:
    """
    Manages daily plans, time blocking, and task integration.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.data_file = self.project_dir / ".day_planner.json"
        self.task_manager = TaskManager(project_dir)
        self.plans: Dict[str, DayPlan] = {} # Key: date_str
        self.load_data()

    def load_data(self) -> None:
        if not self.data_file.exists():
            return

        try:
            data = json.loads(self.data_file.read_text())
            for date_str, plan_data in data.items():
                blocks = [TimeBlock(**b) for b in plan_data.get("blocks", [])]
                self.plans[date_str] = DayPlan(
                    date_str=date_str,
                    blocks=blocks,
                    notes=plan_data.get("notes", "")
                )
        except Exception:
            # If load fails, start fresh (or could log error)
            pass

    def save_data(self) -> None:
        data = {k: v.to_dict() for k, v in self.plans.items()}
        try:
            self.data_file.write_text(json.dumps(data, indent=2))
        except IOError:
            pass

    def get_plan(self, date_obj: date) -> DayPlan:
        date_str = date_obj.isoformat()
        if date_str not in self.plans:
            self.plans[date_str] = DayPlan(date_str=date_str)
        return self.plans[date_str]

    def add_block(self, date_obj: date, start_time: str, duration: int, title: str, task_id: Optional[str] = None) -> Optional[str]:
        """
        Adds a time block. Returns block ID if successful, None if conflict.
        Simple conflict check: overlap with existing blocks.
        """
        plan = self.get_plan(date_obj)

        # Parse time
        try:
            new_start_dt = datetime.strptime(start_time, "%H:%M")
            new_start_min = new_start_dt.hour * 60 + new_start_dt.minute
            new_end_min = new_start_min + duration
        except ValueError:
            return None # Invalid time format

        # Check overlaps
        for block in plan.blocks:
            try:
                b_start_dt = datetime.strptime(block.start_time, "%H:%M")
                b_start_min = b_start_dt.hour * 60 + b_start_dt.minute
                b_end_min = b_start_min + block.duration

                # Overlap logic: (StartA <= EndB) and (EndA >= StartB)
                if new_start_min < b_end_min and new_end_min > b_start_min:
                    return None # Conflict
            except ValueError:
                continue

        # Create block
        block_id = str(int(time.time() * 1000)) # Simple ID
        new_block = TimeBlock(
            id=block_id,
            start_time=start_time,
            duration=duration,
            title=title,
            task_id=task_id
        )
        plan.blocks.append(new_block)
        # Sort by time
        plan.blocks.sort(key=lambda x: x.start_time)
        self.save_data()
        return block_id

    def remove_block(self, date_obj: date, block_id: str) -> bool:
        plan = self.get_plan(date_obj)
        initial_len = len(plan.blocks)
        plan.blocks = [b for b in plan.blocks if b.id != block_id]
        if len(plan.blocks) < initial_len:
            self.save_data()
            return True
        return False

    def update_notes(self, date_obj: date, notes: str) -> None:
        plan = self.get_plan(date_obj)
        plan.notes = notes
        self.save_data()

    def get_unscheduled_tasks(self, date_obj: date) -> List[Any]:
        """
        Returns tasks from TaskManager that are NOT scheduled in the day's plan.
        """
        all_tasks = self.task_manager.fetch_all_tasks()
        plan = self.get_plan(date_obj)

        scheduled_ids = set()
        for b in plan.blocks:
            if b.task_id:
                scheduled_ids.add(b.task_id)

        return [t for t in all_tasks if t.id not in scheduled_ids]

    def auto_schedule(self, date_obj: date) -> int:
        """
        Automatically schedules high-priority tasks into free slots.
        Returns number of tasks scheduled.
        """
        plan = self.get_plan(date_obj)
        tasks = self.get_unscheduled_tasks(date_obj)

        # Sort tasks by priority (High > Medium > Low)
        priority_map = {"High": 0, "Medium": 1, "Low": 2}
        tasks.sort(key=lambda x: priority_map.get(x.priority, 3))

        scheduled_count = 0

        # Define work day slots (09:00 to 17:00, 60 min slots)
        start_hour = 9
        end_hour = 17

        current_min = start_hour * 60
        end_min = end_hour * 60

        for task in tasks:
            if current_min >= end_min:
                break

            # Try to find a slot
            # Simple greedy: find first gap of 60 mins from current_min
            duration = 60

            # Check overlap with existing blocks
            # We iterate through potential start times in 30 min increments
            while current_min + duration <= end_min:
                conflict = False
                slot_start = current_min
                slot_end = current_min + duration

                for block in plan.blocks:
                    try:
                        b_start = datetime.strptime(block.start_time, "%H:%M")
                        b_start_m = b_start.hour * 60 + b_start.minute
                        b_end_m = b_start_m + block.duration

                        if slot_start < b_end_m and slot_end > b_start_m:
                            conflict = True
                            # Jump past this block
                            current_min = b_end_m
                            break
                    except ValueError:
                        pass

                if not conflict:
                    # Found a slot!
                    hour = current_min // 60
                    minute = current_min % 60
                    time_str = f"{hour:02d}:{minute:02d}"

                    self.add_block(date_obj, time_str, duration, task.title, task.id)
                    scheduled_count += 1
                    current_min += duration # Advance
                    break
                else:
                    # If conflict, loop continues with new current_min
                    pass

        return scheduled_count
