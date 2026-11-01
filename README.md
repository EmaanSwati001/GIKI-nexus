# GIKI Nexus

GIKI Nexus is an intelligent knowledge and services hub.

## Project Structure

```text
giki-nexus/
│
├── docs/                      # Documentation
│   ├── requirements/          # Requirements and specifications
│   ├── design/                # System architecture and design docs
│   ├── testing/               # Test plans and test reports
│   └── project-management/    # Milestones, sprints, and task tracking
│
├── frontend/                  # Frontend user interface
│
├── backend/                   # Backend application
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/        # API route handlers
│   │   ├── services/          # Core business logic and external integrations
│   │   ├── graph/             # Graph algorithms / knowledge graph components
│   │   ├── models/            # Data models and entities
│   │   ├── schemas/           # Pydantic schemas / request-response contracts
│   │   └── database/          # DB connection, migrations, and repositories
│   └── tests/                 # Backend automated tests
│
├── data/                      # Dataset management
│   ├── raw/                   # Unprocessed original data
│   └── processed/             # Cleaned and processed data
│
├── scripts/                   # Utility scripts, data loaders, automation
│
├── README.md                  # Project overview and documentation
└── .gitignore                 # Git ignore rules
```
