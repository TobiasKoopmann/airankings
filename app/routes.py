import json
from app import app
from flask import render_template, request, Response
from app.myfunctions import get_special_url
from app.databases.querydb import *

basedir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(basedir, 'static/countries.txt')
with open(filename, "r", encoding="utf-8") as f:
    static_countries = f.readlines()
static_countries = tuple([x.strip() for x in static_countries if 'United States' not in x.strip()])

with open(basedir + '/static/languages.json') as json_file:
    language_dict = json.load(json_file)
curr_language = 'eng'

filename = os.path.join(basedir, 'static/ai_venues.json')
with open(filename, 'r', encoding='utf-8') as f:
    confs = json.load(f)
confs = {k: list(v.keys()) for k, v in confs.items()}


@app.route('/', methods=['GET'])
def index(selected_venues: list = ['core'] + confs['core'], countries: tuple = static_countries):
    start = time.time()
    search_all = False
    if request.args:
        if request.args.get('venues'):
            selected = request.args.get('venues').split(",")
        else:
            selected = selected_venues
        if request.args.get('country'):
            country = request.args.get('country')
        else:
            country = 'Germany'
        if request.args.get('fromyear'):
            year_start = int(request.args.get('fromyear'))
        else:
            year_start = 1970
        if request.args.get('toyear'):
            year_end = int(request.args.get('toyear'))
        else:
            year_end = 2020
        if request.args.get('search'):
            search_term = request.args.get('search')
            name = search_term.lower()
        else:
            name = None
        if request.args.get('orderby'):
            order_by = request.args.get('orderby').lower()
        else:
            order_by = 'pubs'
        if request.args.get('orderdirection'):
            order_dir = request.args.get('orderdirection').lower()
        else:
            order_dir = 'desc'
        if request.args.get('page'):
            page = int(request.args.get('page'))
        else:
            page = 1
        if request.args.get('language'):
            language = request.args.get('language').lower()
            global curr_language
            if language != curr_language:
                curr_language = language
    else:
        country = 'Germany'
        selected = list(selected_venues)
        order_by, order_dir, name, search_term, year_start, year_end, page, language = 'pubs', 'desc', None, None, \
                                                                                       1970, 2020, 1, 'eng'
    desc = True if order_dir == "desc" else False
    if not selected:
        total_count, authors = 0, []
    else:
        total_count, authors = mysql_get_authors(venues=selected, country=country, start_year=year_start,
                                                 end_year=year_end, page=page, name=name, order_by=order_by,
                                                 desc=desc)
        if total_count == 0 and country != "all":
            country = 'all'
            total_count, authors = mysql_get_authors(venues=selected, country=country, start_year=year_start,
                                                     end_year=year_end, page=page, name=name, order_by=order_by,
                                                     desc=desc)
            search_all = True
    if request.args.get("download"):
        def generate():
            for row in authors:
                for i in range(len(row)):
                    if i < len(row) - 1:
                        yield str(row[i]) + ','
                    else:
                        yield str(row[i]) + '\n'

        csvfile = generate()
        response = Response(csvfile, mimetype='text/csv',
                            headers={"Content-Disposition": 'attachment;filename=ratings.csv'})
        return response
    print("Time took: ", str(time.time() - start))

    return render_template('query.html', title='Author Rank', order_by=order_by, desc=order_dir, main_page=True,
                           authors=authors, pubs=[], countries=countries, country=country, yearstart=year_start,
                           yearend=year_end, page=page, author_count=total_count, name=name,
                           search_all=search_all, selected=selected, confs=confs, lang=language_dict[curr_language])


@app.route('/ps')
def problem_solving():
    return index(['problem_solving'] + confs['problem_solving'])


@app.route('/kr')
def knowledge_representation():
    return index(['knowledge_representation'] + confs['knowledge_representation'])


@app.route('/u')
def uncertainty():
    return index(['uncertainty'] + confs['uncertainty'])


@app.route('/ml')
def machine_learning():
    return index(['machine_learning'] + confs['machine_learning'])


@app.route('/cv')
def computer_vision():
    return index(['computer_vision'] + confs['computer_vision'])


@app.route('/nlp')
def natural_language_processing():
    return index(['natural_language_processing'] + confs['natural_language_processing'])


@app.route('/i')
def interaction():
    return index(['interaction'] + confs['interaction'])


@app.route('/r')
def robotics():
    return index(['robotik'] + confs['robotik'])


@app.route('/all')
def all():
    return index(['all'] + list(confs.keys()) + [a for b in confs.values() for a in b])


@app.route('/author')
def author():
    name = request.args.get('name').lower()
    if request.args.get('language'):
        language = request.args.get('language').lower()
        global curr_language
        if language != curr_language:
            curr_language = language
    pubs, author_id, h_index = mysql_get_pubs(name)
    urls = mysql_get_urls(author_id)
    affiliation = mysql_get_affiliation(author_id)
    stats = {
        "number_of_publications": len(pubs),
        "number_of_venues": len(list(set([p['venue'] for p in pubs]))),
        "h_index": h_index
    }
    special, other = get_special_url(urls)
    return render_template('author.html', name=name.title(), pubs=pubs, special=special, urls=other, stats=stats,
                           affiliation=affiliation, lang=language_dict[curr_language])


@app.route('/faq')
def faq():
    return render_template('faq.html', lang="eng")


@app.teardown_appcontext
def close_connection(exception):
    pass
