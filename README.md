# AIQuest API

A small [FastAPI](https://fastapi.tiangolo.com/) project for learning how APIs are built and deployed.

---

## 1. What is all of this? (30-second version)

- **FastAPI** is a Python library for building web APIs — programs that listen for HTTP
  requests (like a browser or mobile app makes) and send back JSON data.
- **Uvicorn** is the *server* that actually runs your FastAPI app and listens on a port.
- **uv** is the tool that installs your Python dependencies (like npm for JavaScript).
- **Deployment** means putting your API on a real server on the internet so other
  people can reach it — not just on your laptop.

```
You (browser/app)  --HTTP request-->  Uvicorn  -->  FastAPI app  -->  JSON response
```

## 2. Project structure

```
FastApi/
├── main.py            # The whole app lives here (routes + data models)
├── pyproject.toml     # Project name + dependencies (managed by uv)
├── uv.lock            # Exact versions of everything installed (keeps servers consistent)
├── Dockerfile         # Recipe to build a portable image for deployment
├── .dockerignore      # Files Docker should skip
└── .venv/             # Your local virtual environment (auto-created, never edit)
```

## 3. Running the app on your computer

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) installed once:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, inside this folder:

```bash
uv sync                          # 1. install dependencies (creates .venv)
uv run uvicorn main:app --reload # 2. start the server with auto-reload
```

> `--reload` restarts the server automatically when you edit `main.py`.
> Perfect while learning — **remove it in production.**

Now open these in your browser:

| URL | What you see |
|---|---|
| http://localhost:8000/ | `{"message": "Welcome to AIQuest!"}` |
| http://localhost:8000/items/42?q=hello | Path + query parameters in action |
| http://localhost:8000/courses | The courses endpoint |
| **http://localhost:8000/docs** | **Interactive API docs (Swagger UI) — try it!** |
| http://localhost:8000/redoc | Alternative documentation page |

## 4. Trying the POST endpoint

The `POST /courses` endpoint needs a JSON body. Test it from another terminal:

```bash
curl -X POST http://localhost:8000/courses \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FastAPI 101",
    "instructor": "Limon",
    "website": "https://aiquest.example.com",
    "duration": 2.5
  }'
```

Or just use the **"Try it out"** button on http://localhost:8000/docs — much easier.

Notice: send a bad URL or a missing field and you get a clear `422` error telling you
exactly what's wrong. That validation comes free from the `Course` model in `main.py`
(you didn't have to write any validation logic — nice, right?).

## 5. How the code works (the 4 ideas to remember)

Open `main.py` — everything maps to these four concepts:

1. **`app = FastAPI()`** — your application object. One per project.
2. **Routes** — `@app.get("/")` means "when someone visits this URL with GET, run this
   function and send back what it returns."
   - `@app.get("/items/{item_id}")` — `{item_id}` is a **path parameter**.
   - `q: str | None = None` — `q` is an optional **query parameter** (`?q=hello`).
3. **Models** — `class Course(BaseModel)` declares the JSON shape your API accepts.
   FastAPI validates and parses incoming bodies into a `Course` object for you.
4. **Status codes** — `@app.post("/courses", status_code=201)` means "successfully
   created" instead of the default 200.

## 6. Deploying: from your laptop to the internet

### Step A — Run it "production style" locally

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

- `--reload` is gone (you don't want the server restarting on a live site).
- `--host 0.0.0.0` makes it reachable from outside your machine — this is exactly
  what every hosting platform runs.

### Step B — Put it in Docker (so it runs *anywhere* identically)

[Docker](https://www.docker.com/get-started/) packages your app + Python + all
dependencies into one image:

```bash
docker build -t aiquest-api .
docker run -p 8000:8000 aiquest-api
```

Your API is now live at http://localhost:8000 — same image runs on any server.

### Step C — Ship it to a free cloud host

The easiest beginner options (both have free tiers and work with the included
`Dockerfile`):

- **Render** (render.com): New → Web Service → connect your GitHub repo → it detects
  the Dockerfile automatically → Deploy. You get a public URL like
  `https://aiquest-api.onrender.com`.
- **Railway** (railway.app): similar flow — connect repo, deploy, done.

The flow is always the same: **push code to GitHub → connect repo to host → host runs
the Dockerfile → get a public URL.**

```bash
git add .
git commit -m "My FastAPI app"
git push   # (after creating a repo on GitHub and: git remote add origin <your-repo-url>)
```

## 7. Common beginner mistakes (learned the hard way so you don't have to)

- Forgetting to activate the venv / use `uv run` → "module not found" errors.
- Editing code but the server still shows old behavior → you forgot `--reload`.
- Deploying with `uvicorn main:app --reload` → slow and unsafe; reload is dev-only.
- Putting secrets (passwords, API keys) in code → use environment variables and a `.env`
  file (add `.env` to `.gitignore`).
- Testing POST in the browser address bar → browsers can only do GET; use `/docs` or `curl`.

## 8. Where to go next

- Official tutorial (excellent): https://fastapi.tiangolo.com/tutorial/
- Add a database: https://sqlmodel.tiangolo.com/ (by the FastAPI author)
- Return real course data from a database instead of placeholder text
