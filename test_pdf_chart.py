import sys
sys.path.insert(0, '/home/sanjana/acc-rmc-ai-platform')
from src.database.session import get_read_only_session
from src.services.dashboard_export_service import DashboardExportService

with get_read_only_session() as db:
    dto = DashboardExportService.build_full_report_dto(
        db=db,
        plant_code=
