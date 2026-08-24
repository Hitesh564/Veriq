import sys
from decimal import Decimal
from sqlmodel import Session
from app.database import engine
from app.subscriptions.models import Plan

def seed_plans():
    """Seeds default subscription plans if they do not exist."""
    print("Starting database seeding...")
    try:
        with Session(engine) as session:
            free_plan = session.get(Plan, "free")
            if not free_plan:
                free_plan = Plan(
                    id="free",
                    name="Free Plan",
                    monthly_price=Decimal("0.00"),
                    interview_limit=3,
                    features_json='["3 Free mock interviews", "Basic performance card", "Conceptual question verification"]',
                    active=True
                )
                session.add(free_plan)
                print("Seeded Free Plan.")
            else:
                print("Free Plan already exists.")
                
            pro_plan = session.get(Plan, "pro")
            if not pro_plan:
                pro_plan = Plan(
                    id="pro",
                    name="Pro Plan",
                    monthly_price=Decimal("19.99"),
                    interview_limit=-1,
                    features_json='["Unlimited mock interviews", "Unlimited AI report cards", "Future premium features", "Full resume technical gap analysis"]',
                    active=True
                )
                session.add(pro_plan)
                print("Seeded Pro Plan.")
            else:
                print("Pro Plan already exists.")
                
            session.commit()
            print("Database seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding database plans: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_plans()
