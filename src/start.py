from circus import get_arbiter

# start mail monitoring
monitor = dict(
    name="monitor",
    cmd="python monitor.py",
    copy_env=True,
    copy_path=True,
)

# start chart precache worker
precache = dict(
    name="precache",
    cmd="python precache.py",
    copy_env=True,
    copy_path=True,
)

# start flask frontend
dashboard = dict(
    name="dashboard",
    cmd="python -m flask run --host=0.0.0.0 --port=80",
    env={"FLASK_APP": "dashboard.py", "FLASK_ENV": "production", "FLASK_DEBUG": "0"},
    copy_env=True,
    copy_path=True,
)

arbiter = get_arbiter([monitor, precache, dashboard])
try:
    arbiter.start()
finally:
    arbiter.stop()
