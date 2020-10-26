import urllib.request
import shutil
import gzip
import json
import re
import os

from collections import defaultdict
from scholarmetrics import hindex

from tqdm import tqdm
from app.dblp_parser import parse_dblp, parse_dblp_person, get_dblp_country
from app.myfunctions import get_dblp_url

URL = 'http://dblp.org/xml/'
basedir = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = basedir + '/data/'
STATIC_PATH = basedir + '/app/static/'


def download_dblp() -> None:
    """
    Downloads the DBLP dataset and saves it into the data_path, which is usually ./data.
    :return:
    """
    source_gz = URL + 'dblp.xml.gz'
    source_dtd = URL + 'dblp.dtd'
    target_gz = DATA_PATH + 'dblp.xml.gz'
    target_dtd = DATA_PATH + 'dblp.dtd'

    print('   Downloading file ' + source_gz)
    with urllib.request.urlopen(source_gz) as response, open(target_gz, 'wb') as fh:
        shutil.copyfileobj(response, fh)
    print('   Downloading file ' + source_dtd)
    with urllib.request.urlopen(source_dtd) as response, open(target_dtd, 'wb') as fh:
        shutil.copyfileobj(response, fh)
    print('   Download finish!')
    print()


def unzip_dblp() -> None:
    """
    Unzips the downloaded DBLP dataset.
    :return:
    """
    source = DATA_PATH + 'dblp.xml.gz'
    target = DATA_PATH + 'dblp.xml'

    with gzip.open(source, 'rb') as f_in:
        with open(target, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print()


def extract_publications():
    """
    Parses the DBLP XML file to json, which can be used by this pipeline.
    :return:
    """
    source = DATA_PATH + 'dblp.xml'
    target = DATA_PATH + 'dblp.json'

    parse_dblp(source, target)
    print()


def extract_ai_publications() -> list:
    """
    Using the venue file (`./app/static/ai_venues.json`) to extract all publications from these respective venues.
    :return:
    """
    source = DATA_PATH + 'dblp.json'
    source_venues = STATIC_PATH + 'ai_venues.json'
    target_pubs = DATA_PATH + 'ai_dblp.json'

    authors = set()
    with open(source_venues, "r", encoding="utf-8") as f:
        tmp = json.load(f)
    # Create a dict for all instances
    venues = dict(pair for d in tmp.values() for pair in d.items())
    venues_set = set()
    for k, v in venues.items():
        venues_set.add(k)
        venues_set.update(v)

    def get_disambiguated_venue(venue_name: str):
        if venue_name in venues:
            return venue_name
        else:
            for k, v in venues.items():
                if venue_name in v:
                    return k

    print('   Parsing ' + source)
    with open(target_pubs, "w", encoding="utf-8") as out_f:
        with open(source, "r", encoding="utf-8") as in_f:
            for line in tqdm(in_f):
                line = json.loads(line)
                if line['booktitle']:
                    curr_venue = line['booktitle'][0]
                elif line['journal']:
                    curr_venue = line['journal'][0]
                curr_venue = re.sub(" \([0-9]+\)$", "", curr_venue)
                if curr_venue in venues_set:
                    line['venue'] = get_disambiguated_venue(curr_venue)
                    json.dump(line, out_f)
                    out_f.write("\n")
                    authors.update(line['author'])
    print('   Parse finish! File ai_dblp.json created!')
    print()
    return list(authors)


def download_semantic_scholar_if_needed(semantic_scholar_path: str, default_count: int = 184, download: bool = False):
    """
    Well, as the name says.
    :param semantic_scholar_path:
    :param default_count:
    :param download:
    :return:
    """
    sem_url = "https://s3-us-west-2.amazonaws.com/ai2-s2-research-public/open-corpus/2020-04-10/"
    if not os.path.exists(semantic_scholar_path):
        os.mkdir(semantic_scholar_path)
        download = True
    if download:
        print("   Downloading semantic scholar first. ")
        with urllib.request.urlopen(sem_url + "manifest.txt") as response, open(semantic_scholar_path + "manifest.txt", 'wb') as fh:
            shutil.copyfileobj(response, fh)
        with open(semantic_scholar_path + "/manifest.txt", "r") as f:
            for line in tqdm(f, total=default_count):
                line = line.strip()
                with urllib.request.urlopen(sem_url + line) as response, open(
                        semantic_scholar_path + line, 'wb') as fh:
                    shutil.copyfileobj(response, fh)
                if "s2-corpus-" in line:
                    with gzip.open(semantic_scholar_path + line, 'rb') as f_in:
                        with open(semantic_scholar_path + line[:-3], 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(semantic_scholar_path + line)


def match_semantic_scholar(download: bool = False):
    """
    Firstly, downloads the Semantic Scholar. Then tries to match all publications and extracts the citations.
    :param download:
    :return:
    """
    source = DATA_PATH + 'ai_dblp.json'
    target = DATA_PATH + 'ai_dataset.json'
    source_persons = DATA_PATH + 'persons.json'
    semantic_scholar_path = DATA_PATH + "semantic_scholar/"
    download_semantic_scholar_if_needed(semantic_scholar_path, download=download)

    def de_list(x, parse_int: bool = False):
        if isinstance(x, list):
            if parse_int:
                return int(x[0])
            return x[0]
        if parse_int:
            return int(x)
        return x

    def get_doi(line) -> str:
        """
        Get doi for a given line of the data, useful for semantic_scholar matching"
        """
        if "ee" in line:
            for x in de_list(line["ee"]):
                if "doi" in x:
                    return x.replace("https://doi.org/", "")

    with open(source_persons, encoding="utf-8") as file:
        persons = [json.loads(line) for line in file]
    # Put all author names into set
    authors = dict()
    for person in persons:
        if isinstance(person["author"], list):
            for auth in person['author']:
                authors[auth] = person['author'][0]
    with open(source, "r", encoding="utf-8") as f:
        pubs = f.readlines()
    pubs = [json.loads(x) for x in pubs]
    for pub in pubs:
        tmp = pub['author']
        for name in pub['author']:
            if name in authors:
                tmp.append(authors[name])
                tmp.remove(name)
        pub['author'] = tmp
    removed_indices = set()
    titles = defaultdict(list)
    [titles[x['title'][0].strip(".").lower()].append(i) for i, x in enumerate(pubs)]
    files = [file_path for file_path in os.listdir(semantic_scholar_path) if "s2-corpus-" in file_path]
    counter = 1
    with open(target, 'w', encoding="utf-8") as out_f:
        for file_path in files:
            print("Reading file ... (", str(counter), "/", str(len(files)), ")")
            with open(semantic_scholar_path + file_path, 'r', encoding="utf-8") as in_f:
                for line in in_f:
                    line = json.loads(line)
                    curr_title = de_list(line['title']).strip().lower()
                    if curr_title in titles:
                        index = None
                        for i in titles[curr_title]:
                            pub = pubs[i]
                            doi = get_doi(pub)
                            if doi and "doi" in line and line["doi"]:
                                if doi == line["doi"]:
                                    index = i
                                    break
                            elif "year" in line and de_list(pub["year"], True) == de_list(line["year"], True):
                                if line["venue"] == "ArXiv":
                                    if pub["journal"] and de_list(pub["journal"]) == "CoRR":
                                        index = i
                                        break
                                elif pub["journal"] and de_list(pub["journal"]) == "CoRR":
                                    continue
                                else:
                                    index = i
                                    break
                        if index and index not in removed_indices:
                            if 'in_citations' not in pub:
                                pub['inCitations'] = len(line['inCitations'])
                            json.dump(pub, out_f)
                            out_f.write("\n")
                            removed_indices.add(index)
            counter += 1
        for i, pub in enumerate(pubs):
            if i not in removed_indices:
                json.dump(pub, out_f)
                out_f.write("\n")
    print('   Parse finish! File ai_dataset.json created!')
    print()


def extract_persons(author_list: list) -> None:
    """
    Extracting all author information from DBLP, as affiliations etc.
    :param author_list:
    :return:
    """
    source = DATA_PATH + 'dblp.xml'
    target = DATA_PATH + 'persons'

    print('   Parsing ' + source)
    parse_dblp_person(source, target, author_list)
    print('   Parse finish! File persons.json created!')
    print()


def parse_countries() -> None:
    """
    Parses country information from the DBLp into the file 'author_countries.json'.
    :return: The file 'author_countries.json'
    """
    source_country = STATIC_PATH + 'countries_domain.txt'
    source_person = DATA_PATH + 'persons.json'
    target = DATA_PATH + 'author_countries.json'

    print('   Parsing ' + source_person)
    countries = get_dblp_country(source_person, source_country)
    with open(target, "w", encoding="utf-8") as f:
        for line in countries:
            json.dump(line, f)
            f.write("\n")
    print('   Parse finish! File author_countries.json created!')
    print()


def pipeline_prepare_db() -> None:
    """
    '*** Starting pipeline process to prepare PyCSRankings Database ***'
    Careful, it will download the semantic scholar, which is up to 240 GB large.
    :return: The files 'ai_dataset.json', 'persons.json' and 'author_countries.json' in the 'data' folder.
    """
    print('**** Starting pipeline process to prepare PyCSRankings Database ****')
    print()

    print('Process 01 - Download DBLP data')
    download_dblp()

    print('Process 02 - Unzipping DBLP data')
    unzip_dblp()

    print('Process 03 - Create dblp.json')
    extract_publications()

    print('Process 04 - Create ai_article.json')
    author_list = extract_ai_publications()

    print('Process 05 - Create persons.json')
    extract_persons(author_list)

    print('Process 06 - Create author_countries.json')
    parse_countries()

    print('Process 07 - Match with Semantic Scholar')
    # Be warned. This will download the semantic scholar dataset, which is rather large.
    match_semantic_scholar()

    print('*** Pipeline process to prepare PyCSRankings Database Finished! ***')


if __name__ == '__main__':
    pipeline_prepare_db()
