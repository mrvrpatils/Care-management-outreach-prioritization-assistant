# Care Management Outreach Prioritization Assistant - Database & Cloud Deployment Guide
### (MySQL Workbench for Local Dev | Supabase PostgreSQL for Cloud Run, Render & Vercel)

---

## 1. Architecture Overview

- **Local Development**: Uses **MySQL Workbench** (or SQLite fallback) on your machine.
  - Connection string: `DATABASE_URL=mysql+pymysql://root:mysql@localhost:3306/care_management`
- **Cloud Deployment**: Uses **Supabase PostgreSQL** for cloud-hosted persistence.
  - Connection string: `DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres` (or Transaction Pooler URL).
  - Target Platforms: **Google Cloud Run**, **Render**, and **Vercel**.

---

## 2. Populating All Data into Supabase

You have **two easy ways** to populate all 10,000 members, outreach statuses, campaigns, and login accounts into Supabase:

### Method A: Automated Python Script (Recommended)
Run the automated script from your project root:
```bash
python backend/scripts/push_data_to_supabase.py --target-url "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
```
*Tip: If using Supabase Connection Pooling (port 6543), provide that URI directly.*

### Method B: Supabase Dashboard SQL Editor
1. Open your project on [Supabase Dashboard](https://supabase.com/dashboard).
2. Go to **SQL Editor** in the left sidebar.
3. Click **New Query**.
4. Open and copy the contents of `backend/scripts/supabase_setup.sql`.
5. Paste into the SQL editor and click **Run** (`Ctrl + Enter`).
6. All tables (`members`, `outreach_statuses`, `campaigns`, `login`) and records are created instantly!

---

## 3. Deploying to Google Cloud Run

### Option 1: Direct Deployment via Google Cloud CLI (`gcloud`)
```bash
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

# 2. Build and Deploy Container to Cloud Run
gcloud run deploy care-management-assistant \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" \
  --set-env-vars "GEMINI_API_KEY=your_gemini_api_key"
```

### Option 2: Cloud Run via Container Registry / Artifact Registry
```bash
# Build image
docker build -t gcr.io/YOUR_GCP_PROJECT_ID/care-management-assistant:latest .
docker push gcr.io/YOUR_GCP_PROJECT_ID/care-management-assistant:latest

# Deploy image
gcloud run deploy care-management-assistant \
  --image gcr.io/YOUR_GCP_PROJECT_ID/care-management-assistant:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

---

## 4. Deploying to Render

1. Create an account on [Render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Select **Docker** environment.
5. In **Environment Variables**, add:
   - `DATABASE_URL` = `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   - `GEMINI_API_KEY` = `your_gemini_api_key`
6. Click **Create Web Service**. Render will automatically build the `Dockerfile` and launch your live URL.

---

## 5. Deploying to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` from the root directory:
```bash
vercel
```
3. Set your environment variables in Vercel Project Settings:
   - `DATABASE_URL` = `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   - `GEMINI_API_KEY` = `your_gemini_api_key`
4. Deploy to production:
```bash
vercel --prod
```

---

## 6. Seed Credentials for Live Dashboard Login

When deployed to Cloud Run / Render / Vercel, use the default seeded credentials:

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | `admin@careoutreach.health` |
| **Lead Care Manager** | `caremanager` | `password123` | `caremanager@careoutreach.health` |

You can also register new users through the `/login` registration interface.

---

## 7. Local vs. Cloud Environment Cheat-Sheet

| Environment | File / Location | `DATABASE_URL` setting |
| :--- | :--- | :--- |
| **Local (MySQL Workbench)** | `backend/.env` | `mysql+pymysql://root:mysql@localhost:3306/care_management` |
| **Cloud (Cloud Run / Render / Vercel)** | Cloud Dashboard Env Vars | `postgresql://postgres.[REF]:[PASS]@aws-0-[REGION].pooler.supabase.com:6543/postgres` |
