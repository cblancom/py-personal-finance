# PyPersonalFinance - Learning Roadmap

This project will teach you modern web development with **FastAPI**, **React**, and **Docker**. Each step builds on the previous one.

---

## 📋 Prerequisites

Before starting, ensure you have:
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- Basic knowledge of Python and JavaScript

---

## 🎯 Learning Objectives

By the end of this project, you'll understand:

1. **API Design & Development** (FastAPI, REST, SQLAlchemy)
2. **Frontend Development** (React, TypeScript, Hooks, API integration)
3. **Database Design** (PostgreSQL, relationships, migrations)
4. **Containerization** (Docker, Docker Compose, multi-stage builds)
5. **Project Architecture** (MVC pattern, folder structure, separation of concerns)

---

## 🗂️ Project Structure (What to Build)

```
py-personal-finance/
├── backend/                    # Python/FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes and schemas
│   │   ├── db/                # Database models
│   │   ├── core/              # Configuration
│   │   └── utils/             # Utility functions
│   ├── migrations/            # Database migrations
│   ├── tests/                 # Unit tests
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React/TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   ├── types/             # TypeScript types
│   │   ├── hooks/             # Custom hooks
│   │   └── utils/             # Utility functions
│   └── package.json           # Node dependencies
│
├── docker/                    # Docker configurations
│   ├── Dockerfile.api         # Backend Docker image
│   ├── Dockerfile.web         # Frontend Docker image
│   ├── nginx.conf             # Reverse proxy config
│   └── docker-compose.yml     # Multi-container orchestration
│
└── README.md                  # Documentation
```

---

## 📚 Step-by-Step Learning Plan

### Phase 1: Backend (FastAPI + SQLAlchemy)
**Goal**: Build a REST API that stores income and expenses in PostgreSQL

#### Step 1.1: Set Up the Project
- [ ] Create the directory structure
- [ ] Initialize a virtual environment (`python -m venv venv`)
- [ ] Install dependencies (`pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-dotenv`)
- [ ] Create `requirements.txt`
- [ ] Create `.env` file with database credentials

#### Step 1.2: Database Models
- [ ] Create `models.py` with SQLAlchemy ORM
- [ ] Define three models: `Income`, `Expense`, `Category`
- [ ] Set up foreign key relationship between `Expense` and `Category`
- [ ] Create tables in PostgreSQL

#### Step 1.3: Database Session
- [ ] Create a database session factory
- [ ] Implement dependency injection for database sessions
- [ ] Learn about SQLAlchemy's `SessionLocal`

#### Step 1.4: Pydantic Schemas
- [ ] Create Pydantic models for request/response validation
- [ ] Define schemas for Income, Expense, Category (create, read, update)
- [ ] Learn about Pydantic's data validation

#### Step 1.5: API Routes
- [ ] Create FastAPI routes for CRUD operations
- [ ] Implement endpoints:
  - `GET /api/income` - List all incomes
  - `POST /api/income` - Create income
  - `GET /api/income/{id}` - Get income by ID
  - `PUT /api/income/{id}` - Update income
  - `DELETE /api/income/{id}` - Delete income
  - (Repeat for Expense and Category)
- [ ] Learn about FastAPI's dependency injection

#### Step 1.6: Testing
- [ ] Write unit tests using pytest
- [ ] Test database operations
- [ ] Test API endpoints
- [ ] Learn about FastAPI's test client

#### Step 1.7: Dockerize Backend
- [ ] Create `Dockerfile.api`
- [ ] Build and run the Docker container
- [ ] Learn about multi-stage Docker builds

---

### Phase 2: Frontend (React + TypeScript)
**Goal**: Build a React frontend that consumes your API

#### Step 2.1: Set Up React Project
- [ ] Create a new React TypeScript project using Vite
- [ ] Configure TypeScript strict mode
- [ ] Set up project structure

#### Step 2.2: TypeScript Types
- [ ] Create type definitions matching your backend schemas
- [ ] Define interfaces for Income, Expense, Category
- [ ] Learn about TypeScript generics and type safety

#### Step 2.3: API Client
- [ ] Create an HTTP client (Axios or Fetch API)
- [ ] Implement service functions for API calls
- [ ] Handle loading states and errors

#### Step 2.4: React Components
- [ ] Create a `Dashboard` component
- [ ] Implement form components for adding income/expense
- [ ] Create list components to display data
- [ ] Learn about React hooks (`useState`, `useEffect`)

#### Step 2.5: State Management
- [ ] Implement global state using Context API or Zustand
- [ ] Handle loading, error, and success states
- [ ] Learn about React's data flow

#### Step 2.6: Styling
- [ ] Implement CSS styling
- [ ] Create reusable style components
- [ ] Learn about responsive design

#### Step 2.7: Dockerize Frontend
- [ ] Create `Dockerfile.web`
- [ ] Build and run the Docker container
- [ ] Learn about static file serving

---

### Phase 3: Integration & Deployment
**Goal**: Put everything together with Docker Compose

#### Step 3.1: Docker Compose
- [ ] Create `docker-compose.yml`
- [ ] Define services for backend, frontend, and database
- [ ] Configure networking between containers
- [ ] Learn about service dependencies

#### Step 3.2: Nginx Reverse Proxy
- [ ] Configure nginx to serve the frontend
- [ ] Set up reverse proxy to backend API
- [ ] Configure CORS headers

#### Step 3.3: Environment Variables
- [ ] Configure environment variables for each service
- [ ] Secure sensitive data
- [ ] Learn about Docker secrets

#### Step 3.4: Database Migrations
- [ ] Set up Alembic for database migrations
- [ ] Create initial migration
- [ ] Learn about version control for database schema

---

## 🎓 Concepts to Learn (In Order)

### Backend Concepts
1. **SQLAlchemy ORM**: Mapping Python classes to database tables
2. **Dependency Injection**: Passing database sessions to functions
3. **Pydantic**: Data validation and serialization
4. **FastAPI**: Modern Python web framework
5. **REST API**: Design principles and best practices
6. **PostgreSQL**: Relational database management
7. **Docker**: Containerization and isolation

### Frontend Concepts
1. **React**: Component-based UI library
2. **TypeScript**: Type-safe JavaScript
3. **Hooks**: State and side effects management
4. **API Integration**: Fetching and handling data
5. **Forms**: Form validation and submission
6. **Styling**: CSS and responsive design
7. **Docker**: Building frontend containers

### DevOps Concepts
1. **Docker Compose**: Multi-container orchestration
2. **Networking**: Container communication
3. **Environment Variables**: Configuration management
4. **Migrations**: Database schema versioning
5. **CI/CD**: Continuous integration and deployment

---

## 📝 Daily Study Plan (Example)

### Week 1: Backend Basics
- **Day 1**: Set up project, install dependencies
- **Day 2**: Create database models
- **Day 3**: Implement database session
- **Day 4**: Create Pydantic schemas
- **Day 5**: Build Income CRUD routes
- **Day 6**: Build Expense and Category CRUD routes
- **Day 7**: Rest and review

### Week 2: Testing & Docker
- **Day 8**: Write unit tests
- **Day 9**: Integration tests
- **Day 10**: Dockerize backend
- **Day 11**: Test Docker container
- **Day 12**: Database migrations
- **Day 13**: Optimize Docker image
- **Day 14**: Rest and review

### Week 3: Frontend Basics
- **Day 15**: Set up React project
- **Day 16**: Create TypeScript types
- **Day 17**: Build API client
- **Day 18**: Create Dashboard component
- **Day 19**: Implement Income form
- **Day 20**: Implement Expense form
- **Day 21**: Rest and review

### Week 4: Frontend Completion & Integration
- **Day 22**: Implement data display components
- **Day 23**: Add error handling
- **Day 24**: Add loading states
- **Day 25**: Dockerize frontend
- **Day 26**: Set up Docker Compose
- **Day 27**: Configure nginx
- **Day 28**: Final testing and deployment

---

## 🔗 Helpful Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### React
- [React Documentation](https://react.dev/)
- [TypeScript React](https://react.dev/learn/typescript)

### SQLAlchemy
- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/20/core/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

### Docker
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## 🎯 Success Criteria

You'll know you're ready when:
- [ ] You can run the application with `docker-compose up`
- [ ] The frontend displays a working dashboard
- [ ] You can add income and expenses through the UI
- [ ] Data is persisted in PostgreSQL
- [ ] You understand how each layer connects
- [ ] You can explain each concept to someone else

---

## 💡 Tips for Learning

1. **Don't rush**: Take your time to understand each concept
2. **Break it down**: Focus on one small feature at a time
3. **Ask questions**: Use Stack Overflow, GitHub issues
4. **Build along**: Type everything yourself, don't copy-paste
5. **Test often**: Write tests as you build
6. **Review code**: After each step, review and refactor
7. **Document**: Keep notes on what you learn

---

## 🚀 Next Steps After Completion

Once you finish this project, you can:
- Add user authentication (JWT tokens)
- Implement real-time updates (WebSockets)
- Add data visualization (charts)
- Deploy to cloud (AWS, GCP, Azure)
- Add mobile app (React Native)
- Implement caching (Redis)

---

**Remember**: The goal is not to finish quickly, but to deeply understand each concept. Take your time, and enjoy the learning process! 🚀
