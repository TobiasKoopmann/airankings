import json
import os
import mysql.connector
from mysql.connector import errorcode

# todo bitte sowas NIE! commiten. Nutze sowas wie den Basepath
# STATIC_VENUE_PATH = "C:/Users/toepf/code-2019-airankings/app/static/ai_venues.json"
basedir = os.path.abspath(os.path.dirname(__file__))
STATIC_VENUE_PATH = basedir + "/../app/static/ai_venues.json"


class TestMYSQL:
    @staticmethod
    def get_mysql_db():
        try:
            return mysql.connector.connect(host='127.0.0.1', user='root')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise

    def test_mysql_connection(self):
        # simple existence check
        db = self.get_mysql_db()
        assert db is not None

    def test_mysql_start(self):
        conn = self.get_mysql_db()
        # The MySQLCursor class instantiates objects that can execute operations such as SQL statements.
        # Cursor objects interact with the MySQL server using a MySQLConnection object.
        c = conn.cursor()
        c.execute('USE airankings')
        sql = 'SELECT a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index ' \
              'FROM (select article_id from article WHERE venue in (%s,%s,%s,%s,%s,%s) AND year >= %s AND year <= %s) as ar ' \
              'natural join author_article aa natural join ' \
              '(select author_id, name, total_pubs, h_index from author natural join author_country where country = %s) as a ' \
              'GROUP BY a.author_id ORDER BY pubs DESC;'
        p = ('core', 'AAAI', 'IJCAI', 'Artif. Intell.', 'ECAI', 'J. Artif. Intell. Res.', 2000, 2020, 'Germany')
        c.execute(sql, p)
        # Returns all rows of a query result set
        # Returns a list of tuples.
        authors = c.fetchall()
        conn.close()
        assert len(authors) >= 0

    def test_mysql_search(self):
        conn = self.get_mysql_db()
        c = conn.cursor()
        c.execute('USE airankings')
        sql = 'SELECT a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index FROM (select article_id from article WHERE venue in (%s,%s,%s,%s) AND year >= %s AND year <= %s) as ar natural join author_article aa natural join (select author_id, name, total_pubs, h_index from author natural join author_country where country = %s) as a GROUP BY a.author_id ORDER BY pubs DESC'
        p = ['core', 'AAAI', 'IJCAI', 'ECAI', 1970, 2020, 'Germany']
        c.execute(sql, p)
        authors = c.fetchall()
        # indexing the authors
        authors = [((i,) + x) for i, x in enumerate(authors, start=1)]

        name = 'andreas hotho'
        authors = [x for x in authors if any(n.strip() in x[2] for n in name.split('&'))]
        conn.close()
        assert len(authors) == 1

    def test_mysql_search_multiple(self):
        conn = self.get_mysql_db()
        c = conn.cursor()
        c.execute('USE airankings')
        sql = 'SELECT a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index FROM (select article_id from article WHERE venue in (%s,%s,%s,%s) AND year >= %s AND year <= %s) as ar natural join author_article aa natural join (select author_id, name, total_pubs, h_index from author natural join author_country where country = %s) as a GROUP BY a.author_id ORDER BY pubs DESC'
        p = ['core', 'AAAI', 'IJCAI', 'ECAI', 1970, 2020, 'Germany']
        c.execute(sql, p)
        authors = c.fetchall()
        authors = [((i,) + x) for i, x in enumerate(authors, start=1)]
        name = 'andreas hotho & gerd stumme'
        # checks if there is a match between the input and the 3. argument in the tupel. Before the inputstring is stripped and splitted(Collab)
        authors = [x for x in authors if any(n.strip() in x[2] for n in name.split('&'))]
        conn.close()
        assert len(authors) == 2

    def test_mysql_hindex(self):
        # checks if the best-ranked author has a score over 0
        conn = self.get_mysql_db()
        c = conn.cursor()
        c.execute('USE airankings')
        sql = 'SELECT a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index FROM (select article_id from article WHERE venue in (%s,%s,%s,%s) AND year >= %s AND year <= %s) as ar natural join author_article aa natural join (select author_id, name, total_pubs, h_index from author natural join author_country where country = %s) as a GROUP BY a.author_id ORDER BY pubs DESC'
        p = ['core', 'AAAI', 'IJCAI', 'ECAI', 1970, 2020, 'Germany']
        c.execute(sql, p)
        authors = c.fetchall()
        conn.close()
        assert authors[0][-1] != 0

    def test_mysql_all_countries(self):
        # checks if the result array has more than 0 arguments
        conn = self.get_mysql_db()
        c = conn.cursor()
        c.execute('USE airankings')
        sql = 'select a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index from (select article_id from article where venue in (%s,%s,%s,%s) and year >= %s and year <= %s) as ar natural join author_article aa natural join author a GROUP BY a.author_id ORDER BY pubs DESC'
        p = ['core', 'AAAI', 'IJCAI', 'ECAI', 1970, 2020]
        c.execute(sql, p)
        authors = c.fetchall()
        conn.close()
        assert len(authors) > 0

    def test_pubs_available_for_all(self):
        with open(STATIC_VENUE_PATH, 'r', encoding='utf-8') as f:
            conferences = json.load(f)
        conferences = {k: list(v.keys()) for k, v in conferences.items()}

        def test_pubs_available_for_domain(domain: str):
            def test_one(conference: str):
                conn = self.get_mysql_db()
                c = conn.cursor()
                c.execute('USE airankings')
                sql = 'select a.author_id, a.name, count(ar.article_id) as pubs, a.total_pubs, a.h_index from ' \
                      '(select article_id from article where venue in (%s) and year >= %s and year <= %s) as ar ' \
                      'natural join author_article aa natural join author a GROUP BY a.author_id ORDER BY pubs DESC'
                p = [conference, 1970, 2020]
                c.execute(sql, p)
                authors = c.fetchall()
                conn.close()
                return len(authors)
            for conf in conferences[domain]:
                assert test_one(conf) > 0
        for d in conferences.keys():
            test_pubs_available_for_domain(domain=d)

