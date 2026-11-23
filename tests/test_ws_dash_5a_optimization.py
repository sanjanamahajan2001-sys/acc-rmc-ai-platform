import pytest
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from src.database.session import get_session_factory
from src.database.models.master import Recipe, Plant
from src.database.models.optimization import OptimizationRun
from src.database.models.user import User, Role, UserRole
from src.services.mix_optimization_service import MixOptimizationService
from src.contracts.optimization.models import OptimizationRunTriggerRequestDTO


@pytest.fixture
def db_session():
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_user(db_session: Session):
    user = db_session.query(User).filter(User.username == "test_optimizer_user").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="test_optimizer_user",
            email="optimizer@acc.in",
            password_hash="hashed_test_password",
            full_name="Test Optimizer Engineer",
            account_status="ACTIVE",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        role = db_session.query(Role).filter(Role.id == "QUALITY_ENGINEER").first()
        if not role:
            role = Role(
                id="QUALITY_ENGINEER",
                name="Quality Engineer",
                description="Quality role",
                is_system_role=True,
                created_at=datetime.now(timezone.utc),
            )
            db_session.add(role)
            db_session.commit()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            assigned_at=datetime.now(timezone.utc),
        )
        db_session.add(user_role)
        db_session.commit()
        db_session.refresh(user)
    return user


def test_phase_5a_trigger_optimization_run_all_recipes(db_session: Session, mock_user: User):
    """Test triggering optimization runs on various recipes including those without pre-seeded RecipeMaterials."""
    recipes = db_session.query(Recipe).filter(Recipe.is_deleted == False).limit(5).all()
    assert len(recipes) > 0

    for recipe in recipes:
        request_dto = OptimizationRunTriggerRequestDTO(
            recipe_id=recipe.recipe_code,
            plant_code="",  # Test empty/default plant code
            optimization_objective="MINIMIZE_COST",
        )

        result = MixOptimizationService.trigger_optimization_run(
            db=db_session,
            request=request_dto,
            current_user=mock_user,
            client_ip="127.0.0.1",
            user_agent="Pytest-Client",
        )

        assert result is not None
        assert result.run_id is not None
        assert result.recipe_code == recipe.recipe_code
        assert len(result.recipe_snapshot.constituents) > 0
        assert result.target_strength_snapshot.target_mean_strength_fck_prime_mpa > 0
        assert result.run_status == "CREATED"
