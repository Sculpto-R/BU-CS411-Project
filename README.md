# iNNiT?
## ➤ About
**iNNiT** is a Django-based web-application that designed to help young adults in London discover community events and entertainment tailored to their preferences.
This app was developed during the Boston University London Fall '25 term for CAS CS 411.

The system combines:
- Web-scraped event data from various venues
- User preference profiles stored in a database
- A future-ready mapping interface for visual exploration


---

## ➤ Goals & Objectives:

- Help users discover **upcoming events** around the London area.
- Personalize recommendations based on **user preferences** (e.g., genres, activities).
- Present events on an **interactive map interface** (integrating scraped data).


---

## ➤ 🛠️ Technologies Used

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python (Django Framework) | Web application framework |
| Database | SQLite (Development) | User, profile, event, and preference storage |
| Frontend | HTML, embedded CSS | Lightweight UI, Mapping Interface (Google Maps) |
| Scraping | BeautifulSoup4, Requests | Event scraping pipeline |
| Testing | Django TestCase, Python test files | Unit and integration tests |
| Containerization | Docker, docker-compose | Environment isolation and deployment |
| API Data | Google Maps | Map rendering base-layer |


---

## ➤ ✅ Requirements Checklist

| Requirement | Fulfillment |
|-------------|-------------|
| Decoupled frontend/backend | Django Templates & REST |
| (At least) one external API call | Google Maps API |
| Use of framework | Django |
| A database-integration containing (at least) user accounts with salted password hashes | SQLite & built-in salted passwords |
| Unit & integration tests | various tests across files via python test files, etc. |
| Docstrings & Logging | found throughout various files |
| Exception-handling | exception-handling found in select files |
| Containerization | Dockerfile |


---

## ➤ User's Manual

The current way to run this program is to clone this repo to a local folder by downloading the zip file.
Open the contained file in your editor of choice.
From here on, 
 navigate to the "innit_project" folder in-terminal, then type in the following in a terminal:
`python manage.py runserver`
...
