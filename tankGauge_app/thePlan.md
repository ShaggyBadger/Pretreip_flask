# 🛠 `tankGauge_app` Structure Overview

This app handles everything related to tank gauge data:
- Loading data from spreadsheets
- Analyzing and reprocessing data
- User interface for admin, planning, and delivery
- Web-form-based tank audits
- HTML rendering of store tank charts and info

## 📁 Folder & File Layout

tankGauge_app/
├── init.py
│   # Registers the Flask Blueprint
│   # Initializes app-specific config or dependencies
│
├── routes.py
│   # All Flask route handlers for tankGauge
│   # Uses the Blueprint defined in init.py
│
├── models.py
│   # SQLAlchemy ORM models related to tank data
│   # E.g., Store, Tank, Audit, DeliveryPlan
│
├── processing.py
│   # Functions/classes to load and process spreadsheet data
│   # Handles “import new data”, “reprocess updated data”, etc.
│
├── admin.py
│   # Admin routes or classes for reviewing and managing data
│   # (Optional) Could be tied to Flask-Admin or custom views
│
├── planning.py
│   # Handles tank delivery planning logic
│   # Forecasting, scheduling deliveries, etc.
│
├── delivery.py
│   # Tools for managing or tracking deliveries
│   # Possibly integrates with planning
│
├── charts.py
│   # Logic to render/store HTML versions of tank charts
│   # Could include data visualization generation
│
├── audit.py
│   # Tank audit logic
│   # Users input stick readings + printout values to track discrepancies
│
├── forms.py
│   # Flask-WTForms (if needed)
│   # E.g., for audits, admin filters, or delivery planning forms
│
├── templates/
│   └── tankGauge/
│       # Jinja2 templates used by this app
│       # E.g., index.html, audit_form.html, delivery_plan.html
│
└── static/
└── tankGauge/
# Optional CSS or JS files specific to this app
