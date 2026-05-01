import sqlite3
import numpy as np
from math import exp
from datetime import datetime
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Flask, redirect, render_template, request, session, url_for
from tables import tables_bp
from model.predict_model import model_predict

app = Flask(__name__, template_folder="template")
app.secret_key = "1234567890"
DATABASE_PATH = Path(__file__).with_name("users.db")
app.register_blueprint(tables_bp)




def login_required(view_function):
	@wraps(view_function)
	def wrapped_view(*args, **kwargs):
		if "user_id" not in session:
			return redirect(url_for("login"))
		return view_function(*args, **kwargs)

	return wrapped_view


@app.context_processor
def inject_auth_state():
	return {
		"logged_in": "user_id" in session,
		"user_name": session.get("user_name"),
	}


@app.get("/")
def home():
	if "user_id" in session:
		return redirect(url_for("dashboard"))
	return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
	if "user_id" in session:
		return redirect(url_for("dashboard"))

	if request.method == "GET":
		return render_template("login.html", active_page="login")

	email = request.form.get("email", "").strip().lower()
	password = request.form.get("password", "")

	with sqlite3.connect(DATABASE_PATH) as conn:
		user = conn.execute(
			"SELECT id, full_name FROM users WHERE email = ? AND password = ?",
			(email, password),
		).fetchone()

	if user:
		session["user_id"] = user[0]
		session["user_name"] = user[1]
		return redirect(url_for("dashboard"))

	return render_template(
		"login.html",
		active_page="login",
		error="Invalid email or password.",
		email=email,
	)


@app.route("/signup", methods=["GET", "POST"])
def signup():
	if "user_id" in session:
		return redirect(url_for("dashboard"))

	if request.method == "GET":
		return render_template("signup.html", active_page="signup")

	full_name = request.form.get("full_name", "").strip()
	email = request.form.get("email", "").strip().lower()
	password = request.form.get("password", "")
	confirm_password = request.form.get("confirm_password", "")

	if password != confirm_password:
		return render_template(
			"signup.html",
			active_page="signup",
			error="Password and confirm password do not match.",
			full_name=full_name,
			email=email,
		)

	try:
		with sqlite3.connect(DATABASE_PATH) as conn:
			uid = f"USR-{uuid4().hex[:12].upper()}"
			conn.execute(
				"INSERT INTO users (uid, full_name, email, password) VALUES (?, ?, ?, ?)",
				(uid, full_name, email, password),
			)
	except sqlite3.IntegrityError:
		return render_template(
			"signup.html",
			active_page="signup",
			error="An account with this email already exists.",
			full_name=full_name,
			email=email,
		)

	return render_template(
		"login.html",
		active_page="login",
		success="Account created successfully. Please login.",
		email=email,
	)


@app.route("/today-data", methods=["GET", "POST"])
@login_required
def today_data():
	if request.method == "GET":
		return render_template(
			"today_data.html",
			active_page="today-data",
			today_date=datetime.now().strftime("%Y-%m-%d"),
			form_data={},
		)

	activity_date = datetime.now().date().isoformat()
	study_hours_raw = request.form.get("study_hours", "").strip()
	focus_score_raw = request.form.get("focus_score", "").strip()
	sleep_hours_raw = request.form.get("sleep_hours", "").strip()
	phone_usage_hours_raw = request.form.get("phone_usage_hours", "").strip()

	form_data = {
		"study_hours": study_hours_raw,
		"focus_score": focus_score_raw,
		"sleep_hours": sleep_hours_raw,
		"phone_usage_hours": phone_usage_hours_raw,
	}

	try:
		study_hours = float(study_hours_raw)
		focus_score = int(focus_score_raw)
		sleep_hours = float(sleep_hours_raw)
		phone_usage_hours = float(phone_usage_hours_raw)
	except ValueError:
		return render_template(
			"today_data.html",
			active_page="today-data",
			today_date=datetime.now().strftime("%Y-%m-%d"),
			form_data=form_data,
			error="Please enter valid numeric values for all fields.",
		)

	if study_hours < 0 or sleep_hours < 0 or phone_usage_hours < 0 or not 0 <= focus_score <= 100:
		return render_template(
			"today_data.html",
			active_page="today-data",
			today_date=datetime.now().strftime("%Y-%m-%d"),
			form_data=form_data,
			error="Study/sleep/phone hours must be non-negative, and focus score must be 0-100.",
		)

	input_values =[study_hours,focus_score,study_hours,phone_usage_hours]
	score = model_predict(input_values)
	""" bad code model not imported yet tetti khera but now done
	raw_score = (
		intercept
		+ study_weight * study_hours
		+ focus_weight * focus_score
		+ sleep_weight * sleep_hours
		+ phone_weight * phone_usage_hours
	)

	score = 100 / (1 + exp(-(raw_score - 550) / 100))
	score = max(0, min(100, score))
	"""
	with sqlite3.connect(DATABASE_PATH) as conn:
		conn.execute(
			"""
			INSERT INTO daily_productivity (
				user_id,
				activity_date,
				study_hours,
				focus_score,
				sleep_hours,
				phone_usage_hours,
				score
			) VALUES (?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(user_id, activity_date)
			DO UPDATE SET
				study_hours = excluded.study_hours,
				focus_score = excluded.focus_score,
				sleep_hours = excluded.sleep_hours,
				phone_usage_hours = excluded.phone_usage_hours,
				score = excluded.score
			""",
			(
				session["user_id"],
				activity_date,
				study_hours,
				focus_score,
				sleep_hours,
				phone_usage_hours,
				score,
			),
		)

	return redirect(url_for("dashboard", score=score))


@app.get("/dashboard")
@login_required
def dashboard():
	score             = request.args.get("score", type=float)
	top_percent       = None
	today_total_users = 0
	today_date        = datetime.now().date().isoformat()

	with sqlite3.connect(DATABASE_PATH) as conn:

		# latest score
		if score is None:
			latest = conn.execute(
				"""
				SELECT score FROM daily_productivity
				WHERE user_id = ?
				ORDER BY activity_date DESC LIMIT 1
				""",
				(session["user_id"],),
			).fetchone()
			score = latest[0] if latest else None

		# today's percentile
		today_row = conn.execute(
			"""
			SELECT score FROM daily_productivity
			WHERE user_id = ? AND activity_date = ? LIMIT 1
			""",
			(session["user_id"], today_date),
		).fetchone()

		today_score = None
		if today_row:
			today_score       = today_row[0]
			today_total_users = conn.execute(
				"SELECT COUNT(*) FROM daily_productivity WHERE activity_date = ?",
				(today_date,),
			).fetchone()[0]
			higher = conn.execute(
				"SELECT COUNT(*) FROM daily_productivity WHERE activity_date = ? AND score > ?",
				(today_date, today_score),
			).fetchone()[0]
			rank        = higher + 1
			top_percent = 1.0 if today_total_users <= 1 else round((rank / today_total_users) * 100, 1)

		# Graph 1: Bell curve
		all_scores = conn.execute(
			"SELECT score FROM daily_productivity WHERE activity_date = ?",
			(today_date,),
		).fetchall()
		if len(all_scores) < 5:
			all_scores = conn.execute(
				"SELECT score FROM daily_productivity"
			).fetchall()

		# Graph 2: Daily trend
		daily_rows = conn.execute(
			"""
			SELECT activity_date, score FROM daily_productivity
			WHERE user_id = ?
			ORDER BY activity_date ASC LIMIT 30
			""",
			(session["user_id"],),
		).fetchall()

		# Graph 3: Weekly average
		weekly_rows = conn.execute(
			"""
			SELECT
				strftime('%W', activity_date) as week_num,
				MIN(activity_date)            as week_start,
				ROUND(AVG(score), 2)          as avg_score,
				ROUND(AVG(study_hours), 2)    as avg_study,
				ROUND(AVG(focus_score), 2)    as avg_focus
			FROM daily_productivity
			WHERE user_id = ?
			GROUP BY week_num
			ORDER BY week_num ASC
			LIMIT 8
			""",
			(session["user_id"],),
		).fetchall()

		# Graph 4: Feature breakdown
		feature_rows = conn.execute(
			"""
			SELECT activity_date, study_hours, focus_score,
				   sleep_hours, phone_usage_hours
			FROM daily_productivity
			WHERE user_id = ?
			ORDER BY activity_date ASC
			LIMIT 14
			""",
			(session["user_id"],),
		).fetchall()

	# Bell curve computation
	all_scores_arr = []
	for row in all_scores:
		try:
			all_scores_arr.append(float(row[0]))
		except (TypeError, ValueError):
			continue
	bell_x, bell_y = [], []

	if len(all_scores_arr) >= 2:
		mu    = float(np.mean(all_scores_arr))
		sigma = float(np.std(all_scores_arr)) or 1.0
		xs    = np.linspace(max(0, mu - 4*sigma), min(100, mu + 4*sigma), 200)
		ys    = (1/(sigma * np.sqrt(2*np.pi))) * np.exp(-0.5*((xs - mu)/sigma)**2)
		bell_x = [round(float(v), 3) for v in xs]
		bell_y = [round(float(v), 6) for v in ys]
	else:
		mu, sigma = 50.0, 15.0

	# Daily trend arrays
	dates       = [r[0] for r in daily_rows]
	scores_list = [round(r[1], 1) for r in daily_rows]

	trend_line = []
	if len(scores_list) > 1:
		x          = np.arange(len(scores_list))
		m, b       = np.polyfit(x, scores_list, 1)
		trend_line = [round(float(m*i + b), 2) for i in x]
	else:
		trend_line = scores_list[:]

	# Weekly arrays kod 
	week_labels = [r[1] for r in weekly_rows]
	week_scores = [r[2] for r in weekly_rows]
	week_study  = [r[3] for r in weekly_rows]
	week_focus  = [r[4] for r in weekly_rows]

	# Feature breakdown arrays
	feat_dates  = [r[0] for r in feature_rows]
	feat_study  = [r[1] for r in feature_rows]
	feat_focus  = [r[2] for r in feature_rows]
	feat_sleep  = [r[3] for r in feature_rows]
	feat_phone  = [r[4] for r in feature_rows]

	return render_template(
		"dashboard.html",
		active_page       = "dashboard",
		score             = round(score, 1) if score is not None else None,
		top_percent       = top_percent,
		today_total_users = today_total_users,
		bell_x            = bell_x,
		bell_y            = bell_y,
		user_score        = today_score,
		bell_mean         = round(mu, 2),
		bell_sigma        = round(sigma, 2),
		dates             = dates,
		scores            = scores_list,
		trend_line        = trend_line,
		week_labels       = week_labels,
		week_scores       = week_scores,
		week_study        = week_study,
		week_focus        = week_focus,
		feat_dates        = feat_dates,
		feat_study        = feat_study,
		feat_focus        = feat_focus,
		feat_sleep        = feat_sleep,
		feat_phone        = feat_phone,
	)


@app.get("/logout")
def logout():
	session.clear()
	return redirect(url_for("login"))


if __name__ == "__main__":
	app.run(debug=True)