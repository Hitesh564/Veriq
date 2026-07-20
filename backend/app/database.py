from sqlmodel import SQLModel, create_engine, Session
from app.config import DATABASE_URL

# Connect arguments specifically for SQLite thread handling
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

def init_db():
    # Lazy import to avoid circular dependency issues
    from app.subscriptions.models import Plan
    SQLModel.metadata.create_all(engine)
    
    # Seed default plans if not already present
    try:
        with Session(engine) as session:
            free_plan = session.get(Plan, "free")
            if not free_plan:
                free_plan = Plan(
                    id="free",
                    name="Free Plan",
                    monthly_price=0.0,
                    interview_limit=3,
                    features_json='["3 Free mock interviews", "Basic performance card", "Conceptual question verification"]',
                    active=True
                )
                session.add(free_plan)
                print("Seeded Free Plan.")
                
            pro_plan = session.get(Plan, "pro")
            if not pro_plan:
                pro_plan = Plan(
                    id="pro",
                    name="Pro Plan",
                    monthly_price=19.99,
                    interview_limit=-1,
                    features_json='["Unlimited mock interviews", "Unlimited AI report cards", "Future premium features", "Full resume technical gap analysis"]',
                    active=True
                )
                session.add(pro_plan)
                print("Seeded Pro Plan.")
                
            session.commit()
    except Exception as e:
        print(f"Error seeding default plans: {e}")
    
    # Proactively check if columns exist in tables, add them if not (DB agnostic)
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        
        # 1. Check Transcript columns
        if "transcript" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("transcript")]
            with engine.begin() as conn:
                if "audio_url" not in columns:
                    conn.execute(text("ALTER TABLE transcript ADD COLUMN audio_url VARCHAR"))
                    print("Successfully added audio_url column to transcript table.")
                if "turn_metadata_json" not in columns:
                    conn.execute(text("ALTER TABLE transcript ADD COLUMN turn_metadata_json VARCHAR"))
                    print("Successfully added turn_metadata_json column to transcript table.")
                    
        # 2. Check Interview columns
        if "interview" in inspector.get_table_names():
            int_columns = [col["name"] for col in inspector.get_columns("interview")]
            with engine.begin() as conn:
                for col in ["candidate_profile_json", "job_profile_json", "company_profile_json", "blueprint_json", "user_id", "resume_path"]:
                    if col not in int_columns:
                        default_clause = " DEFAULT 'default'" if col == "user_id" else ""
                        conn.execute(text(f"ALTER TABLE interview ADD COLUMN {col} VARCHAR{default_clause}"))
                        print(f"Successfully added {col} column to interview table.")
    except Exception as e:
        print(f"Error checking/adding columns to tables: {e}")

def get_session():
    with Session(engine) as session:
        yield session
        
# For direct scripts if needed
def get_direct_session():
    return Session(engine)
