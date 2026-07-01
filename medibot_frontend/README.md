# MediBot Frontend

Next.js frontend for the MediBot FastAPI backend.

## Run

Start the backend first:

```bash
cd ../medibot_modular
uvicorn api:app --reload --port 8000
```

Then start the frontend:

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

The frontend calls `/api/*`, and `next.config.mjs` rewrites those requests to `http://localhost:8000/*`.

## Demo Users

| User | Password | Role |
| --- | --- | --- |
| `dr.mehta` | `doctor123` | `doctor` |
| `nurse.priya` | `nurse123` | `nurse` |
| `billing.ravi` | `billing123` | `billing_executive` |
| `tech.anand` | `tech123` | `technician` |
| `admin.sys` | `admin123` | `admin` |

