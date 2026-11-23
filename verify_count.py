from src.database.session import get_session_factory
from src.database.models.production import Batch

db = get_session_factory()()
count = db.query(Batch).count()
print(f"SELECT COUNT(*) FROM prd_batches; -> {count}")
db.close()
