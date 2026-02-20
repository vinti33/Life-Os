from schemas.plan_schemas import DailyPlanSchema, DailyTask
from pydantic import ValidationError

try:
    plan = DailyPlanSchema(
        plan_summary="Test Plan",
        tasks=[
            DailyTask(title="Focus 1", start_time="10:00", end_time="13:00", category="work", energy_required="high", priority=1),
            DailyTask(title="Exercise", start_time="11:00", end_time="12:00", category="health", energy_required="medium", priority=1)
        ]
    )
    print("Plan Validated Successfully (UNEXPECTED)")
except ValidationError as e:
    print(f"Validation Failed (EXPECTED): {e}")
except ValueError as e:
    print(f"Value Error (EXPECTED): {e}")
