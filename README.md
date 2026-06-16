# DeskGuard - Backend Engine 
(to be integrated with Deskguard - Frontend)

This repository houses the core engine and relational state API for DeskGuard. It manages live desk statuses, processes check-in requests, and serves as the single source of truth for the interactive floor maps.

##  Key Features
* **High-Performance REST API:** Fast handling of incoming desk status updates and operational check-ins.
* **In-Memory State Engine:** Blazing-fast state retention ensuring zero lag when updating live configurations.
* **Cross-Origin Resource Sharing (CORS):** Fully configured to securely communicate with remote frontend environments (like v0 and mobile browser viewports).

## Tech Stack
* **Language:** Python 3.11+
* **Framework:** FastAPI
* **Server Gateway:** Uvicorn
* **Deployment:** Render (Cloud Web Service)

## Repository Structure
* `main.py` - Core application file hosting the FastAPI initialization, validation schemas, and endpoint controllers.
* `requirements.txt` - Python project dependencies.

## Core API Endpoints

### 1. Get All Desks Status
* **Endpoint:** `GET /api/desks`
* **Description:** Retrieves the comprehensive real-time availability layout for the entire workspace.

### 2. Process Desk Check-In
* **Endpoint:** `POST /api/desk/check-in`
* **Request Payload:**
```json
  {
    "desk_id": "D-04"
  }
