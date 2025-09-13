# 🚛 Pretreip_flask

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-brightgreen.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](./LICENSE)

**Pretreip_flask** is a command and control platform engineered for the transportation and logistics sector. It provides mission-critical tools for fleet readiness, safety protocol enforcement, and operational dominance, centralizing vehicle inspections, driver performance analytics, and fuel logistics.

---

## 🎯 Core Capabilities

The platform is organized into several key operational modules.

| Capability | Intel Briefing |
| --- | --- |
| 🔐 **Personnel Security** | Secure operative registration and authentication with role-based clearance levels. Includes a command panel for personnel oversight. |
| 🛠 **Fleet Readiness** | Execute digital vehicle inspections using adaptable mission templates. Document deficiencies, assign threat levels, and upload visual reconnaissance. |
| 📈 **Performance Analytics** | Process and exploit SpeedGauge driver performance intel. Execute deep data analysis, conduct audits, and leverage a dedicated API for systems integration. |
| ⛽ **Fuel Logistics** | Command fuel logistics across multiple sites. Monitor supply lines, plan refueling operations, and calculate reserves with precision tank charts. |
| 🖥 **Command Console** | A central console for administrators to control all operational modules, from intel uploads to operative and system configuration. |

---

## 🛰️ Situational Awareness

*(placeholder for a screenshot or GIF of the main command dashboard)*

![Application Screenshot](https://via.placeholder.com/800x450.png?text=Pretreip_flask+Command+Dashboard)

---

## 🛠️ Arsenal

This platform is built on a battle-tested, Python-based stack to ensure robust and scalable performance in the field.

- **Core Framework:** **Python** & **Flask**
- **Data Store:** **MySQL**
- **ORM & Migrations:** **SQLAlchemy** & **Flask-Migrate** (Alembic)
- **Intel Processing:** **Pandas** & **NumPy**
- **UI/UX:** **Jinja2** & **Bootstrap 5**
- **Deployment:** **Gunicorn**

For a complete manifest of all ordnance, see the `requirements.txt` file.

---

## 🔌 Systems Integration

The `speedGauge_app` contains the `Api` service class, a critical component for querying and processing operative data for front-end mission displays. Here is a standard implementation within a route:

```python
from flask import render_template
from speedGauge_app.SpeedgaugeApi import Api

# Example route in speedGauge_app/routes.py
@speedgauge_blueprint.route('/operative/<driver_id>')
def operative_dashboard(driver_id):
    # Instantiate API for a specific operative
    sg_api = Api(driver_id=driver_id)

    # Assemble and build the performance history
    report_data = sg_api.build_speedgauge_report()

    # Transmit data to the command console display
    return render_template('operative_dashboard.html', data=report_data)
```

---

## 🗺️ Deployment Blueprint

The platform is constructed with a modular, blueprint-based architecture for tactical separation of concerns.

```
/Pretreip_flask
│
├── run.py                # Entry point for local development
├── wsgi.py               # WSGI entry point for field deployment
├── requirements.txt      # Dependency manifest
├── .env.example          # Example environment parameters
├── db_schema.md          # Database schema schematics
│
├── /migrations/          # Database migration scripts
│
├── /flask_app/           # Core application package
│   ├── models/           # SQLAlchemy data models
│   ├── templates/        # Jinja2 UI templates
│   └── static/           # Static assets (CSS, JS, images)
│
├── /admin_app/           # Blueprint for the Command Console
├── /auth_app/            # Blueprint for Personnel Authentication
├── /speedGauge_app/      # Blueprint for Performance Analytics & API
└── /tankGauge_app/       # Blueprint for Fuel Logistics
```

---

## 🚀 Deployment Protocol

Follow these instructions to deploy the system on your local machine.

### 1. Mission Requirements

- Python 3.11+
- A running MySQL server instance

### 2. System Assembly

1.  **Acquire the source code:**
    ```bash
    git clone https://github.com/your-username/Pretreip_flask.git
    cd Pretreip_flask
    ```

2.  **Establish a secure virtual environment:**
    ```bash
    # For Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    py -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies from the manifest:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration & Calibration

1.  **Provision the database:**
    - Access your MySQL instance and execute the following command:
      ```sql
      CREATE DATABASE pretrip_db;
      ```

2.  **Set environment parameters:**
    - Copy the example parameter file to create your local configuration:
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file with your database credentials and a unique secret key:
      ```dotenv
      FLASK_APP=run.py
      FLASK_DEBUG=True
      SECRET_KEY='generate-a-strong-and-secret-key'
      DB_USER='your_mysql_user'
      DB_PASSWORD='your_mysql_password'
      DB_HOST='localhost'
      DB_PORT='3306'
      DB_NAME='pretrip_db'
      ```

3.  **Synchronize the database schema:**
    - Execute the following command to apply the latest schema.
      ```bash
      flask db upgrade
      ```

### 4. Launch Sequence

-   **For Local Development / Testing:**
    Engage the Flask development server.
    ```bash
    flask run
    ```

-   **For Field Deployment:**
    Deploy with a production-grade WSGI server like Gunicorn.
    ```bash
    gunicorn --bind 0.0.0.0:8000 wsgi:app
    ```

Once launched, the command console is accessible at `http://127.0.0.1:5000` (for development).

---

## 🤝 Reinforcements

Reinforcements are welcome. Report enemy contact (bugs), request new hardware (features), or submit your own modifications via pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/NewOrdnance`)
3.  Commit your Changes (`git commit -m 'Add some NewOrdnance'`)
4.  Push to the Branch (`git push origin feature/NewOrdnance`)
5.  Open a Pull Request
