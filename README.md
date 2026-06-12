# PyPersonalFinance

A personal finance tracking application built with FastAPI, React, and Docker.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- PostgreSQL (included in Docker Compose)

### Run the Application

```bash
# Start all services (backend, frontend, database)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📚 Learning Path

This project is designed for learning. Follow the step-by-step guide in [LEARNING_PLAN.md](LEARNING_PLAN.md) to build this application gradually.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Browser                          │
│                      (http://localhost:3001)                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │    Nginx (Frontend)   │
          │  http://localhost:80  │
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │   FastAPI Backend     │
          │ http://localhost:8888 │
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │   PostgreSQL Database │
          │    localhost:55432    │
          └───────────────────────┘
```

## 📁 Project Structure

See [LEARNING_PLAN.md](LEARNING_PLAN.md) for a detailed breakdown of each component and what to build.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React, TypeScript, Vite
- **Database**: PostgreSQL
- **Infrastructure**: Docker, Docker Compose, Nginx

## 📖 Documentation

- [LEARNING_PLAN.md](LEARNING_PLAN.md) - Step-by-step learning guide
- [FastAPI Docs](https://fastapi.tiangolo.com/) - Backend framework
- [React Docs](https://react.dev/) - Frontend framework

## 🤝 Contributing

Contributions are welcome! Please open issues or pull requests.

## 📄 License

MIT License
