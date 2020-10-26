import sqlite3
import os
import time

from flask import g
from app.myfunctions import get_dblp_url
from app.databases.create_sqlitedb import get_mysql_db

curpath = os.path.dirname(os.path.realpath(__file__))
DATABASE = os.path.join(curpath, 'static', 'pycsrankings.sqlite3')


def mysql_get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def mysql_get_database_venues():
    with get_mysql_db() as conn:
        c = conn.cursor()
        sql = "Select distinct venue from article;"
        c.execute(sql)
        return c.fetchall()


def mysql_get_authors(venues: list, country: str = 'all', start_year: int = 2000, end_year: int = 2020, page: int = 1,
                      name: str = None, order_by: str = "pubs", desc: bool = True) -> \
        (int, list):
    """
    :param venues:List of venues
    :param country: List of countries
    :param start_year: From when
    :param end_year: to when
    :param page:
    :param name:
    :param order_by: name, pubs, total_pubs, h_index
    :param desc:
    :return:
    """
    start = time.time()
    offset = (page - 1) * 40
    authors = help_mysql_get_authors(venues=venues, country=country, start_year=start_year, end_year=end_year,
                                     name=name, order_by=order_by, desc=desc)
    authors = authors[offset:offset + 40]
    authors = [[x[0], x[2], ''.join(i for i in x[2].title() if not i.isdigit()).strip(), x[3], x[4], 0, x[5],
                mysql_get_main_urls(x[2])] for x in authors]
    current_len = len(authors)
    print("Ending query. Took ", str(time.time() - start))
    return current_len, authors


def help_mysql_get_authors(venues: list, country: str, start_year: int, end_year: int, name: str, order_by: str,
                           desc: bool) -> list:
    """
        :param venues:List of venues
        :param country: List of countries
        :param start_year: From when
        :param end_year: to when
        :param name:
        :param order_by: name, pubs, total_pubs, h_index
        :param desc:
        :return:
        """
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE airankings')
    all_venues = True if "all" in venues else False
    if not all_venues:
        p = venues.copy()
    else:
        p = []
    p.append(start_year)
    p.append(end_year)
    if country == "all" and all_venues:
        sql = 'select a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index, a.googlescholar from ' \
              '(select article_id from article where year >= %s and year <= %s) as ar ' \
              'natural join author_article aa ' \
              'natural join (select author_id, name, total_pubs, h_index, googlescholar from author) as a ' \
              'GROUP BY a.author_id ORDER BY '
    elif country == "all":
        sql = 'select a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index, a.googlescholar ' \
              'from (select article_id from article where venue in ({seq}) and year >= %s and year <= %s) as ar ' \
              'natural join author_article aa ' \
              'natural join (select author_id, name, total_pubs, h_index, googlescholar from author) as a ' \
              'GROUP BY a.author_id ORDER BY '.format(seq=','.join(['%s'] * len(venues)))
    elif all_venues:
        sql = 'SELECT a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index, a.googlescholar ' \
              'FROM (select article_id from article WHERE year >= %s AND year <= %s) as ar ' \
              'natural join author_article aa natural join ' \
              '(select author_id, name, total_pubs, h_index, googlescholar from author ' \
              'natural join author_country where country = %s) as a ' \
              'GROUP BY a.author_id ORDER BY '
        p.append(country)
    else:
        sql = 'SELECT a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index, a.googlescholar ' \
              'FROM (select article_id from article WHERE venue in ({seq}) AND year >= %s AND year <= %s) as ar ' \
              'natural join author_article aa natural join ' \
              '(select author_id, name, total_pubs, h_index, googlescholar from author ' \
              'natural join author_country ' \
              'where country = %s ) as a ' \
              'GROUP BY a.author_id ORDER BY ' \
            .format(seq=','.join(['%s'] * len(venues)))
        p.append(country)
    if order_by:
        sql += order_by
    else:
        sql += " pubs"
    if desc:
        sql += ' DESC'
    c.execute(sql, p)
    authors = c.fetchall()
    authors = [((i,) + x) for i, x in enumerate(authors, start=1)]
    c.execute(sql, p)
    conn.close()
    if name:
        authors = [x for x in authors if
                   any(n.strip() in x[2] for n in name.split('&')) or
                   (x[6] and any(n.strip() in x[6].lower() for n in name.split('&')))]
    return authors


def mysql_get_pubs(author_name: str):
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE airankings')
    p = (author_name,)
    sql = 'select author_id, h_index from author where name = %s;'
    c.execute(sql, p)
    res = c.fetchall()[0]
    aid = res[0]
    p = (aid,)
    sql = 'select distinct title, venue, year, ar.key, ar.in_citations from article ar where ar.article_id in ' \
          '(select article_id from author_article where author_id = %s) order by year desc;'
    c.execute(sql, p)
    pubs = c.fetchall()
    conn.close()
    pubs = [{'title': x[0], 'venue': x[1], 'year': x[2], 'key': x[3], 'cits': x[4]} for x in pubs]
    return pubs, res[0], res[1]


def mysql_get_urls(author_id: int):
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE airankings')
    p = (author_id,)
    sql = 'select url from author_url where author_id = %s;'
    c.execute(sql, p)
    res = c.fetchall()
    result_urls = [x[0] for x in res]
    conn.close()
    return result_urls


def mysql_get_affiliation(author_id: int):
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE airankings')
    p = (author_id,)
    sql = 'select affiliation from author_country where author_id = %s;'
    c.execute(sql, p)
    res = c.fetchall()
    result = [x[0] for x in res]
    conn.close()
    return result


def mysql_get_main_urls(author_name: str) -> dict:
    conn = get_mysql_db()
    c = conn.cursor()
    c.execute('USE airankings')
    sql = 'select url from author_url natural join author a where a.name=%s;'
    p = (author_name,)
    c.execute(sql, p)
    res = c.fetchall()
    result_urls = [x[0] for x in res]
    main_page_urls = {'dblp': get_dblp_url(author_name)}
    github = []
    for url in result_urls:
        if 'orcid.org/' in url:
            main_page_urls['orcid'] = url
        elif 'scholar.google.com/' in url:
            main_page_urls['gs'] = url
        elif 'twitter.com/' in url:
            main_page_urls['twitter'] = url
        elif 'github.com/' in url:
            github.append(url)
        elif 'linkedin.com/' in url:
            main_page_urls['linkedin'] = url
    if github:
        main_page_urls['github'] = github
    conn.close()
    return main_page_urls


if __name__ == '__main__':
    urls = mysql_get_urls('Zhi-Hua Zhou')
    print(urls)
