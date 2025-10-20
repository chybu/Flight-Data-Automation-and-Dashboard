!(example1.jpeg)
!(example2.jpeg)

# Flight Data Automation and Dashboard

A complete end-to-end **Python system** for collecting, processing, storing, and visualizing real-time flight data from the Skyscanner API.  
The project integrates **web automation**, **data parsing**, **database insertion**, and a **Dash dashboard** to streamline large-scale flight information analysis.

---

## Overview

This project automates flight data retrieval using dynamic cookies and user-agent rotation, cleans and structures the results into SQL tables, and provides an **interactive web dashboard** for visual analysis.

The pipeline includes:
1. **Automated Data Collection** — Uses `undetected_chromedriver` and authenticated sessions to query Skyscanner APIs for flight availability, durations, carriers, and pricing.
2. **Data Structuring** — Cleans and formats raw JSON responses into normalized flight records (one-way and round-trip).
3. **Database Integration** — Inserts structured flight data into a MySQL database running inside Docker.
4. **Visualization** — A Dash dashboard allows interactive flight exploration, filtering, and plotting of flight attributes such as price, duration, stopovers, and carriers.

---

## Core Components

| File | Description |
|------|--------------|
| **`Cookie.py`** | Automates Chrome session startup, retrieves Skyscanner cookies, and solves captchas if necessary. |
| **`UserAgent.py`** | Rotates user agents to avoid request throttling. |
| **`FlightScraper.py`** | Queries the Skyscanner API, parses flight legs, segments, carriers, durations, and prices into structured Python dataclasses. |
| **`LocationScraper.py`** | Retrieves and parses airport metadata, coordinates, and geolocation info. |
| **`models.py`** | Defines Python dataclasses (`Place`, `DirectFlightTicket`, `FlightResult`) used throughout scraping and database insertion. |
| **`db_models.py`** | Defines SQLAlchemy ORM models for tables: `location`, `airport`, `direct_flight`, and `round_flight`. |
| **`DBInserter.py`** | Manages database connections (MySQL via Docker), inserts new flight and location records, and handles timezone mapping. |
| **`dashboard_demo.py`** | Dash web application for searching routes, choosing date ranges, and visualizing flight data interactively. |
| **`insertToDBScript_demo.py`** | Demo script showing the full flow: start Docker → scrape flights → insert results → stop Docker. |

---

## Tech Stack

- **Python 3.11**
- **Selenium / undetected-chromedriver** — handle dynamic login and cookie retrieval  
- **requests** — API communication  
- **SQLAlchemy** — ORM for structured data management  
- **MySQL (Docker)** — persistent storage for flight data  
- **Dash + Plotly** — dashboard and visualization interface  
- **TimezoneFinder** — resolve timezone metadata for airports  

---

## Database Schema

The system creates and populates:
- `location`: Airport or city with timezone info  
- `airport`: Airport-level data linked to location  
- `direct_flight`: One-way flight details  
- `round_flight`: Round-trip flight details  

Each entry stores duration breakdowns, stopovers, carrier info, agent data, and prices, allowing detailed analytics and trend monitoring.

---

## Dashboard

An interactive **Dash** web app (`dashboard_demo.py`) that allows users to:
- Search by origin and destination
- Choose **direct** or **round-trip**
- Select date ranges (± days)
- Filter flights and visualize relationships such as:
  - Price vs duration
  - Number of stops vs carrier
  - Agent rating vs total transfer time  
- View flight results as a sortable table
