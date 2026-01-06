# RestroBot - AI

A production-ready multi-user restaurant ordering system using LangGraph for conversation management, OpenAI GPT for natural language processing, FastAPI for REST API, React for web interface, and PostgreSQL for data persistence.

## System Architecture

```
Browser (React) → FastAPI (REST) → LangGraph (State Machine) → OpenAI GPT
                      ↓
                 PostgreSQL (Menu + Orders)
```

**Stack:**
- **Frontend**: React 18.3 + Vite 7.3
- **Backend**: FastAPI 0.115 + Uvicorn 0.34
- **AI Engine**: LangGraph 0.3.21 + LangChain + OpenAI GPT-4o-mini
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0
- **Deployment**: Docker + Docker Compose

**Features:**
- Multi-user concurrent sessions with in-memory session store
- Natural language conversation with context-aware responses
- Database-backed menu management (23 items, 4 categories)
- Order persistence with price tracking
- Real-time order management
- RESTful API with auto-generated documentation

## Near-future Features

- **Authentication & roles**: customer sessions + admin/operator roles
- **Admin dashboard**: manage menu, prices, modifiers, specials, out-of-stock
- **Real-time updates**: order status updates (WebSocket/SSE) for customers + kitchen
- **Payments**: Stripe integration (pay-at-table / online checkout)
- **Order lifecycle**: statuses (received → preparing → ready → served) + ETA updates
- **Observability**: structured logging, request tracing, and metrics
- **Production session store**: Redis-backed sessions instead of in-memory storage

## Quick Start

### Prerequisites
- Docker Desktop
- OpenAI API key ([get here](https://platform.openai.com/api-keys))

### Web Application (Multi-User)

```bash
# Setup
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-your-key

# Start all services
chmod +x start-web.sh
./start-web.sh

# Access
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### CLI Mode (Single User)

```bash
chmod +x docker-setup.sh run.sh
./docker-setup.sh
./run.sh
```

## Project Structure

```
pos-ai/
├── src/                      # Core conversation engine
│   ├── config.py            # LLM config, system prompts
│   ├── state.py             # OrderState TypedDict
│   ├── database.py          # PostgreSQL operations
│   ├── tools.py             # LangChain tools (menu, orders)
│   ├── nodes.py             # Graph node implementations
│   └── graph.py             # LangGraph conversation flow
├── api/                      # FastAPI backend
│   └── main.py              # REST endpoints, session management
├── frontend/                 # React web UI
│   └── src/App.jsx          # Chat interface
├── db/                       # Database schema
│   ├── init.sql             # Schema (8 tables)
│   ├── seed.sql             # Menu data (23 items)
│   └── 02_add_orders.sql    # Order tables
├── main.py                   # CLI entry point
├── docker-compose-web.yml    # Multi-service orchestration
└── requirements.txt          # Python dependencies
```

**Database Schema (8 tables):**
- `categories` - Menu categories
- `menu_items` - Items with prices
- `modifiers` - Customization options
- `item_modifiers` - Item-modifier links
- `specials` - Daily specials
- `out_of_stock` - Availability tracking
- `orders` - Order headers (customer, table, total)
- `order_items` - Order line items

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + DB status |
| GET | `/menu` | Get all menu items |
| POST | `/session/create` | Create new session |
| POST | `/chat` | Send message, get response |
| POST | `/order/place` | Place order to database |

**Session Management:**
- In-memory session store with UUID-based session IDs
- Each session maintains independent conversation state
- Supports concurrent users without state conflicts

## How It Works

### Conversation Flow (LangGraph)

```
START → Chatbot Node → Tool Execution → Response → END
         ↓              (get_menu, add_to_order, place_order)
    OpenAI GPT-4o-mini
```

**Key Components:**

1. **State Management** (`src/state.py`)
   - `OrderState` TypedDict with messages and order items
   - Persistent across conversation turns

2. **Tools** (`src/tools.py`)
   - `get_menu()` - Query PostgreSQL for available items
   - `add_to_order()` - Add items to session cart
   - `place_order()` - Persist order to database

3. **Graph Nodes** (`src/nodes.py`)
   - `chatbot_node()` - LLM interaction
   - `tool_node()` - Tool invocation
   - `human_node()` - CLI input (CLI mode only)

4. **Session Management** (`api/main.py`)
   - Creates isolated LangGraph instances per session
   - Manages conversation state in memory
   - Routes requests to appropriate graph instance

## Configuration

**Environment Variables (.env):**
```bash
OPENAI_API_KEY=sk-your-key
DATABASE_URL=postgresql://restrobot:restrobot_pass@db:5432/restrobot
```

**LLM Settings (`src/config.py`):**
```python
LLM_MODEL = "gpt-4o-mini"        # Model: gpt-4o, gpt-4o-mini, gpt-4-turbo
LLM_TEMPERATURE = 0.7             # Creativity (0-1)
RECURSION_LIMIT = 100             # Max conversation depth
```

## Database Operations

**View orders:**
```bash
python view_orders.py
# or
./db-shell.sh
```

**Add menu item:**
```sql
INSERT INTO menu_items (category_id, name, description, price, available)
VALUES (2, 'Pasta Carbonara', 'Classic Italian pasta', 14.99, true);
```

**Update price:**
```sql
UPDATE menu_items SET price = 16.99 WHERE name = 'Margherita Pizza';
```

**Recent orders:**
```sql
SELECT id, customer_name, total_amount, status, created_at FROM orders 
ORDER BY created_at DESC LIMIT 10;
```

## Development

**Local setup (without Docker):**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start database only
docker-compose -f docker-compose-web.yml up -d db

# Update .env
DATABASE_URL=postgresql://restrobot:restrobot_pass@localhost:5432/restrobot

# Start API
cd api && uvicorn main:app --reload

# Start frontend
cd frontend && npm install && npm run dev
```

**Test API:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/menu
```

## Docker Commands

**Start all services:**
```bash
docker-compose -f docker-compose-web.yml up -d
```

**View logs:**
```bash
docker-compose -f docker-compose-web.yml logs -f api
docker-compose -f docker-compose-web.yml logs -f db
```

**Stop services:**
```bash
docker-compose -f docker-compose-web.yml down
```

**Reset database:**
```bash
docker-compose -f docker-compose-web.yml down -v
docker-compose -f docker-compose-web.yml up -d
```

## Production Deployment

**Railway (Recommended):**
```bash
npm install -g @railway/cli
railway login
railway init
railway add  # Add PostgreSQL
railway variables set OPENAI_API_KEY=sk-your-key
railway up
```

**Environment variables for production:**
- `OPENAI_API_KEY` - Required
- `DATABASE_URL` - Auto-configured by Railway
- `PORT` - Auto-configured

**CORS Configuration:**
Update `api/main.py` for production domain:
```python
allow_origins=["https://yourdomain.com"]
```

## License

MIT License - Free for educational and commercial use.

---

**Tech Stack:** LangGraph 0.3.21 • LangChain • OpenAI GPT-4o-mini • FastAPI 0.115 • React 18.3 • PostgreSQL 16 • Docker



## Troubleshooting

**Services not running:**
```bash
docker-compose -f docker-compose-web.yml ps
docker-compose -f docker-compose-web.yml restart api
```

**Database connection failed:**
```bash
docker-compose -f docker-compose-web.yml logs db
docker-compose -f docker-compose-web.yml restart db
```

**API errors:**
```bash
docker-compose -f docker-compose-web.yml logs api | grep -i error
docker-compose -f docker-compose-web.yml restart api
```

**Port conflicts:**
Edit `docker-compose-web.yml` and change host ports:
```yaml
ports:
  - "5433:5432"  # Database
  - "8001:8000"  # API
```




