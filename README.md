# PBS Backend API

This project is a FastAPI-based backend for mobile and dashboard APIs.

## Structure

- `app/main.py`: Main entry point for FastAPI application
- `app/api/mobile/`: Mobile API routes
- `app/api/dashboard/`: Dashboard API routes
- `app/models/`: Data models
- `app/config/`: Configuration settings

## Getting Started

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn
   ```
2. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Endpoints
- `/mobile/ping`: Test mobile API
- `/dashboard/ping`: Test dashboard API

---

Replace placeholder code with your actual business logic and models as needed.
