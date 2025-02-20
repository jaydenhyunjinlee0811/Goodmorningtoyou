import os
from flask import Flask, render_template
import datetime
import webbrowser

from config import CONFIG
from src.utils import (
    create_pgclient, 
    get_logger,
    sort_by_year
)
from src import (
    NewsAPIGetter, 
    OnthisdayAPIGetter, 
    Parser
)

WORKDIR = os.getcwd()
LOGGER_DT_FMT = datetime.datetime.strftime(
    datetime.datetime.now(), '%Y%m%s-%H%M'
)
LOGGER_DIR = os.path.join(WORKDIR, 'log')

if not os.path.exists(LOGGER_DIR):
    _ = os.mkdir(LOGGER_DIR)
LOGGER_FP = os.path.join(LOGGER_DIR, f'DEV_{LOGGER_DT_FMT}.log')
TOPICS = {
    'NEWS': NewsAPIGetter,
    'ONTHISDAY': OnthisdayAPIGetter
}

app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)
logger = get_logger()

DT = datetime.date.today()
YEAR = DT.year
HEADER_DT = f'{DT.strftime('%b %d')}th'

@app.route('/')
@app.route('/home')
def home():
    return render_template(
        'home.html',
        date=HEADER_DT,
        year=YEAR,
        author='Jayden Lee'
    )

@app.route('/news/<author>')
def news(author: str):
    pgclient = create_pgclient(
        host=CONFIG['DB_HOST'],
        port=CONFIG['DB_PORT'],
        db_name=CONFIG['DB_NAME'],
        user=CONFIG['DB_USER'],
        pwd=CONFIG['DB_PWD'],
    )
    news_query = f"""
    SELECT
        title, 
        publisher,
        description,
        url
    FROM {CONFIG['DB_SCHEMA']}.news
    WHERE publisheddate = '{DT}';
    """
    # news_query = f"""
    # SELECT
    #     title, 
    #     publisher,
    #     description,
    #     url
    # FROM {CONFIG['DB_SCHEMA']}.news
    # WHERE publisheddate = '2025-02-09';
    # """
    articles = list()

    with pgclient.cursor() as cursor:
        try:
            _ = cursor.execute(news_query)
            res = cursor.fetchall()

            for i, r in enumerate(res):
                title, publisher, description, url = r
                articles.append({
                    'label': i+1,
                    'title': title.title(),
                    'publisher': publisher,
                    'description': description,
                    'url': url
                })
            
        except Exception as e:
            logger.error('ERROR TYPE: [%s]', type(e))
        finally:
            pgclient.close()

    return render_template(
        'news.html', 
        articles=articles,
        author=author,
        dt=DT.strftime('%m/%d/%Y')
    )

@app.route('/onthisday/<author>')
def onthisday(author: str):
    pgclient = create_pgclient(
        host=CONFIG['DB_HOST'],
        port=CONFIG['DB_PORT'],
        db_name=CONFIG['DB_NAME'],
        user=CONFIG['DB_USER'],
        pwd=CONFIG['DB_PWD'],
    )
    onthisday_query = f"""
    SELECT
        year,
        event
    FROM {CONFIG['DB_SCHEMA']}.onthisday
    WHERE publisheddate = '{DT}';
    """
    # onthisday_query = f"""
    # SELECT
    #     year,
    #     event
    # FROM {CONFIG['DB_SCHEMA']}.onthisday
    # """
    onthisday = list()

    with pgclient.cursor() as cursor:
        try:
            _ = cursor.execute(onthisday_query)
            res = cursor.fetchall()

            for r in res:
                year, event = r
                onthisday.append({
                    'year': year,
                    'event': event
                }) 

            onthisday = sort_by_year(onthisday)
            for i, item in enumerate(onthisday):
                item['label'] = i+1
            
        except Exception as e:
            logger.error('ERROR TYPE: [%s]', type(e))
            logger.error('ERROR MSG:')
            logger.error(e, exc_info=True)
        finally:
            pgclient.close()

    return render_template(
        'onthisday.html', 
        events=onthisday,
        date=HEADER_DT,
        author=author
    )

if __name__ == '__main__':
    for topic, Getter in TOPICS.items():
        getter = Getter(
            source_endpoint=CONFIG[topic]['API_SOURCE'],
            source_key=CONFIG[topic].get('API_KEY', ''),
            bucket_name=CONFIG['STG_BUCKET_NAME'],
            bucket_key=CONFIG[topic]['STG_BUCKET_KEY'],
            access_key_id=CONFIG['ACCESS_KEY_ID'],
            access_key_pwd=CONFIG['ACCESS_KEY_PWD'],
            logger_fp=LOGGER_FP
        )
        getter.get()

    parser = Parser(
        access_key_id=CONFIG['ACCESS_KEY_ID'],
        access_key_pwd=CONFIG['ACCESS_KEY_PWD'],
        bucket_name=CONFIG['STG_BUCKET_NAME'],
        bucket_keys=[
            CONFIG['NEWS']['STG_BUCKET_KEY'],
            CONFIG['ONTHISDAY']['STG_BUCKET_KEY']
        ],
        db_host=CONFIG['DB_HOST'],
        db_name=CONFIG['DB_NAME'],
        db_port=CONFIG['DB_PORT'],
        db_pwd=CONFIG['DB_PWD'],
        db_user=CONFIG['DB_USER'],
        tbl_schema=CONFIG['DB_SCHEMA']
    )
    parser.parse()

    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:5000/')

    app.run(debug=True, port=5000)