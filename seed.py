"""Optional: python seed.py  -> creates demo@expenseflow.com / demo123 with sample data."""
import random
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app import app
from models import db, User, Expense, Budget, CATEGORIES, PAYMENTS

with app.app_context():
    if not User.query.filter_by(email="demo@expenseflow.com").first():
        u = User(name="Demo User", email="demo@expenseflow.com", password=generate_password_hash("demo123"))
        db.session.add(u); db.session.commit()
        for i in range(90):
            db.session.add(Expense(user_id=u.id, amount=random.randint(50, 1500), category=random.choice(CATEGORIES),
                description="Sample expense", payment_method=random.choice(PAYMENTS), date=date.today() - timedelta(days=i)))
        db.session.add(Budget(user_id=u.id, amount=10000, month=date.today().strftime("%Y-%m")))
        db.session.commit()
        print("Seeded demo user: demo@expenseflow.com / demo123")
