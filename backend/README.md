# Setting up the UI (backend + frontend)

## Backend (FastAPI):

```
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload
```

By default the backend runs on `http://localhost:8000`.

## Frontend (React):

```
cd frontend
npm install
npm run dev
```



Frontend dev server runs on `http://localhost:5173` and the example app calls the backend at `http://localhost:8000`.

# Running The Backend and Frontend

## Backend: 
uvicorn backend.main:app --reload

## Frontend:
npm run dev