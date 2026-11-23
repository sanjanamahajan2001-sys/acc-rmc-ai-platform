import sys
sys.path.insert(0, '/home/sanjana/acc-rmc-ai-platform')
from src.database.session import get_read_only_session
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.production import Batch
from src.database.models.master import Plant, Recipe

with get_read_only_session() as db:
    tests_count = db.query(CubeTest).filter(CubeTest.age_days == 28, CubeTest.compressive_strength_mpa > 0).count()
    print(f'Total 28-day valid tests: {tests_count}')

    tested_batches = (
        db.query(Batch.id, Batch.batch_number, Batch.created_at, CubeTest.compressive_strength_mpa)
        .join(ConcreteSample, ConcreteSample.batch_id == Batch.id)
        .join(CubeSet, CubeSet.sample_id == ConcreteSample.id)
        .join(CubeTest, CubeTest.cube_set_id == CubeSet.id)
        .filter(CubeTest.age_days == 28, CubeTest.compressive_strength_mpa > 0)
        .order_by(Batch.created_at.asc())
        .all()
    )
    print(f'Tested batches count: {len(tested_batches)}')
    for b in tested_batches[:10]:
        print(b)
