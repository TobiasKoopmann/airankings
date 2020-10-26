from lxml import etree
from datetime import datetime
from tqdm import tqdm
import csv
import json
import re

# all of the element types in dblp
all_elements = {"article", "inproceedings", "proceedings", "book", "incollection", "phdthesis", "mastersthesis", "www"}
# all of the feature types in dblp
all_features = {"address", "author", "booktitle", "cdrom", "chapter", "cite", "crossref", "editor", "ee", "isbn",
                "journal", "month", "note", "number", "pages", "publisher", "school", "series", "title", "url",
                "volume", "year"}


def log_msg(message):
    """Produce a log with current time"""
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)


def context_iter(dblp_path):
    """Create a dblp data iterator of (event, element) pairs for processing"""
    return etree.iterparse(source=dblp_path, dtd_validation=True, load_dtd=True)  # required dtd


def clear_element(element):
    """Free up memory for temporary element tree after processing the element"""
    element.clear()
    while element.getprevious() is not None:
        del element.getparent()[0]


def count_pages(pages):
    """Borrowed from: https://github.com/billjh/dblp-iter-parser/blob/master/iter_parser.py
    Parse pages string and count number of pages. There might be multiple pages separated by commas.
    VALID FORMATS:
        51         -> Single number
        23-43      -> Range by two numbers
    NON-DIGITS ARE ALLOWED BUT IGNORED:
        AG83-AG120
        90210H     -> Containing alphabets
        8e:1-8e:4
        11:12-21   -> Containing colons
        P1.35      -> Containing dots
        S2/109     -> Containing slashes
        2-3&4      -> Containing ampersands and more...
    INVALID FORMATS:
        I-XXI      -> Roman numerals are not recognized
        0-         -> Incomplete range
        91A-91A-3  -> More than one dash
        f          -> No digits
    ALGORITHM:
        1) Split the string by comma evaluated each part with (2).
        2) Split the part to subparts by dash. If more than two subparts, evaluate to zero. If have two subparts,
           evaluate by (3). If have one subpart, evaluate by (4).
        3) For both subparts, convert to number by (4). If not successful in either subpart, return zero. Subtract first
           to second, if negative, return zero; else return (second - first + 1) as page count.
        4) Search for number consist of digits. Only take the last one (P17.23 -> 23). Return page count as 1 for (2)
           if find; 0 for (2) if not find. Return the number for (3) if find; -1 for (3) if not find.
    """
    cnt = 0
    for part in re.compile(r",").split(pages):
        subparts = re.compile(r"-").split(part)
        if len(subparts) > 2:
            continue
        else:
            try:
                re_digits = re.compile(r"[\d]+")
                subparts = [int(re_digits.findall(sub)[-1]) for sub in subparts]
            except IndexError:
                continue
            cnt += 1 if len(subparts) == 1 else subparts[1] - subparts[0] + 1
    return "" if cnt == 0 else str(cnt)


def extract_feature(elem, features, include_key=False):
    """Extract the value of each feature"""
    if include_key:
        attribs = {'key': [elem.attrib['key']]}
    else:
        attribs = {}
    for feature in features:
        attribs[feature] = []
    for sub in elem:
        if sub.tag not in features:
            continue
        if sub.tag == 'title':
            text = re.sub("<.*?>", "", etree.tostring(sub).decode('utf-8')) if sub.text is None else sub.text
        elif sub.tag == 'pages':
            text = count_pages(sub.text)
        else:
            text = sub.text
        if text is not None and len(text) > 0:
            attribs[sub.tag] = attribs.get(sub.tag) + [text]
    return attribs


def parse_all(dblp_path, save_path, include_key=False):
    log_msg("PROCESS: Start parsing...")
    f = open(save_path, 'w', encoding='utf8')
    for _, elem in context_iter(dblp_path):
        if elem.tag in all_elements:
            attrib_values = extract_feature(elem, all_features, include_key)
            f.write(str(attrib_values) + '\n')
        clear_element(elem)
    f.close()
    log_msg("FINISHED...")  # load the saved results line by line using json


def parse_entity(dblp_path, save_path, type_name, features=None, save_to_csv=False, include_key=False):
    """Parse specific elements according to the given type name and features"""
    log_msg("PROCESS: Start parsing for {}...".format(str(type_name)))
    assert features is not None, "features must be assigned before parsing the dblp dataset"
    results = []
    attrib_count, full_entity, part_entity = {}, 0, 0
    for _, elem in tqdm(context_iter(dblp_path)):
        if elem.tag in type_name:
            attrib_values = extract_feature(elem, features, include_key)  # extract required features
            results.append(attrib_values)  # add record to results array
            for key, value in attrib_values.items():
                attrib_count[key] = attrib_count.get(key, 0) + len(value)
            cnt = sum([1 if len(x) > 0 else 0 for x in list(attrib_values.values())])
            if cnt == len(features):
                full_entity += 1
            else:
                part_entity += 1
        elif elem.tag not in all_elements:
            continue
        clear_element(elem)
    if save_to_csv:
        f = open(save_path, 'w', newline='', encoding='utf8')
        writer = csv.writer(f, delimiter=',')
        writer.writerow(features)  # write title
        for record in results:
            # some features contain multiple values (e.g.: author), concatenate with `::`
            row = ['::'.join(v) for v in list(record.values())]
            writer.writerow(row)
        f.close()
    else:  # default save to json file
        with open(save_path, mode='w', encoding='utf-8', errors='ignore') as f:
            for line in tqdm(results):
                json.dump(line, f)
                f.write("\n")
    return full_entity, part_entity, attrib_count, results


def parse_author(dblp_path, save_path, save_to_csv=False):
    type_name = ['article', 'book', 'incollection', 'inproceedings']
    log_msg("PROCESS: Start parsing for {}...".format(str(type_name)))
    authors = set()
    for _, elem in tqdm(context_iter(dblp_path)):
        if elem.tag in type_name:
            authors.update(a.text for a in elem.findall('author'))
        elif elem.tag not in all_elements:
            continue
        clear_element(elem)
    if save_to_csv:
        f = open(save_path, 'w', newline='', encoding='utf8')
        writer = csv.writer(f, delimiter=',')
        writer.writerows([a] for a in sorted(authors))
        f.close()
    else:
        with open(save_path, 'w', encoding='utf8') as f:
            f.write('\n'.join(sorted(authors)))
    log_msg("FINISHED...")


def parse_article(dblp_path, save_path, save_to_csv=False, include_key=False):
    type_name = ['article']
    features = ['title', 'author', 'year', 'journal', 'pages']
    full_entity, part_entity, attrib_count, results = parse_entity(dblp_path, save_path, type_name, features, save_to_csv=save_to_csv, include_key=include_key)
    log_msg('Total articles found: {}, articles contain all features: {}, articles contain part of features: {}'
            .format(full_entity + part_entity, full_entity, part_entity))
    log_msg("Features information: {}".format(str(attrib_count)))
    return results


def parse_inproceedings(dblp_path, save_path, save_to_csv=False, include_key=False):
    type_name = ["inproceedings"]
    features = ['title', 'author', 'year', 'pages', 'booktitle']
    full_entity, part_entity, attrib_count, results = parse_entity(dblp_path, save_path, type_name, features, save_to_csv=save_to_csv, include_key=include_key)
    log_msg('Total articles found: {}, articles contain all features: {}, articles contain part of features: {}'
            .format(full_entity + part_entity, full_entity, part_entity))
    log_msg("Features information: {}".format(str(attrib_count)))
    return results


def parse_proceedings(dblp_path, save_path, save_to_csv=False, include_key=False):
    type_name = ["proceedings"]
    features = ['title', 'editor', 'year', 'booktitle', 'series', 'publisher']
    # Other features are 'volume','isbn' and 'url'.
    full_entity, part_entity, attrib_count, results = parse_entity(dblp_path, save_path, type_name, features, save_to_csv=save_to_csv, include_key=include_key)
    log_msg('Total articles found: {}, articles contain all features: {}, articles contain part of features: {}'
            .format(full_entity + part_entity, full_entity, part_entity))
    log_msg("Features information: {}".format(str(attrib_count)))
    return results


def parse_book(dblp_path, save_path, save_to_csv=False, include_key=False):
    type_name = ["book"]
    features = ['title', 'author', 'publisher', 'isbn', 'year', 'pages']
    full_entity, part_entity, attrib_count, results = parse_entity(dblp_path, save_path, type_name, features, save_to_csv=save_to_csv, include_key=include_key)
    log_msg('Total articles found: {}, articles contain all features: {}, articles contain part of features: {}'
            .format(full_entity + part_entity, full_entity, part_entity))
    log_msg("Features information: {}".format(str(attrib_count)))
    return results


def parse_publications(dblp_path, save_path, save_to_csv=False, include_key=False) -> list:
    type_name = ['article', 'inproceedings']
    features = ['title', 'author', 'journal', 'year', 'pages', 'booktitle']
    full_entity, part_entity, attrib_count, results = parse_entity(dblp_path, save_path, type_name, features, save_to_csv=save_to_csv, include_key=include_key)
    log_msg('Total articles found: {}, articles contain all features: {}, articles contain part of features: {}'
            .format(full_entity + part_entity, full_entity, part_entity))
    log_msg("Features information: {}".format(str(attrib_count)))
    return results


def parse_dblp(dblp_path, save_path) -> list:
    # dblp_path = '../data/dblp2.xml'
    # save_path = '../data/article.json'
    try:
        context_iter(dblp_path)
        log_msg("LOG: Successfully loaded \"{}\".".format(dblp_path))
    except IOError:
        log_msg("ERROR: Failed to load file \"{}\". Please check your XML and DTD files.".format(dblp_path))
        exit()
    return parse_publications(dblp_path, save_path, include_key=True)


def elem2dict(node: etree) -> dict:
    """
    Convert an lxml.etree node tree into a dict.
    """
    result = {}
    for element in node.iterchildren():
        # Remove namespace prefix
        key = element.tag.split('}')[1] if '}' in element.tag else element.tag
        # Process element as tree element if the inner XML contains non-whitespace content
        if element.text and element.text.strip():
            value = element.text
        else:
            value = elem2dict(element)
        if key in result:
            if type(result[key]) is list:
                result[key].append(value)
            else:
                tmp = result[key]
                result[key] = [tmp] + [value]
        else:
            result[key] = value
    for attrib in node.keys():
        result[attrib] = node.get(attrib)
    return result


def parse_persons(dblp_path: str, save_path: str, author_list: set) -> None:
    type_name = ['www']
    log_msg("PROCESS: Start parsing for {}...".format(str(type_name)))
    authors = list()
    for _, elem in tqdm(context_iter(dblp_path)):
        if elem.tag in type_name:
            authors.append(elem2dict(elem))
        elif elem.tag not in all_elements:
            continue
        clear_element(elem)
    with open(save_path + "_all.json", 'w', encoding='utf8') as f:
        for line in authors:
            f.write(json.dumps(line) + "\n")
    res_author = []
    for author in tqdm(authors):
        if 'author' in author:
            if isinstance(author['author'], list) and any(curr_auth in author_list for curr_auth in author['author']):
                res_author.append(author)
            elif author['author'] in author_list:
                res_author.append(author)
    with open(save_path + '.json', 'w', encoding='utf8') as f:
        for line in res_author:
            f.write(json.dumps(line) + "\n")
    log_msg("FINISHED...")


def parse_dblp_person(dblp_path: str, save_path: str, author_list: list) -> None:
    try:
        context_iter(dblp_path)
        log_msg("LOG: Successfully loaded \"{}\".".format(dblp_path))
    except IOError:
        log_msg("ERROR: Failed to load file \"{}\". Please check your XML and DTD files.".format(dblp_path))
        exit()
    return parse_persons(dblp_path, save_path, author_list)


def flat_map_attr(x: list, attr: str = 'note') -> list:
    """
    Helper function for the DBLP note parsing
    :param x:
    :param attr:
    :return:
    """
    ret = []
    for i in x:
        if isinstance(i[attr], list):
            for j in i[attr]:
                if isinstance(j, str):
                    ret.append({"author": i['author'], attr: j.strip()})
        elif isinstance(i[attr], str):
            ret.append({"author": i['author'], attr: i[attr].strip()})
    return ret


def get_country_dict_from_urls(urls: list, domain_country: dict) -> dict:
    """
    :param urls:
    :params domain_country:
    :return:
    """
    def get_country(url: str):
        if url.strip().split(".")[-1] in domain_country:
            return domain_country[url.strip().split(".")[-1]]
    black_list_urls = ['orcid.org/', 'scholar.google.com/', 'twitter.com/', 'github.com/', 'linkedin.com/']
    urls = [x for x in urls if not any(black_url in x['url'] for black_url in black_list_urls)]
    urls = [(x['author'], x['url'], get_country(x['url'])) for x in urls if get_country(x['url'])]
    urls = [a for b in [[(y, x[1], x[2]) for y in x[0]] if isinstance(x[0], list) else [x] for x in urls] for a in b]
    return {x[0]: (x[1], x[2]) for x in urls}


def get_dblp_country(path_to_persons_file: str, path_to_country_file: str, output_path_country: str = None) -> list:
    """
    Extract all the countries from the person.json. Is using a country file as support.
    :param path_to_persons_file:
    :param path_to_country_file:
    :param output_path_country:
    :return:
    """
    with open(path_to_persons_file, "r", encoding="utf-8") as f:
        persons = f.readlines()
    persons = [json.loads(x) for x in persons]
    notes = flat_map_attr([x for x in persons if "note" in x])
    with open(path_to_country_file, "r", encoding="utf-8") as f:
        countries = f.readlines()
    domain_country = {x.strip().split(",")[1]: x.strip().split(",")[0] for x in countries}
    countries = [x.strip().split(",")[0] for x in countries]
    urls = flat_map_attr([x for x in persons if "url" in x], attr='url')
    urls = get_country_dict_from_urls(urls, domain_country)
    author_countries, url_counter = [], 0
    for author in notes:
        matched = False
        for c in countries:
            if c.lower() in author['note'].lower():
                if c == 'United States':
                    c = 'USA'
                if c == 'United Kingdom':
                    c = 'UK'
                author_countries.append({"author": author['author'], "country": c, "affiliation": author['note']})
                matched = True
        if not matched:
            author_names = author['author'] if isinstance(author['author'], list) else [author['author']]
            if any(auth in urls for auth in author_names):
                author_countries.append({"author": author['author'], "country": urls[author_names[0]][1],
                                         "url": urls[author_names[0]][0]})
                url_counter += 1
    print("Resulting in", len(author_countries), "outputs. Matched ", str(url_counter), " from URLs. ")
    if output_path_country:
        with open(output_path_country, "w", encoding="utf-8") as f:
            for line in author_countries:
                json.dump(line, f)
                f.write("\n")
    return author_countries


if __name__ == '__main__':
    source = '../data/dblp2.xml'
    target = '../data/article.json'
    parse_dblp(source, target)
