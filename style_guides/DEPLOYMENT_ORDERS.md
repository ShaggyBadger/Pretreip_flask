# ⚙️ DEPLOYMENT ORDERS — DevOps & Workflow Guide

Alright, time to ship it. A fancy rig in the garage is just a trophy. A rig on the road is a tool. This document is our pre-flight checklist. Follow it every time. No shortcuts. No excuses. A clean deployment is a good deployment.

These orders keep our operation smooth and prevent us from blowing a gasket in production.

---

## 1. Branch Strategy & Environment Setup

- **`main` Branch:** This is the highway. It’s for production code only. You don’t push to it directly.
- **`develop` Branch:** This is the workshop. All new work gets merged here for testing.
- **Feature Branches (`feature/...`):** Where you build new stuff. Branch off `develop`.
- **Hotfix Branches (`fix/...`):** For emergency repairs. Branch off `main`, then merge back to both `main` and `develop`.

**Local Setup:** Your machine should mirror the production environment as much as possible. Use Docker if you can. Your `.env` file is your local config.

## 2. Commit & Tag Naming

- **Commits:** Keep ‘em clean and descriptive. Follow the convention:
  - `Fix: Description of the fix.`
  - `Add: Description of the new feature.`
  - `Refactor: Description of the code change.`
  - `Docs: Description of the documentation change.`
  - `Style: Formatting or UI changes.`
- **Tags:** We tag releases on the `main` branch. Use semantic versioning (e.g., `v1.0.0`, `v1.0.1`).

## 3. Pull Request / Review Checklist

Before you merge to `develop`, you do a PR. Since it’s a one-man shop, you’re reviewin’ your own work. Be honest.

- [ ] **Self-Review:** Did you read your own code? Does it make sense?
- [ ] **Testing:** Did you write and run tests for the new code?
- [ ] **Linting:** Does the code pass the linter (`flake8`, `prettier`)?
- [ ] **Functionality:** Does it do what it’s supposed to do? Did you check it in the browser?
- [ ] **Secrets:** Did you accidentally hardcode any passwords or keys? (If so, fix it *before* you commit.)
- [ ] **Commit History:** Is your commit history clean and easy to read?

## 4. Environment Configuration

- **`.env` file:** This file is for local development ONLY.
- **DO NOT COMMIT `.env` FILES.** Add `.env` to your `.gitignore`.
- **Production Config:** On the production server, secrets are managed as environment variables set by the system or a secure vault. Don’t put a `.env` file in production.
- **`.env.example`:** Keep this file in the repo. It should list all the variables the app needs, but with placeholder or empty values.

## 5. Backup & Rollback Protocols

- **Database:** Regular backups are a must. Set up a cron job on the server to run `mysqldump` and save it to a secure location daily.
- **Rollback:** If a deployment goes sideways, the fastest way to roll back is to re-deploy the previous stable tag from the `main` branch.

## 6. Deployment Steps

This is the mission. Follow it to the letter.

1.  **Merge to `main`:** Ensure your `develop` branch is stable and all tests are passing. Merge `develop` into `main`.
2.  **Tag the Release:** Create a new version tag on `main` (e.g., `git tag v1.2.0`).
3.  **Push to Remote:** `git push origin main --tags`.
4.  **SSH into Production Server:** Get secure access to the machine.
5.  **Pull the Code:** Navigate to the project directory and run `git pull origin main`.
6.  **Install Dependencies:** If you added new ones, update your virtual environment: `pip install -r requirements.txt`.
7.  **Run Migrations:** If the database schema changed, run migrations: `flask db upgrade`.
8.  **Restart the Application:** Restart the Gunicorn service to apply the changes: `sudo systemctl restart myapp` (or whatever your service is called).

## 7. Continuous Integration (CI) Notes

Right now, we’re the CI pipeline. In the future, we can set up GitHub Actions to automatically run tests and linters on every push. For now, do it manually. It builds character.

## 8. Monitoring & Logging After Deployment

- **Check the Logs:** After deployment, tail the application logs and the Nginx logs for a few minutes. Make sure there are no new errors.
- **Test in Production:** Open the live site. Click around. Make sure the new stuff works and the old stuff ain’t broken.

---
*Deployments are serious business. Stay sharp. Stay focused. And don’t break the build.*
