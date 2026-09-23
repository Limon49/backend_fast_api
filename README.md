# AIQuest API

A small FastAPI project that grew up: **users can buy products, and every
purchase is stored in the database so you can look it up properly.**

Built with [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/)
(SQLAlchemy + Pydantic), MySQL, [Alembic](https://alembic.sqlalchemy.org/) migrations
and [uv](https://docs.astral.sh/uv/) for dependencies.

---

## 1. What is all of this? (30-second version)

- **FastAPI** turns Python functions into HTTP endpoints (`@router.post("/orders")`).
- **Uvicorn** is the server that runs the app and listens on a port.
- **SQLModel** lets one Python class be *both* the database table and the JSON shape.
- **Alembic** keeps the database schema in version control — "migrations" are the
  steps that move a database from one version of the code to the next.
- **uv** installs dependencies (like npm for JavaScript).

```
You (browser/app) --HTTP request--> Uvicorn --> FastAPI router --> CRUD --> MySQL
                                         <-- JSON response <--
```

## 2. Project structure

```
FastApi/
├── app/                        # the application package
│   ├── main.py                 # build the app: CORS, errors, routers, lifespan
│   ├── core/                   # cross-cutting pieces, no business logic
│   │   ├── config.py           #   every setting (env vars / .env)
│   │   ├── database.py         #   engine + "one session per request"
│   │   ├── exceptions.py       #   NotFoundError / ConflictError + error envelope
│   │   ├── logging.py          #   logging setup
│   │   └── utils.py            #   utcnow()
│   ├── models/                 # database tables (the truth)
│   │   ├── user.py  product.py  order.py
│   ├── schemas/                # request/response contracts (what the API accepts/returns)
│   ├── crud/                   # queries + business rules (no HTTP here)
│   │   ├── user.py  product.py  order.py  report.py
│   ├── api/
│   │   ├── deps.py             #   SessionDep, PaginationDep
│   │   └── v1/                 #   the versioned HTTP layer
│   │       ├── router.py       #     includes every router below
│   │       ├── health.py  users.py  products.py  orders.py  reports.py  examples.py
│   └── scripts/                # runnable helpers
│       ├── init_db.py          #   run migrations + create the SQL view
│       ├── seed.py             #   insert demo products
│       └── db_views.py         #   the `order_details` view
├── migrations/                 # Alembic: the schema history
│   ├── env.py
│   └── versions/0001_initial_user.py, 0002_products_and_orders.py
├── tests/                      # pytest suite (uses a throwaway SQLite database)
├── docker/entrypoint.sh        # wait for DB -> migrate -> start uvicorn
├── alembic.ini  docker-compose.yml  Dockerfile  .env.example  pyproject.toml
```

**Why this shape?** Each layer can be understood on its own:

| Layer | Knows about | Does *not* know about |
|---|---|---|
| `models/` | tables, columns, relationships | HTTP, JSON |
| `schemas/` | JSON shape, validation rules | SQL, sessions |
| `crud/` | queries, business rules | HTTP status codes |
| `api/` | URLs, status codes, dependencies | how SQL is written |

That is what makes the purchase logic testable without spinning up a web server,
and what stops a database column name from leaking into your public API.

## 3. Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and MySQL.

```bash
uv sync                                        # 1. install dependencies (.venv)
cp .env.example .env                           # 2. your local settings (optional)
uv run python -m app.scripts.init_db           # 3. create/upgrade the tables
uv run python -m app.scripts.seed              # 4. add demo products
uv run uvicorn app.main:app --reload           # 5. start the server
```

Then open:

| URL | What you see |
|---|---|
| http://localhost:8000/ | welcome + links |
| http://localhost:8000/api/v1/health | app *and* database status |
| **http://localhost:8000/docs** | **Swagger UI — try every endpoint here** |
| http://localhost:8000/redoc | alternative documentation |

New tables in your database after step 3: `product`, `orders`, `order_item` —
plus the `order_details` view (section 6).

## 4. The data model

Four tables, one clear chain — who bought what:

```
user ──< orders ──< order_item >── product
 │         │             │            │
 who      one purchase   one line:    what can
         by one user     how many     be bought
                        at what price
```

| Table | Meaning | Interesting columns |
|---|---|---|
| `user` | who buys | `name`, `email` (unique), `age` |
| `product` | what can be bought | `price` `DECIMAL(10,2)`, `stock`, `is_active` |
| `orders` | one purchase | `user_id`, `status` (`paid`/`cancelled`), `total_amount`, `created_at` |
| `order_item` | one line of a purchase | `order_id`, `product_id`, `quantity`, `unit_price`, `line_total` |

Three decisions worth understanding, because they are what real shops do:

1. **The table is `orders`, not `order`.** `ORDER` is a reserved word in MySQL, so
   every raw query would need backticks.
2. **`unit_price` and `line_total` are copies** taken at purchase time. Change a
   product's price tomorrow and yesterday's receipts still add up correctly.
3. **Products are deactivated, never deleted** (`is_active = false`). Order lines
   point at products, so a hard delete would break purchase history.

The database also enforces the rules it can (`price > 0`, `stock >= 0`,
`quantity > 0`) with `CHECK` constraints and foreign keys — see
`migrations/versions/0002_products_and_orders.py`.

## 5. Buying something

One request = one purchase. You send **product ids and quantities**; the server
does the rest.

```bash
# A product to buy (price is a string to keep it exact)
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name": "FastAPI 101", "price": "19.99", "stock": 10}'

# Buy two of it (user 1 must exist)
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "items": [{"product_id": 1, "quantity": 2}]}'
```

The response tells the whole story in one shot:

```json
{
  "id": 1,
  "user_id": 1,
  "status": "paid",
  "total_amount": 39.98,
  "created_at": "2026-09-22T09:44:34",
  "item_count": 1,
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "product_name": "FastAPI 101",
      "quantity": 2,
      "unit_price": 19.99,
      "line_total": 39.98,
      "product": { "id": 1, "name": "FastAPI 101", "stock": 8, "...": "..." }
    }
  ],
  "user": { "id": 1, "name": "Limon", "email": "limon@edutune.com", "age": 25 }
}
```

**What happens inside `POST /api/v1/orders`** (all in `app/crud/order.py`):

1. the user must exist → otherwise **404**
2. every product must exist → otherwise **404**
3. products must be active → otherwise **409**
4. stock must be enough → otherwise **409** (`have 10, want 999`), and nothing changes
5. the price is read **from the database** — a client cannot send its own price
6. duplicate lines for the same product are **merged**, so `2 + 3` is checked as `5`
7. stock is decreased, order + lines are inserted, **one `commit()`**

Because it is a single transaction, it is all-or-nothing: a failure halfway
through rolls everything back. There is a test for exactly that
(`test_a_failed_write_rolls_back_the_whole_purchase`).

Other things you can do:

```bash
curl "http://localhost:8000/api/v1/orders?user_id=1&status=paid"   # filter
curl http://localhost:8000/api/v1/users/1/orders                   # history
curl -X POST http://localhost:8000/api/v1/orders/1/cancel          # stock goes back
curl "http://localhost:8000/api/v1/products?search=fast&in_stock=true"
curl http://localhost:8000/api/v1/reports/sales                    # revenue per product
```

Errors always come back in the same shape, so the frontend needs one error handler:

```json
{"error": {"code": "conflict", "message": "Not enough stock for 'FastAPI 101' (have 10, want 999)"}}
```

## 6. Seeing it in the database (this is the fun part)

### The `order_details` view

Joining four tables by hand gets old fast, so the project creates a **SQL view**
that behaves like a ready-made report:

```sql
SELECT * FROM order_details;
```

```
+----------+---------------+--------------------+----------+------------+------------+-------------+--------+
| order_id | customer_name | product_name       | quantity | unit_price | line_total | order_total | status |
+----------+---------------+--------------------+----------+------------+------------+-------------+--------+
|        1 | Limon         | FastAPI 101        |        2 |      19.99 |      39.98 |       69.48 | paid   |
|        1 | Limon         | SQLModel Deep Dive |        1 |      29.50 |      29.50 |       69.48 | paid   |
+----------+---------------+--------------------+----------+------------+------------+-------------+--------+
```

Open it in TablePlus, Sequel Ace, DBeaver or the `mysql` client — the view is a
normal object in the sidebar. `GET /api/v1/reports/recent-orders` returns exactly
the same columns as JSON, so the API and your SQL client never disagree.

The view is created by `uv run python -m app.scripts.init_db` and you can rebuild
it on its own any time with `uv run python -m app.scripts.db_views`.

### Queries worth keeping

```sql
-- Everything a user ever bought
SELECT * FROM order_details WHERE customer_email = 'limon@edutune.com';

-- What is on the shelf right now
SELECT id, name, price, stock, is_active FROM product ORDER BY name;

-- Orders with their totals
SELECT o.id, u.name, o.status, o.total_amount, o.created_at
FROM orders o JOIN user u ON u.id = o.user_id
ORDER BY o.created_at DESC;

-- Best sellers (what /reports/sales computes)
SELECT p.name, SUM(oi.quantity) AS units, SUM(oi.line_total) AS revenue
FROM order_item oi
JOIN product p ON p.id = oi.product_id
JOIN orders  o ON o.id = oi.order_id
WHERE o.status = 'paid'
GROUP BY p.id, p.name
ORDER BY revenue DESC;

-- How much each user has spent
SELECT u.name, COUNT(DISTINCT o.id) AS orders, SUM(o.total_amount) AS spent
FROM orders o JOIN user u ON u.id = o.user_id
WHERE o.status = 'paid'
GROUP BY u.id, u.name;
```

Handy one-liners:

```bash
mysql -u aiquest -p aiquest_db -e "SELECT * FROM order_details;"
mysql -u aiquest -p aiquest_db -e "SELECT id, name, stock FROM product;"
```

## 7. API reference

Everything lives under `/api/v1` (paths are versioned so a future breaking change
can ship as `/api/v2` without breaking existing clients).

| Method | Path | What it does |
|---|---|---|
| GET | `/` | welcome + links (not versioned) |
| GET | `/api/v1/health` | app + database status (503 if the DB is down) |
| POST | `/api/v1/users` | create a user (409 if the email exists) |
| GET | `/api/v1/users` | list users (`limit`, `offset`) |
| GET | `/api/v1/users/{id}` | one user |
| GET | `/api/v1/users/{id}/orders` | that user's purchase history |
| POST | `/api/v1/products` | create a product |
| GET | `/api/v1/products` | list (`search`, `in_stock`, `include_inactive`, `limit`, `offset`) |
| GET | `/api/v1/products/{id}` | one product |
| PATCH | `/api/v1/products/{id}` | change name/price/stock/is_active |
| DELETE | `/api/v1/products/{id}` | soft delete (`is_active = false`) |
| POST | `/api/v1/orders` | **buy products** (201, 404, 409, 422) |
| GET | `/api/v1/orders` | list (`user_id`, `status`, `limit`, `offset`) |
| GET | `/api/v1/orders/{id}` | one order with its lines (404 if unknown) |
| POST | `/api/v1/orders/{id}/cancel` | cancel + put the stock back (409 if already cancelled) |
| GET | `/api/v1/reports/sales` | units sold + revenue per product |
| GET | `/api/v1/reports/recent-orders` | the flat `order_details` rows as JSON |
| GET/POST | `/api/v1/items/{id}`, `/api/v1/courses` | the original teaching examples |

List endpoints return an envelope, never a bare array:

```json
{"total": 1, "limit": 50, "offset": 0, "items": [ { "...": "..." } ]}
```

Status codes you will meet: **201** created, **404** not found, **409** conflict
(out of stock, duplicate email, already cancelled), **422** the body failed
validation, **503** the database is unreachable.

## 8. Tests

```bash
uv run pytest              # 42 tests, about half a second
uv run pytest -v           # see each test name
uv run pytest tests/test_orders.py::test_cancel_puts_the_stock_back
```

The suite covers the purchase flow end to end: totals, stock changes, price
snapshots, merged duplicate lines, cancel-and-restock, the reports, every error
case (404 / 409 / 422) and the rollback when a write fails.

**They never touch your MySQL database.** `tests/conftest.py` creates a fresh
SQLite file per test and swaps the session dependency with
`app.dependency_overrides`. That is the payoff of the layered structure: the API
you test is the real API, with only its database source replaced.

## 9. Migrations (how the tables stay in sync)

Migrations are numbered Python files that describe how to change the schema.
They are the reason the code and the database can never drift apart.

```bash
uv run alembic current                      # which version is the DB on?
uv run alembic history                      # every migration, oldest first
uv run alembic upgrade head                 # apply all pending migrations
uv run alembic downgrade -1                 # undo the last one
uv run alembic upgrade head --sql           # print the SQL instead of running it
uv run alembic revision --autogenerate -m "add phone to user"   # new migration
```

The two migrations here:

| Revision | What it does |
|---|---|
| `0001_initial_user` | the original `user` table (baseline) |
| `0002_products_and_orders` | `product`, `orders`, `order_item` + constraints and indexes |

### Already have a database with a `user` table?

Then the first migration is already true for you — it must be *recorded* as
applied, not run again:

```bash
uv run alembic stamp 0001_initial_user   # "assume 0001 is already done"
uv run alembic upgrade head              # only runs what is missing (0002)
```

That is exactly what was done to your `aiquest_db`: your two existing users were
kept, and only the three new tables were created. On a brand new database you
just run `uv run alembic upgrade head` and everything is built from scratch.

Rule of thumb: **never edit a migration that has already been applied.** Add a
new one instead.

## 10. Configuration

Nothing is hardcoded: every value has a sensible default in
`app/core/config.py` and can be overridden by an environment variable or a
`.env` file (copy `.env.example`).

| Variable | Default | Meaning |
|---|---|---|
| `ENVIRONMENT` | `development` | free-form label, shown in `/health` |
| `DEBUG` | `true` | DEBUG logs when true, INFO when false |
| `SQL_ECHO` | `false` | print every SQL statement |
| `AUTO_CREATE_TABLES` | `false` | create tables from models at startup (dev shortcut) |
| `DB_USER` | `aiquest` | MySQL user |
| `DB_PASSWORD` | `aiquest123` | MySQL password |
| `DB_HOST` | `127.0.0.1` | MySQL host (`db` inside docker-compose) |
| `DB_PORT` | `3306` | MySQL port |
| `DB_NAME` | `aiquest_db` | database name |
| `DATABASE_URL` | *(unset)* | full URL override, wins over all `DB_*` values |
| `CORS_ORIGINS` | `*` | comma separated allowed browser origins |

`.env` is in `.gitignore` — secrets belong there, never in code.

## 11. Docker and deployment

### Production style locally

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000   # no --reload: dev only
```

### Docker (app + MySQL, one command)

```bash
docker compose up --build        # API on :8000, MySQL on :3307
docker compose exec api python -m app.scripts.seed
docker compose down              # stop; add -v to also delete the database volume
```

The container's entrypoint waits for MySQL, runs `alembic upgrade head`, then
starts uvicorn (`docker/entrypoint.sh`). Notes:

- MySQL is published on **3307** on purpose: your Mac already has MySQL on 3306.
- The API runs as a non-root user and has a real `HEALTHCHECK` hitting
  `/api/v1/health`.
- Migrations run at startup; set `RUN_MIGRATIONS=false` for a second replica so
  two containers do not migrate at the same time.

Building the image by hand:

```bash
docker build -t aiquest-api .
docker run -p 8000:8000 \
  -e DB_HOST=host.docker.internal -e DB_NAME=aiquest_db \
  -e DB_USER=aiquest -e DB_PASSWORD=aiquest123 aiquest-api
```

### A real host (Render / Railway / Fly)

1. push the code to GitHub
2. create the service from the repo (it detects the `Dockerfile`)
3. set the environment variables (`DB_*`, `ENVIRONMENT=production`, `DEBUG=false`,
   `CORS_ORIGINS=https://your-frontend`) — never bake secrets into the image
4. point it at a managed MySQL and let the entrypoint run the migrations

## 12. Conventions used here (so new code feels the same)

- **Models vs schemas**: `app/models` is the database, `app/schemas` is the API.
  Never return a table model directly — map it (`OrderRead.from_model`).
- **Routers are thin**: parse → call a `crud` function → return a schema.
- **CRUD raises domain errors** (`NotFoundError`, `ConflictError`), never
  `HTTPException`. The HTTP translation lives in one place
  (`app/core/exceptions.py`).
- **One consistent error shape** everywhere: `{"error": {"code", "message"}}`.
- **Money is `DECIMAL(10,2)` + `Decimal`**, and serialised as a JSON number.
- **Timestamps are UTC** (`app.core.utils.utcnow`).
- **Every list endpoint paginates** (`?limit=&offset=`) and returns
  `{total, limit, offset, items}`.
- **Add a migration** for every model change, and a test for every new rule.

## 13. Common beginner mistakes (learned the hard way)

- Forgetting `uv run` → "module not found".
- Editing the code but the server still behaves the old way → you forgot `--reload`.
- Changing a model and not creating a migration → the API 500s with
  "unknown column"; run `uv run alembic revision --autogenerate -m "..."`.
- Testing a POST in the browser address bar → browsers can only do GET; use
  `/docs` or `curl`.
- Putting prices or stock in the request body and trusting them → this project
  always reads them from the database.
- Hard-deleting rows that other rows point at → deactivate instead.
- Committing secrets (`DB_PASSWORD`) in `.env` → keep it out of git.

## 14. Where to go next

Ideas that fit this structure without a rewrite:

- **Auth**: add `password_hash` to `user`, then a `POST /api/v1/auth/token`
  router, and replace `user_id` in the order body with "the current user".
- **A cart**: a `cart_item` table (add to cart → checkout) — a good exercise in
  multi-step flows.
- **Payments**: a `payment` table plus a `pending → paid` order status.
- **Concurrency**: `SELECT ... FOR UPDATE` on products so two simultaneous
  buyers cannot oversell the last item.
- **Observability**: request IDs and structured JSON logs.

Official docs: [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/),
[SQLModel](https://sqlmodel.tiangolo.com/), [Alembic](https://alembic.sqlalchemy.org/),
[uv](https://docs.astral.sh/uv/).
