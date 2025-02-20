# Goodmorningtoyou
### Author: Jayden Lee
### Table of contents
* [Introduction](#introduction)
* [Requirements](#requirements)
* [How to](#how-to)
* [Order of Operation](#order-of-operation)
* [Snippets](#web-snippets)

----

### Introduction
**Good morning to you!**

Most of us love to have a sip of that coffee in the morning while getting ready for the day ahead of us. Some of us get on treadmil to warm up our body, some of us read book or meditate to clear their mind, and some of us like to stay on top of world's status by watching news or reading articles. 

I programmed this simple, yet briefly informatiave, web application to help people quickly retrieve daily news and historical events. Application is fully capable of fetching today's most updated news articles, cleaning and loading the data into locally hosted database service, and displaying the information on a simply designed Web UI.

----

### Requirements
- Application hosts all external services on your local machine using Docker containers; local machines are expected to have Docker CLI or Docker Desktop installed
- Python executable to execute scripts with
- Python environment is version-managed & version-controlled using [Poetry](https://python-poetry.org/)
- Tables in target database are expected to be defined prior to collection of data; refer to `src/PostgreSQL/defineObjects.sql` for defining database objects

----

### How to
1. You'll need an active Docker daemon, check the status of your Docker daemon by running 
```bash
    docker ps -a
```

2. Install all dependencies using `poetry`, which uses `poetry.lock` in project root directory, by running
```bash
    poetry install # Installs all dependencies and creates `venv` folder in project root with installed packages
```

3. Create and start all Docker containers by running
```bash
    docker compose up -d
```

4. You now have all services needed for the app alive; create the database objects in PostgreSQL environment using `src/defineObjects.sql`

5. Input your config sets like API key in `config/__init__.py` and update your `docker-compose.yaml` accordingly

6. Once successfully launched, execute `app.py`; **REMEMBER TO ACTIVATE YOUR VENV**
```bash
    python main.py
```

----

### Order of Operation
1. `src/Getter/*Getter.py` objects collect today's news and events happened on today's date from open-source API websites and store the collected dataset into locally-hosted object-storage system([MiniO](https://min.io/))
    - News data is collected from [[NewsAPI](https://newsapi.org)]
    - Events that happened on this day is collected from [[OnThisDay](https://www.onthisday.com)]

2. `src/Parser/Parser.py` object gathers fetched data from MiniO buckets, cleans & processes them according to the needs, and ingests them into locally-hosted RDBMS([PostgreSQL](https://www.postgresql.org/))

3. Stored datasets get reflected on Web UI spun up using Python [Flask](https://flask.palletsprojects.com/en/stable/) designed with [HTML](https://en.wikipedia.org/wiki/HTML) and [CSS](https://en.wikipedia.org/wiki/CSS) Markup Languages

----

### Web Snippets
- News: <img src='static/img/news-snippet.png'>

- OnthisDay: <img src='static/img/onthisday-snippet.png'>