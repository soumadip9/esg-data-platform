# Deploy to Render

## One-click deploy

1. Push this repo to GitHub (already done: `soumadip9/esg-data-platform`)
2. Open: **https://dashboard.render.com/select-repo?type=blueprint**
3. Connect GitHub and select **`esg-data-platform`**
4. Render reads `render.yaml` and creates:
   - PostgreSQL database (`breathe-esg-db`)
   - API service (`breathe-esg-api`)
   - Frontend service (`breathe-esg-web`)
5. Click **Apply** and wait ~10–15 minutes for first deploy

## Live URLs (after deploy)

| Service | URL |
|---------|-----|
| Frontend (submit this) | https://breathe-esg-web.onrender.com |
| API | https://breathe-esg-api.onrender.com |
| Health check | https://breathe-esg-api.onrender.com/health/ |

## Login credentials

```
Username: analyst
Password: demo1234
Tenant:   Acme Corporation (has sample data)

Username: analyst2
Password: demo1234
Tenant:   Globex Industries (empty — demonstrates tenant isolation)
```

## After deploy — verify

1. Open the frontend URL
2. Sign in with `analyst` / `demo1234`
3. Go to **Ingestion** — confirm sample data loaded (seed runs on deploy)
4. Go to **Review Queue** — you should see activity records
5. Test **Approve** on a few flagged rows

## If frontend can't reach API

In Render dashboard → **breathe-esg-web** → **Environment**:

- Confirm `VITE_API_URL` = `https://breathe-esg-api.onrender.com/api`
- Click **Manual Deploy → Clear build cache & deploy**

In **breathe-esg-api** → **Environment**:

- Confirm `CORS_ALLOWED_ORIGINS` = `https://breathe-esg-web.onrender.com`

## Free tier notes

- Services **spin down after 15 min idle** — first load may take 30–60 seconds
- PostgreSQL free tier expires after 90 days (enough for assignment review)

## Submission email template

```
GitHub: https://github.com/soumadip9/esg-data-platform
Live app: https://breathe-esg-web.onrender.com
Login: analyst / demo1234
```

Share the repo with:
- saurav@breatheesg.com
- rahul@breatheesg.com
- shivang@breatheesg.com
