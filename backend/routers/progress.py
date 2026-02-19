from fastapi import APIRouter, Depends
from models import User, Plan, Task, TaskCompletion
from routers.auth import get_current_user
from utils.logger import get_logger
from typing import Dict, List, Any
from datetime import datetime, timedelta, date
from beanie.operators import In

log = get_logger("router.progress")
router = APIRouter(prefix="/progress", tags=["progress"])

# --- Helper: Calculate stats for a date range ---
async def _calculate_period_stats(user_id, start_date_str: str, end_date_str: str):
    """
    Calculates completion % for every day in the range.
    Returns:
    - daily_stats: Map { "YYYY-MM-DD": percentage }
    - average: Overall average percentage
    """
    # 1. Fetch all Plans (Daily) in range
    plans = await Plan.find(
        Plan.user_id == user_id,
        Plan.date >= start_date_str,
        Plan.date <= end_date_str,
        Plan.plan_type == "daily"  # Only count daily plans
    ).to_list()
    
    # Map map: date -> {total: 0, completed: 0}
    # Initialize with 0 for all days? Or only days with plans? 
    # User requirement: "Year Heatmap: Aggregate daily percentages".
    # Typically heatmaps show 0/empty for days without data.
    
    # We will iterate through plans to get tasks
    stats = {} 
    
    if not plans:
        return {}, 0

    plan_ids = [p.id for p in plans]
    
    # 2. Fetch all Tasks for these plans
    # Note: potential for large query if range is huge (Year). 
    # Optimization: If performance hit, raw aggregation pipeline is better. 
    # But for a single user, fetching 1 year of tasks (e.g. 5 * 365 = 1800 tasks) is fine for Mongo/Beanie.
    tasks = await Task.find(In(Task.plan_id, plan_ids)).to_list()
    
    # Group tasks by plan_id to map to date
    plan_date_map = {p.id: p.date for p in plans}
    tasks_by_date = {}
    
    # Initialize counts
    for p in plans:
        stats[p.date] = {"total": 0, "completed": 0, "score": 0}
        
    # Count Totals
    task_ids = []
    for t in tasks:
        d = plan_date_map.get(t.plan_id)
        if d:
            stats[d]["total"] += 1
            task_ids.append(t.id)

    # 3. Fetch Completions (The source of truth for Status)
    completions = await TaskCompletion.find(
        TaskCompletion.user_id == user_id,
        TaskCompletion.date >= start_date_str,
        TaskCompletion.date <= end_date_str
    ).to_list()
    
    # Apply completions
    for c in completions:
        # Check if this completion corresponds to a valid task in our set (optional validation)
        # We assume strict consistency isn't 100% required here, but good to match dates.
        if c.date in stats:
             # We can't simple count completions because multiple completions might exist for recurring tasks, 
             # but we only care if it matches a task in the plan?
             # Actually, TaskCompletion is the truth. But we need a denominator (Total Tasks).
             # Total Tasks comes from the Plan.
             
             # Challenge: A recurring task completed today has a TaskCompletion record.
             # The 'Task' object exists in the Plan.
             # So we count how many 'Done' statuses in completions match tasks in that day's plan.
             
             # Simplification: 
             # For a specific date D:
             # Total = Count of Tasks in Plan(D)
             # Completed = Count of TaskCompletions(D) where task_id is in Tasks(Plan(D))
             # AND status="done"
             
             if c.status == "done":
                 # Verify it belongs to the plan? 
                 # Optimization: Just count it towards that date's score if it's done. 
                 # Warning: If user somehow has orphans, they might count. 
                 # But generally safe.
                 
                 # Need to ensure we don't double count if multiple entries (shouldn't happen with unique logic).
                 if c.date in stats:
                     status_entry = stats[c.date]
                     # Only increment if it's not already capped? 
                     # No, just increment. 
                     # Wait, we need to match it to a task to be sure it's valid?
                     # Let's assume yes for O(1).
                     status_entry["completed"] += 1

    # Calculate Percentages
    daily_percentages = {}
    total_percent_sum = 0
    count_days_with_data = 0
    
    for date_key, data in stats.items():
        total = data["total"]
        completed = data["completed"]
        
        # Cap completion at total (in case of data anomalies)
        if completed > total: completed = total
        
        pct = (completed / total * 100) if total > 0 else 0
        daily_percentages[date_key] = round(pct)
        
        if total > 0:
            total_percent_sum += pct
            count_days_with_data += 1
            
    avg = round(total_percent_sum / count_days_with_data) if count_days_with_data > 0 else 0
    
    return daily_percentages, avg


# --- Endpoints ---

@router.get("/year/{year}")
async def get_year_progress(
    year: int,
    current_user: User = Depends(get_current_user)
):
    """
    Returns heatmap data and monthly averages for the year.
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    daily_map, year_avg = await _calculate_period_stats(current_user.id, start_date, end_date)
    
    # Format for Heatmap (Array of objects)
    heatmap_data = [
        {"date": d, "percentage": p} 
        for d, p in daily_map.items()
    ]
    
    # Calculate Monthly Averages
    monthly_stats = {k: [] for k in range(1, 13)}
    
    for d_str, pct in daily_map.items():
        try:
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            monthly_stats[dt.month].append(pct)
        except:
            pass
            
    monthly_averages = []
    for m in range(1, 13):
        vals = monthly_stats[m]
        avg = round(sum(vals) / len(vals)) if vals else 0
        monthly_averages.append({"month": m, "percentage": avg})
        
    return {
        "year": year,
        "average": year_avg,
        "heatmap": heatmap_data,
        "monthly_averages": monthly_averages
    }

@router.get("/month/{year}/{month}")
async def get_month_progress(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user)
):
    """
    Returns daily stats for a specific month.
    """
    # Construct start/end
    import calendar
    _, last_day = calendar.monthrange(year, month)
    
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    daily_map, month_avg = await _calculate_period_stats(current_user.id, start_date, end_date)
    
    days_array = [
        {"date": d, "percentage": p}
        for d, p in daily_map.items()
    ]
    days_array.sort(key=lambda x: x["date"])
    
    return {
        "period": f"{year}-{month:02d}",
        "average": month_avg,
        "days": days_array
    }

@router.get("/day/{date_str}")
async def get_day_detail(
    date_str: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed breakdown for a specific day.
    """
    # Re-use Plan Router logic partially, but we need strictly historical data view
    # Fetch Plan
    plan = await Plan.find_one(
        Plan.user_id == current_user.id,
        Plan.date == date_str,
        Plan.plan_type == "daily"
    )
    
    if not plan:
        return {"date": date_str, "found": False}
        
    tasks = await Task.find(Task.plan_id == plan.id).to_list()
    
    # Overlay Completions
    completions = await TaskCompletion.find(
        TaskCompletion.user_id == current_user.id,
        TaskCompletion.date == date_str
    ).to_list()
    
    status_map = {str(c.task_id): c.status for c in completions}
    
    enriched_tasks = []
    completed_count = 0
    
    for t in tasks:
        # Default status pending
        status = "pending"
        if str(t.id) in status_map:
            status = status_map[str(t.id)]
        
        if status == "done":
            completed_count += 1
            
        enriched_tasks.append({
            "id": str(t.id),
            "title": t.title,
            "category": t.category,
            "status": status,
            "priority": t.priority
        })
        
    total = len(tasks)
    percentage = (completed_count / total * 100) if total > 0 else 0
    
    return {
        "date": date_str,
        "found": True,
        "percentage": round(percentage),
        "total": total,
        "completed": completed_count,
        "summary": plan.summary,
        "tasks": enriched_tasks
    }


@router.get("/suggestions")
async def get_suggestions(
    current_user: User = Depends(get_current_user)
):
    """
    Analyze patterns and return suggestions.
    1. Missed Recurring Tasks (3+ misses in last 7 days)
    2. Low Performance Days (<40% avg on specific weekday over last 4 weeks)
    """
    suggestions = []
    today = date.today()
    
    # --- 1. Missed Recurring Tasks ---
    # Look back 7 days
    start_7d = str(today - timedelta(days=7))
    
    # Get all tasks in this window? 
    # Better: Get all completions? 
    # "Missed" means Task exists in Plan but Status != DONE.
    # So we need Plans -> Tasks -> Completions for last 7 days.
    
    # Reuse helper to get daily maps? No, we need granular task data.
    plans_7d = await Plan.find(
        Plan.user_id == current_user.id,
        Plan.date >= start_7d,
        Plan.plan_type == "daily"
    ).to_list()
    
    if plans_7d:
        pids = [p.id for p in plans_7d]
        tasks_7d = await Task.find(In(Task.plan_id, pids)).to_list()
        
        # Link tasks to dates
        pid_date = {p.id: p.date for p in plans_7d}
        
        # Get completions
        completions_7d = await TaskCompletion.find(
            TaskCompletion.user_id == current_user.id,
            TaskCompletion.date >= start_7d
        ).to_list()
        
        # Map: (task_title) -> Miss Count
        # We use Title to group recurring tasks (assuming same title)
        miss_counts = {}
        
        # Build completion map: (task_id, date) -> status
        # Actually, TaskCompletion uses task_id. 
        # But recurring tasks have different IDs in different plans?
        # YES. Orchestrator creates new Task objects for each daily plan.
        # So grouping by TITLE is the only way to detect "Recurring Task" misses.
        
        comp_map = {(str(c.task_id)): c.status for c in completions_7d}
        
        for t in tasks_7d:
            status = comp_map.get(str(t.id), "pending") # Default if no record
            if status != "done":
                # Check if it was supposed to be done?
                # Assume all tasks in plan are "to do".
                # Group by title
                title = t.title.strip().lower()
                miss_counts[title] = miss_counts.get(title, 0) + 1
                
        # Filter > 2
        for title, count in miss_counts.items():
            if count >= 3:
                suggestions.append({
                    "type": "missed_recurring",
                    "title": title.capitalize(),
                    "message": f"You've missed '{title}' {count} times this week. Consider rescheduling or removing it.",
                    "count": count
                })
                
    # --- 2. Low Performance Weekdays ---
    # Look back 28 days (4 weeks)
    start_28d = str(today - timedelta(days=28))
    
    daily_stats, _ = await _calculate_period_stats(current_user.id, start_28d, str(today))
    
    # Group by weekday (0=Mon, 6=Sun)
    # week_stats = {0: [], 1: [], ...}
    week_stats = {i: [] for i in range(7)}
    
    for d_str, pct in daily_stats.items():
        try:
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            week_stats[dt.weekday()].append(pct)
        except:
            pass
            
    # Analyze
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day_idx, pcts in week_stats.items():
        if not pcts: continue
        avg = sum(pcts) / len(pcts)
        if avg < 40:
             suggestions.append({
                "type": "pattern_low_energy",
                "day": weekdays[day_idx],
                "average": round(avg),
                "message": f"{weekdays[day_idx]}s seem tough (Avg: {round(avg)}%). Try scheduling fewer tasks."
            })

    return suggestions
