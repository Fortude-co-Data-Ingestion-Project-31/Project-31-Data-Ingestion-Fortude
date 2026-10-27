# Project 31: Data Ingestion Engine
# FIT4002-Fortude

This is a data pipeline designed to integrate data from multiple systems, standardise their data formats, then distribute them to appropriate storage systems to allow the collected data to be analysed and queried in a unified way.

This system is composed of:
- **Connectors** to extract data from various platforms including Infor, JIRA, and SharePoint
- **Mappers** to normalise the data into a canonical format and serialise it into the format required
- **Business Rules** to filter, transform, and route data records
- **Storage Systems** to output the processed data to appropriate destinations

## MongoDB vector output

The ingestion output list includes separate **MongoDB** (document storage) and
**MongoDB Vector Database** targets. Selecting the vector target writes chunk
text and normalized embeddings to the `vector_chunks` collection without
writing the source document to the document collections.

Vector output requires a MongoDB Atlas cluster with Vector Search enabled.
The application creates a `vector_index` Atlas Search index on first write.
Embeddings are generated locally with
`sentence-transformers/all-MiniLM-L6-v2`; set
`MONGO_VECTOR_EMBEDDING_MODEL` to use another compatible local model. The
index dimension must match the configured model. Regular MongoDB document
outputs use `MONGO_URI` and `MONGO_DB_NAME`. Vector output has its own
connection and database settings: `MONGO_VECTOR_URI` and
`MONGO_VECTOR_DB_NAME`. The collection defaults to `vector_chunks`; optionally
set `MONGO_VECTOR_COLLECTION` to use a different collection name. Neither the
database nor collection setting is the Atlas project or cluster name.

To use MongoDB Atlas, create `backend/app/.env` (this file is ignored by Git)
and set:

```dotenv
MONGO_URI=mongodb+srv://<document-user>:<url-encoded-password>@<document-cluster-host>/?retryWrites=true&w=majority
MONGO_DB_NAME=<document-database>
MONGO_VECTOR_URI=mongodb+srv://<vector-user>:<url-encoded-password>@<vector-cluster-host>/?retryWrites=true&w=majority
MONGO_VECTOR_DB_NAME=<vector-database>
MONGO_VECTOR_COLLECTION=vector_chunks
```

Use each connection string from Atlas, replace the placeholders locally, and
restart the backend after changing the file. The vector URI may point to the
same cluster as the document URI, while `MONGO_VECTOR_DB_NAME` selects a
separate database. In Atlas, allow the backend machine's IP address in Network
Access and give each database user read/write access to its database. Do not
share or commit the URIs. Vector output requires both vector-specific settings
and fails clearly instead of silently writing to the regular MongoDB database
or localhost.

For a manual SharePoint ingestion, selecting **MongoDB Vector Database**
re-enumerates the current SharePoint files and upserts their chunks, so existing
files are indexed even when the delta feed has no new changes. The response
reports the target database, collection, and number of indexed chunks. In Atlas
Data Explorer, open the configured vector database and the `vector_chunks`
collection to see each chunk's `content` and `embedding` fields. Open **Vector
Data** in the application sidebar to browse chunk text and metadata without
displaying embedding arrays.

SharePoint vector ingestion retains the selected mapper and rule names, along
with rule metadata and tags, on each vector chunk. These selections are also
retained for automatic SharePoint delta sync. Documents rejected by the
Knowledge Base sensitivity rule are excluded from vector storage, and any
older vectors for them are removed.

## Contributors

| Name                     | Student Email               | Personal Email               |
| ------------------------ | --------------------------- | ---------------------------- |
| Junjie Huang (Joel)      | jhua0145@student.monash.edu | gulityeaten@gmail.com        |
| Naveen Sellathurai       | nsel0009@student.monash.edu | Navboy44@outlook.com         |
| Nag Rohith Chapalamadugu | rcha0087@student.monash.edu | sivasvg1rohith@gmail.com     |
| Rowan Albert Alex        | ralb0005@student.monash.edu | ralbertalex@gmail.com        |
| Sai Ashish Ramishetty    | sram0056@student.monash.edu | sairamishetty58@gmail.com    |
| Sona Hariharan           | shar0108@student.monash.edu | sonahariharan067@gmail.com   |


## Documentation links

- Full Development Guide: https://docs.google.com/document/d/1HHSTL8_dvFfBZY46qxhkSk_gw6rnYG-cDUmNmGnLFsg/edit?usp=sharing
- [Setup](documentation/setup.md)
- [GIT Guidelines](documentation/git-guidelines.md)

## backend

- **Create and activate a virtual environment (recommended):**

	```bash
	python -m venv .venv
	source .venv/bin/activate
	```

- **Install Python dependencies:**

	```bash
	pip install -r requirements.txt
	```

- **Run the backend tests:**

	```bash
	cd backend
	pytest -q -m "not integration"
	```

## Frontend

- **Install dependencies:**

	```bash
	cd frontend
	npm install
	```

- **Run development server:**

	```bash
	cd frontend
	npm run dev
	```

- **Run the frontend test suite and production build:**

	```bash
	cd frontend
	npm test -- --run
	npm run build
	```

## CI/CD pipeline

This repository includes GitHub Actions workflows to keep the project healthy during development and deployment:

- `.github/workflows/ci.yml` - Runs backend pytest checks and frontend build/test validation on pushes and pull requests.
- `.github/workflows/cd.yml` - Builds release artifacts and provides a deployment job that can be connected to the target hosting platform.

The CI workflow is intentionally configured to skip external integration tests by default, which reduces flaky failures caused by service dependencies such as Jira, MongoDB or SharePoint.

For production deployment, update the placeholder deployment step in `.github/workflows/cd.yml` to use your real deployment tool (for example Azure App Service, Docker registry publishing, or SSH-based deployment).

## Folder structure

A concise overview of the repository layout and the purpose of important folders and files:

- `backend/`: Python backend service.
	- `app/`: Main application code (entrypoints and application logic).
		- `auth.py`, `main.py`: Authentication and app startup logic.
		- `connectors/`: Implementations that extract data from external sources.
		- `mappers/`: Normalize and map raw inputs into canonical formats.
		- `rules/`: Business rule handlers used to filter/transform data.
		- `outputs/`: Code that writes processed data to storage destinations.
		- `tools/`: Utility scripts and demos (helpers for local runs).

- `src/`: Frontend React app source.
	- `components/`: Reusable UI components (Header, Card, Sidebar, etc.).
	- `pages/`: Route-level pages used by the app (Dashboard, Login, Settings, etc.).
	- `index.jsx`, `App.jsx`, `index.css`: Frontend entry points and styling.

- `local_data/`: Example/local input and output data used for demos and local testing.
	- `input/`: Raw sample input files used by connectors.
	- `output/`: Resulting JSON or processed files after running ingestion locally.

- `documentation/`: Project docs and guides (`setup.md`, `auth_flow.md`, `git-guidelines.md`).

- `tests/`: Unit and integration tests.
	- `backend/`: backend-focused pytest tests.
	- `frontend/`: Frontend test placeholders and UI tests.

- Top-level files:
	- `package.json`, `vite.config.js`, `tailwind.config.js`: Frontend build and dependency configs.
	- `requirements.txt`, `pytest.ini`: Python dependencies and test configuration for the backend.
	- `README.md`: This file — project overview and quickstart.

Use this section to quickly orient new contributors and link into specific files or folders when more detail is required.