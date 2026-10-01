import os, secrets, csv, io
from datetime import date, datetime
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from models import db, User, Expense, Budget, CATEGORIES, PAYMENTS

app = Flask(__name__)
PROD = os.environ.get("APP_ENV") == "production"
_key = os.environ.get("SECRET_KEY")
if PROD and not _key:
    raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")
_db = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config.update(
    SECRET_KEY=_key or "dev-only-key",
    SQLALCHEMY_DATABASE_URI=_db.replace("postgres://", "postgresql://", 1),
    SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=PROD,
    MAX_CONTENT_LENGTH=1024 * 1024,
)
if PROD:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify(error="Authentication required"), 401
    return redirect(url_for("login"))


# ---------- helpers ----------
def parse_expense(data):
    """Validate input; returns (clean_dict, error)."""
    try:
        amount = float(data.get("amount"))
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return None, "Amount must be a positive number."
    category = data.get("category")
    if category not in CATEGORIES:
        return None, "Invalid category."
    payment = data.get("payment_method") or "UPI"
    if payment not in PAYMENTS:
        return None, "Invalid payment method."
    try:
        d = datetime.strptime(data.get("date") or date.today().isoformat(), "%Y-%m-%d").date()
    except ValueError:
        return None, "Date must be YYYY-MM-DD."
    return {"amount": amount, "category": category, "payment_method": payment, "date": d,
            "description": (data.get("description") or "").strip()[:200]}, None


def month_total(user_id, ym):
    rows = Expense.query.filter_by(user_id=user_id).all()
    return sum(e.amount for e in rows if e.date.strftime("%Y-%m") == ym)


def category_totals(user_id, ym):
    out = defaultdict(float)
    for e in Expense.query.filter_by(user_id=user_id).all():
        if e.date.strftime("%Y-%m") == ym:
            out[e.category] += e.amount
    return out


def prev_month(ym):
    y, m = map(int, ym.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def insights(user_id, ym):
    cur, prev = category_totals(user_id, ym), category_totals(user_id, prev_month(ym))
    msgs = []
    for cat, amt in sorted(cur.items(), key=lambda x: -x[1]):
        p = prev.get(cat, 0)
        if p > 0:
            change = (amt - p) / p * 100
            if abs(change) >= 5:
                word = "more" if change > 0 else "less"
                msgs.append(f"You spent {abs(change):.0f}% {word} on {cat} this month compared with last month.")
    if cur:
        top = max(cur, key=cur.get)
        msgs.append(f"Your biggest spending category this month is {top} (₹{cur[top]:,.0f}).")
    return msgs[:4] or ["Add more expenses to see spending insights."]


def summary(user_id):
    today = date.today()
    ym = today.strftime("%Y-%m")
    exps = Expense.query.filter_by(user_id=user_id).all()
    budget = Budget.query.filter_by(user_id=user_id, month=ym).first()
    spent = month_total(user_id, ym)
    cats = category_totals(user_id, ym)
    monthly, daily = defaultdict(float), defaultdict(float)
    for e in exps:
        monthly[e.date.strftime("%Y-%m")] += e.amount
        if e.date.strftime("%Y-%m") == ym:
            daily[e.date.day] += e.amount
    last_days = (date(today.year + (today.month == 12), today.month % 12 + 1, 1) - date.resolution).day
    return {
        "total": sum(e.amount for e in exps),
        "this_month": spent,
        "today": sum(e.amount for e in exps if e.date == today),
        "highest": max((e.amount for e in exps), default=0),
        "categories": dict(cats),
        "monthly": dict(sorted(monthly.items())[-6:]),
        "daily": {str(d): daily.get(d, 0) for d in range(1, last_days + 1)},
        "budget": budget.amount if budget else None,
        "remaining": (budget.amount - spent) if budget else None,
        "insights": insights(user_id, ym),
    }


# ---------- auth ----------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        if not name or "@" not in email or len(pw) < 6:
            flash("Enter a name, valid email and a password of 6+ characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("That email is already registered.", "danger")
        else:
            u = User(name=name, email=email, password=generate_password_hash(pw))
            db.session.add(u)
            db.session.commit()
            login_user(u)
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if u and check_password_hash(u.password, request.form.get("password", "")):
            login_user(u)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------- pages ----------
@app.route("/dashboard")
@login_required
def dashboard():
    recent = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc(), Expense.id.desc()).limit(5).all()
    return render_template("dashboard.html", s=summary(current_user.id), recent=recent)


@app.route("/budget", methods=["POST"])
@login_required
def set_budget():
    try:
        amt = float(request.form.get("amount"))
        if amt <= 0:
            raise ValueError
    except (TypeError, ValueError):
        flash("Budget must be a positive number.", "danger")
        return redirect(url_for("dashboard"))
    ym = date.today().strftime("%Y-%m")
    b = Budget.query.filter_by(user_id=current_user.id, month=ym).first()
    if b:
        b.amount = amt
    else:
        db.session.add(Budget(amount=amt, month=ym, user_id=current_user.id))
    db.session.commit()
    flash("Monthly budget saved.", "success")
    return redirect(url_for("dashboard"))


def filtered_query():
    q = Expense.query.filter_by(user_id=current_user.id)
    a = request.args
    if a.get("category"):
        q = q.filter_by(category=a["category"])
    if a.get("payment_method"):
        q = q.filter_by(payment_method=a["payment_method"])
    try:
        if a.get("from"):
            q = q.filter(Expense.date >= datetime.strptime(a["from"], "%Y-%m-%d").date())
        if a.get("to"):
            q = q.filter(Expense.date <= datetime.strptime(a["to"], "%Y-%m-%d").date())
        if a.get("min"):
            q = q.filter(Expense.amount >= float(a["min"]))
        if a.get("max"):
            q = q.filter(Expense.amount <= float(a["max"]))
    except ValueError:
        flash("Some filters were invalid and ignored.", "warning")
    if a.get("q"):
        q = q.filter(Expense.description.ilike(f"%{a['q']}%"))
    return q.order_by(Expense.date.desc(), Expense.id.desc())


@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    if request.method == "POST":
        data, err = parse_expense(request.form)
        if err:
            flash(err, "danger")
        else:
            db.session.add(Expense(user_id=current_user.id, **data))
            db.session.commit()
            flash("Expense added.", "success")
        return redirect(url_for("expenses"))
    items = filtered_query().all()
    return render_template("expenses.html", items=items, total=sum(e.amount for e in items),
                           categories=CATEGORIES, payments=PAYMENTS, today=date.today().isoformat())


@app.route("/expenses/<int:eid>/edit", methods=["POST"])
@login_required
def edit_expense(eid):
    e = Expense.query.filter_by(id=eid, user_id=current_user.id).first_or_404()
    data, err = parse_expense(request.form)
    if err:
        flash(err, "danger")
    else:
        for k, v in data.items():
            setattr(e, k, v)
        db.session.commit()
        flash("Expense updated.", "success")
    return redirect(url_for("expenses"))


@app.route("/expenses/<int:eid>/delete", methods=["POST"])
@login_required
def delete_expense(eid):
    e = Expense.query.filter_by(id=eid, user_id=current_user.id).first_or_404()
    db.session.delete(e)
    db.session.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses"))


# ---------- security ----------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST" and not request.path.startswith("/api/"):
        tok = session.get("_csrf")
        if not tok or not secrets.compare_digest(request.form.get("csrf_token", ""), tok):
            abort(400)


@app.after_request
def headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Referrer-Policy"] = "same-origin"
    if PROD:
        r.headers["Strict-Transport-Security"] = "max-age=31536000"
    return r


for _c, _m in [(400, "Bad request or expired form. Please go back and retry."), (404, "Page not found."), (500, "Something went wrong on our side.")]:
    app.register_error_handler(_c, lambda e, c=_c, m=_m: (render_template("error.html", code=c, msg=m), c))


# ---------- more pages ----------
@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html", s=summary(current_user.id))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        act, f = request.form.get("action"), request.form
        if act == "name" and f.get("name", "").strip():
            current_user.name = f["name"].strip()[:80]
            db.session.commit()
            flash("Profile updated.", "success")
        elif act == "password":
            if not check_password_hash(current_user.password, f.get("old", "")):
                flash("Current password is incorrect.", "danger")
            elif len(f.get("new", "")) < 6:
                flash("New password must be 6+ characters.", "danger")
            else:
                current_user.password = generate_password_hash(f["new"])
                db.session.commit()
                flash("Password changed.", "success")
        elif act == "delete":
            u = current_user._get_current_object()
            logout_user()
            db.session.delete(u)
            db.session.commit()
            flash("Account deleted.", "info")
            return redirect(url_for("login"))
        return redirect(url_for("profile"))
    return render_template("profile.html")


@app.route("/expenses/export")
@login_required
def export_csv():
    safe = lambda v: "'" + v if v[:1] in ("=", "+", "-", "@") else v
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "Category", "Description", "Payment", "Amount"])
    for e in filtered_query().all():
        w.writerow([e.date, e.category, safe(e.description or ""), e.payment_method, e.amount])
    return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=expenses.csv"})


# ---------- REST API ----------
@app.route("/api/expenses", methods=["GET"])
@login_required
def api_list():
    return jsonify([e.to_dict() for e in filtered_query().all()])


@app.route("/api/expenses", methods=["POST"])
@login_required
def api_create():
    data, err = parse_expense(request.get_json(silent=True) or {})
    if err:
        return jsonify(error=err), 400
    e = Expense(user_id=current_user.id, **data)
    db.session.add(e)
    db.session.commit()
    return jsonify(e.to_dict()), 201


@app.route("/api/expenses/<int:eid>", methods=["PUT"])
@login_required
def api_update(eid):
    e = Expense.query.filter_by(id=eid, user_id=current_user.id).first()
    if not e:
        return jsonify(error="Not found"), 404
    body = request.get_json(silent=True) or {}
    merged = {**e.to_dict(), **body}
    data, err = parse_expense(merged)
    if err:
        return jsonify(error=err), 400
    for k, v in data.items():
        setattr(e, k, v)
    db.session.commit()
    return jsonify(e.to_dict())


@app.route("/api/expenses/<int:eid>", methods=["DELETE"])
@login_required
def api_delete(eid):
    e = Expense.query.filter_by(id=eid, user_id=current_user.id).first()
    if not e:
        return jsonify(error="Not found"), 404
    db.session.delete(e)
    db.session.commit()
    return jsonify(deleted=eid)


@app.route("/api/expenses/summary")
@login_required
def api_summary():
    return jsonify(summary(current_user.id))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
