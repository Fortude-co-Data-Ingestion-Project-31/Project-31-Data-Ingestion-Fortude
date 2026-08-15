# Project 31: Data Ingestion Engine
# FIT4002-Fortude

This is a data pipeline designed to integrate data from multiple systems, standardise their data formats, then distribute them to appropriate storage systems to allow the collected data to be analysed and queried in a unified way.

This system is composed of:
- **Connectors** to extract data from various platforms including Infor, JIRA, and SharePoint
- **Mappers** to normalise the data into a canonical format and serialise it into the format required
- **Business Rules** to filter, transform, and route data records
- **Storage Systems** to output the processed data to appropriate destinations

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

## Frontend

- **Install dependencies:**

	```bash
	npm install
	```

- **Run development server:**

	```bash
	npm run dev
	```

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
	- `backend/`: Backend-focused pytest tests.
	- `frontend/`: Frontend test placeholders and UI tests.

- Top-level files:
	- `package.json`, `vite.config.js`, `tailwind.config.js`: Frontend build and dependency configs.
	- `requirements.txt`, `pytest.ini`: Python dependencies and test configuration for the backend.
	- `README.md`: This file — project overview and quickstart.

Use this section to quickly orient new contributors and link into specific files or folders when more detail is required.