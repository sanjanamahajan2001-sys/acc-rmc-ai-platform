import sys
sys.path.insert(0, '/home/sanjana/acc-rmc-ai-platform')
from src.database.session import get_read_only_session
from src.services.statistical_quality_service import StatisticalQualityService

with get_read_only_session() as db:
    res = StatisticalQualityService.get_strength_timeline(db, plant_code=None, limit=50)
    print(f'Total points returned: {len(res.timeline)}')
    with_28d = [p for p in res.timeline if p.result_28d_mpa is not None]
    print(f'Points with 28d break: {len(with_28d)}')
    for p in res.timeline[-10:]:
        print(p.batch_number, p.production_timestamp, p.result_7d_mpa, p.result_28d_mpa)
