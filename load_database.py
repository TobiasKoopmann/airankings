import os
from app.databases.create_sqlitedb import process_article_authors, create_new_db, process_authors, process_url, \
    process_countries

basedir = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(basedir, 'data')


def create_db(reset: bool) -> None:
    """
    Creates the database locally. The files 'ai_dataset.json', 'persons.json' and 'author_countries.json' need to be in the 'data' folder.
    :param reset: If true, drops old 'airankings' database first, which is recommended
    :return:
    """
    source_article = os.path.join(DATA_PATH, 'ai_dataset.json')
    source_person = os.path.join(DATA_PATH, 'persons.json')
    source_country = os.path.join(DATA_PATH, 'author_countries.json')
    target = 'airankings'
    create_new_db(target, reset=reset)
    author_ids = process_authors(db_name=target, file_path_pubs=source_article)
    process_article_authors(db_name=target, file_path=source_article, author_ids=author_ids)
    process_url(db_name=target, file_path=source_person, author_ids=author_ids)
    process_countries(db_name=target, file_path=source_country, author_ids=author_ids)
    print('   DB Created!')
    print()


if __name__ == '__main__':
    print('Create database')
    create_db(reset=True)
    print("Finished load the database. ")
