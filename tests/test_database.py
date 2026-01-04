import pytest
from shared.database import init_db, get_db, Base
from shared.models import Signal, AgentQuestion, AgentKnowledge
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory DB for testing
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_signal_creation(db_session):
    sig = Signal(name="TEST_SIGNAL", value="some_value")
    db_session.add(sig)
    db_session.commit()

    retrieved = db_session.query(Signal).filter_by(name="TEST_SIGNAL").first()
    assert retrieved is not None
    assert retrieved.value == "some_value"
    assert retrieved.is_active is True

def test_agent_question(db_session):
    q = AgentQuestion(question="What is this?", source_agent="test_agent")
    db_session.add(q)
    db_session.commit()

    retrieved = db_session.query(AgentQuestion).first()
    assert retrieved.question == "What is this?"
    assert retrieved.status == "pending"

def test_agent_knowledge(db_session):
    k = AgentKnowledge(category="QA_BLOCKER", content="Blocked on DB", source_agent="tester")
    db_session.add(k)
    db_session.commit()

    retrieved = db_session.query(AgentKnowledge).filter_by(category="QA_BLOCKER").first()
    assert retrieved.content == "Blocked on DB"
