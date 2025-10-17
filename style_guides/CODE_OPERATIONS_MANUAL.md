# 💻 CODE OPERATIONS MANUAL — Coding Style Guide

This ain’t just a pile of code; it’s an engine. And every part’s gotta be clean, reliable, and easy to fix when you’re on the side of the road at 3 a.m. This manual makes sure our machine runs smooth. Write code that’s built to last, not just to work once.

Follow these rules. Your future self will thank you.

---

## 1. Project Stack

This rig is built on a simple, sturdy chassis. Don’t add chrome unless it makes the truck go faster.

- **Backend:** Python 3.x, Flask
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Database:** MySQL (production), SQLite (for quick local tests if needed)
- **Deployment:** Gunicorn, Nginx, Docker
- **Key Libraries:** SQLAlchemy, Pandas, Bootstrap

## 2. File & Folder Conventions

Keep your toolbox organized. No one likes searchin’ for a 10mm socket.

- **Flask Apps:** Each major feature gets its own app folder (e.g., `pretrip_app`, `speedGauge_app`).
- **Templates & Static:** Keep `templates/` and `static/` inside their respective app folders.
- **Blueprints:** Use Flask Blueprints to keep routes organized within their apps.
- **Naming:** Use `snake_case` for all filenames and directories (e.g., `db_management.py`).

## 3. Code Formatting Rules

Cleanliness is next to godliness. Or at least, it makes debugging less of a nightmare.

- **Python:** Follow PEP 8. No excuses. Use a linter like `flake8` or `black` to enforce it automatically.
- **JavaScript:** Use a standard, modern style. `Prettier` is your friend.
- **HTML/CSS:** Keep it clean. Indent properly. Don’t write CSS inline unless you’ve got a damn good reason.
- **Line Length:** Keep lines under 99 characters. Your monitor is wide, but your brain ain’t.

## 4. Naming Conventions

If you have to guess what a variable does, you named it wrong.

- **Python Variables:** `snake_case` (e.g., `driver_name`).
- **Python Functions:** `snake_case` (e.g., `calculate_fuel_usage()`).
- **Python Classes:** `PascalCase` (e.g., `class VehicleTemplate:`).
- **JavaScript Variables:** `camelCase` (e.g., `let driverName;`).
- **Constants:** `ALL_CAPS_SNAKE_CASE` (e.g., `MAX_SPEED_LIMIT`).
- **Be descriptive:** `dn` is not a variable name. `dot_number` is.

## 5. Commenting & Documentation Standards

Comments should explain *why*, not *what*. If the code is so clever you have to explain it, it’s probably too clever.

- **Docstrings:** Use them for all public modules, functions, and classes. Explain what it does, its args, and what it returns.
- **Inline Comments:** Use sparingly. Good code should be self-documenting.
- **`# TODO:`:** Use for things that need doin’. Add your name and a date if you can.
  ```python
  # TODO (Josh, 2025-10-18): Refactor this to use the new API endpoint.
  ```

## 6. Version Control Rules

Git is our logbook. Keep it clean.

- **Branching:**
  - `main`: Always stable, always deployable.
  - `develop`: The main work branch. All feature branches come from here.
  - `feature/<name>`: For new stuff (e.g., `feature/add-tire-pressure-tool`).
  - `fix/<name>`: For bug squashing (e.g., `fix/login-bug`).
- **Commits:**
  - Write clear, concise commit messages.
  - Start with a verb (e.g., `Fix:`, `Add:`, `Refactor:`).
  - Reference issue numbers if you got ‘em.
  - Example: `Fix: Corrected fuel calculation for off-road mileage.`
- **Merges:** Use Pull Requests to merge into `develop`. Don’t push directly.

## 7. Error Handling & Logging

Things break. Be ready for it.

- **Error Handling:** Use `try...except` blocks for anything that talks to the outside world (files, networks, databases).
- **Logging:** Use Flask’s built-in logger. Log errors with stack traces. Log important events (e.g., user login, data import). Don’t log sensitive data.

## 8. Security Practices

Don’t leave the keys in the ignition.

- **Secrets:** Use environment variables (`.env` file) for all secrets (API keys, database passwords). Never hardcode them.
- **Input Validation:** Trust no one. Sanitize and validate all user input on both the client and server side.
- **SQL Injection:** Use an ORM (SQLAlchemy) or parameterized queries. Never use string formatting to build SQL queries.

## 9. Testing & Deployment Notes

- **Testing:** Write tests for your code. At a minimum, write unit tests for critical business logic.
- **Deployment:** See the `DEPLOYMENT_ORDERS.md` for the full procedure.

---
*This manual is the law of the land. Keep your code clean, or you’ll be on latrine duty.*
