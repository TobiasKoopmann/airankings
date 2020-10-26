import sys
import json
from http.client import HTTPConnection, HTTPException
from bs4 import BeautifulSoup
import requests
import os

from threading import Thread
from airankings import main



basedir = os.path.abspath(os.path.dirname(__file__))
venueSource = basedir + '/../app/static/ai_venues.json'

URL = ('localhost', 5000)


class TestWebsite:
    #    website_thread = Thread(target=main)
    #    website_thread.start()

    @staticmethod
    def get_website(get='/'):

        try:
            conn = HTTPConnection(URL[0], URL[1])
            conn.request('GET', get)
            contents = conn.getresponse().read()
        except HTTPException:
            sys.exit('AIRankings could not be reached. ')

        try:
            soup = BeautifulSoup(contents, 'html.parser')
        except:
            sys.exit('HTML of web page is not valid. ')
        return soup

    def test_conferences(self):
        # Idea: checking if there are as many HTML-Elements representing Conferences as there should be
        # Number of Conferences in total: 96
        def iterate_through_conferences(my_dict, conference_list):
            for k, v in my_dict.items():
                if isinstance(v, dict):
                    iterate_through_conferences(v, conference_list)
                    continue
                conference_list.append(str(k))
            return conference_list

        soup = self.get_website()
        conferences_expected = []
        with open(venueSource) as venueJson:
            data = json.load(venueJson)
            conferences_expected = iterate_through_conferences(data, conferences_expected)

        counter = 0
        conferences_on_website = soup.find_all('li', class_="pl-2")
        for x in conferences_on_website:
            assert counter < len(conferences_on_website)
            venue_search = conferences_expected[counter]
            item = x.contents[1].contents[1].contents[3].contents
            actual_venue = str(item[0])
            # if (venue_search == actual_venue):
            assert venue_search == actual_venue
            counter += 1
        assert len(conferences_on_website) == len(conferences_expected)

    def test_table(self):
        soup = self.get_website()
        result = soup.find(id="query")
        assert len(result) > 0

    def test_search_function(self):
        session_requests = requests.session()
        response = session_requests.get("http://localhost:5000/?search=andreas%20hotho&venues=core,AAAI,IJCAI,ECAI,Artificial%20Intelligence,JAIR")
        website = BeautifulSoup(response.text, 'html.parser')
        search_results = website.findAll('td')
        assert response.status_code == 200
        assert len(search_results) != 0
        assert ("Andreas Hotho") in search_results[1].text

    def test_shareable_overlay(self):
        # there is no way of simulating a click on the share button using BeautifulSoup.
        # Using selenium could fix this issue
        print("Not Implemented yet!")

    def test_author_pages(self):
        url = 'http://localhost:5000/'
        session_requests = requests.session()
        r = session_requests.post(url)
        url = 'http://localhost:5000/author?name=luc%20de%20raedt'
        r = session_requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        assert r.status_code == 200
        assert len(soup) > 0

    def test_author_page_functions(self):
        authorpage = self.get_website("/author?name=luc%20de%20raedt")
        linkbox = authorpage.find("div", class_="col-6 border-left")
        assert len(linkbox.find_all('a')) > 0
        publication_table = authorpage.find("table", id='publication')
        assert publication_table is not None

    def test_search_by_googleid(self):
        session_requests = requests.session()
        response = session_requests.get("http://localhost:5000/?search=eWTzXFAAAAAJ&venues=core,AAAI,IJCAI,ECAI,Artificial%20Intelligence,JAIR")
        website = BeautifulSoup(response.text, 'html.parser')
        search_results = website.findAll('td')
        assert response.status_code == 200
        assert len(search_results) != 0
        assert ("Andreas Hotho") in search_results[1].text


# website_thread.join()
