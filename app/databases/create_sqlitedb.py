import os
import json
import mysql.connector
import re
from mysql.connector import errorcode
from tqdm import tqdm
from scholarmetrics import hindex
from sqlite3 import Error


def get_mysql_db(host='127.0.0.1'):
    try:
        return mysql.connector.connect(host=host, user='root')
    except mysql.connector.Error as err:
        try:
            return mysql.connector.connect(host=host, user='root')
        except:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            else:
                print(err)


def create_new_db(db_name: str, reset: bool = True, verbose: int = 1, is_mysql: bool = True) -> None:
    """
    :param db_name: Where the SQLite file will be saved
    :param reset:
    :param is_mysql:
    :param verbose:
    :return:
    """
    if verbose:
        print("Creating the Database. ")
    if is_mysql:
        conn = get_mysql_db()
        c = conn.cursor()
        if reset:
            try:
                c.execute("DROP DATABASE {}".format(db_name))
            except:
                print('Cannot delete database. ')
        try:
            c.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
        except mysql.connector.Error as err:
            print("Failed creating database: {}".format(err))
            exit(1)
    else:
        if reset and os.path.exists(db_name):
            os.remove(db_name)
        # Create new DB if no DB exist
        if not os.path.exists(db_name):
            try:
                conn = get_mysql_db()
            except Error as e:
                print(e)
        conn = get_mysql_db()

    c = conn.cursor()
    c.execute('USE {}'.format(db_name))
    sql = 'create table if not exists article ' \
          '(article_id int(7) primary key AUTO_INCREMENT, ' \
          '`key` varchar(64), ' \
          '`title` text, ' \
          '`year` int(7), ' \
          '`venue` varchar(128), ' \
          '`in_citations` int(7)) ENGINE=InnoDB'
    c.execute(sql)
    sql = 'create index if not exists article_index on article (venue, article_id);'
    c.execute(sql)

    # Table author
    sql = 'create table if not exists author ' \
          '(`author_id` integer primary key AUTO_INCREMENT, ' \
          '`name` varchar(64), ' \
          '`total_pubs` integer, ' \
          '`h_index` integer, ' \
          '`googlescholar` varchar(512)) ENGINE=InnoDB'
    c.execute(sql)
    sql = 'create index if not exists author_index on author (author_id, name);'
    c.execute(sql)

    # Table author_article
    sql = 'create table if not exists author_article ' \
          '(author_id integer, ' \
          'article_id integer, ' \
          'primary key (author_id, article_id)) ENGINE=InnoDB'
    c.execute(sql)
    sql = 'create index if not exists author_article_index on author_article (article_id);'
    c.execute(sql)

    # Table country
    sql = 'create table if not exists author_country ' \
          '(author_id integer, ' \
          'country varchar(32), ' \
          'affiliation varchar(128), ' \
          'primary key (author_id, country)) ENGINE=InnoDB'
    c.execute(sql)
    sql = 'create index if not exists country_index on author_country (country, author_id);'
    c.execute(sql)

    # Table author_url
    sql = 'create table if not exists author_url (' \
          'author_id integer, ' \
          'url varchar(512), ' \
          'primary key (author_id, url)) ENGINE=InnoDB'
    c.execute(sql)
    sql = 'create index if not exists url_index on author_url (author_id);'
    c.execute(sql)

    conn.commit()
    conn.close()


def parse_author_name(author_name) -> str:
    return ''.join([i for i in author_name if not i.isdigit()]).strip()


def process_authors(db_name: str, file_path_pubs: str, verbose: int = 1) -> dict:
    if verbose:
        print("Loading the authors into the database. ")
    authors = {}
    with open(file_path_pubs, 'r', encoding='utf-8') as fh:
        if verbose:
            print("Loading set of authors. ")
        for line in tqdm(fh):
            info = json.loads(line)
            if "inCitations" in info:
                citations = [info['inCitations']]
            else:
                citations = []
            for author in info['author']:
                if author in authors:
                    tmp = authors[author]
                    tmp = (tmp[0] + 1, tmp[1] + citations)
                    authors[author] = tmp
                else:
                    authors[author] = (1, citations)

    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE {}'.format(db_name))
    author_ids = {}
    if verbose:
        print("Parsing authors into DB. ")
    for author, values in tqdm(authors.items()):
        sql = 'insert into author(name, total_pubs, h_index) values (%s, %s, %s);'
        p = (author.lower(), values[0], int(hindex(values[1])))
        c.execute(sql, p)
        author_ids[author] = c.lastrowid
    conn.commit()
    conn.close()
    return author_ids


def process_article_authors(db_name: str, file_path: str, author_ids: dict, verbose: int = 1) -> None:
    """
    :param db_name: Where the DB file is located
    :param file_path: Where the articles are
    :param author_ids:
    :param verbose:
    :return:
    """
    if verbose:
        print("Loading the articles and authors into the database. ")
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE {}'.format(db_name))
    c.execute("set names utf8;")

    def get_element(element, parse_int: bool = False):
        if isinstance(element, list):
            if len(element) == 1:
                if parse_int:
                    return int(element[0])
                return ''.join([i for i in element[0] if len(i.encode('utf-8')) < 4])
            elif len(element) == 0:
                return None
        if parse_int:
            return int(element)
        return ''.join([i for i in element if len(i.encode('utf-8')) < 4])

    with open(file_path, 'r', encoding='utf-8') as fh:
        sql_article = 'insert ignore into article(`key`, title, year, venue, in_citations) VALUES (%s,%s,%s,%s,%s);'
        sql_author_article = 'insert ignore into author_article(`author_id`, `article_id`) values (%s,%s);'
        for line in tqdm(fh):
            pub = json.loads(line)
            pub_key = get_element(pub['key'])
            pub_title = get_element(pub['title'])
            pub_year = get_element(pub['year'], parse_int=True)
            pub_venue = pub['venue']
            if 'inCitations' in pub:
                pub_in_citations = pub['inCitations']
            else:
                pub_in_citations = 0
            p = (pub_key, pub_title, pub_year, pub_venue, pub_in_citations)
            c.execute(sql_article, p)
            pub_id = c.lastrowid
            # author & author_article
            for author in pub['author']:
                p = (author_ids[author], pub_id)
                c.execute(sql_author_article, p)
    conn.commit()
    conn.close()


def process_countries(db_name: str, file_path: str, author_ids: dict, verbose: int = 1) -> None:
    if verbose:
        print("Loading the countries into the database. ")
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE {}'.format(db_name))
    c.execute("set names utf8;")
    with open(file_path, 'r', encoding='utf-8') as fh:
        if verbose:
            print("Loading the countries. ")
        for line in tqdm(fh):
            info = json.loads(line)
            if isinstance(info['author'], list):
                if info["country"] == 'United States':
                    info["country"] = 'USA'
                elif info["country"] == 'United Kingdom':
                    info["country"] = 'UK'
                for auth in info['author']:
                    if auth.strip() in author_ids:
                        if 'affiliation' in info:
                            sql = 'insert ignore into author_country(author_id, country, affiliation) values (%s,%s,%s);'
                            p = (author_ids[auth.strip()], info["country"], info['affiliation'])
                        else:
                            sql = 'insert ignore into author_country(author_id, country) values (%s,%s);'
                            p = (author_ids[auth.strip()], info["country"])
                        c.execute(sql, p)
            elif info["author"].strip() in author_ids:
                if 'affiliation' in info:
                    sql = 'insert ignore into author_country(author_id, country, affiliation) values (%s,%s,%s);'
                    p = (author_ids[info["author"].strip()], info["country"], info['affiliation'])
                else:
                    sql = 'insert ignore into author_country(author_id, country) values (%s,%s);'
                    p = (author_ids[info["author"].strip()], info["country"])
                c.execute(sql, p)
    conn.commit()
    conn.close()


def process_url(db_name: str, file_path: str, author_ids: dict, verbose: int = 1) -> None:
    if verbose:
        print("Loading the URLs into the database. ")
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE {}'.format(db_name))
    c.execute("set names utf8;")

    sql = 'insert ignore into author_url(author_id, url) values (%s,%s);'
    with open(file_path, 'r', encoding='utf-8') as fh:
        for line in tqdm(fh):
            info = json.loads(line)
            authors = info.get('author')
            title = info.get('title')
            urls = info.get('url')
            if title == 'Home Page':
                if authors is not None and urls is not None:
                    if isinstance(authors, str):
                        authors = [authors]
                    if isinstance(urls, str):
                        urls = [urls]
                    for author in authors:
                        if author in author_ids:
                            for url in urls:
                                p = (author_ids[author], url)
                                c.execute(sql, p)
    conn.commit()
    conn.close()
    insert_google_scholar_id(db_name)


def insert_google_scholar_id(db_name: str):
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE {}'.format(db_name))
    c.execute("set names utf8;")
    sql = 'select author_id,url from author_url where url like "%scholar.google%" '
    c.execute(sql)
    authors = c.fetchall()
    for author in authors:
        sql = 'Update author set googlescholar=%s where author_id=%s'
        scholarId = re.findall('(?<=user=).+', str(author[1]))
        p = [scholarId[0], int(author[0])]
        c.execute(sql, p)
    conn.commit()
    conn.close()


def get_country_list(db_name: str):
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE {}'.format(db_name))
    c.execute("set names utf8;")

    c.execute('select distinct country from author_country')
    countries = c.fetchall()
    countries = [x[0] for x in countries]
    countries.sort()
    conn.close()
    return countries
