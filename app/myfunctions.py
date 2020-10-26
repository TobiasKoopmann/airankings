import json
from tqdm import tqdm


def get_dblp_url(pname: str) -> str:
    # Modified from csrankings.js at csrankings.org

    # Ex: "Emery D. Berger" -> "http://dblp.uni-trier.de/pers/hd/b/Berger:Emery_D='
    # First, replace spaces and non - ASCII characters(not complete).
    # Known issue: does not properly handle suffixes like Jr., III, etc.
    name = pname.title()[:]
    chars = "'|\-|\."
    for c in chars:
        name = name.replace(c, '=')
    name = name.replace('Á', '=Aacute=')
    name = name.replace('á', '=aacute=')
    name = name.replace('è', '=egrave=')
    name = name.replace('é', '=eacute=')
    name = name.replace('í', '=iacute=')
    name = name.replace('ï', '=iuml=')
    name = name.replace('ó', '=oacute=')
    name = name.replace('ç', '=ccedil=')
    name = name.replace('ä', '=auml=')
    name = name.replace('ö', '=ouml=')
    name = name.replace('ø', '=oslash=')
    name = name.replace('Ö', '=Ouml=')
    name = name.replace('ü', '=uuml=')

    splitname = name.split(' ')

    lastname = splitname[-1]
    
    disambiguation = ''
    try:
        val = int(lastname)
    except ValueError:
        val = 0
    if val > 0:
        # this was a disambiguation entry; go back.
        disambiguation = lastname
        splitname.pop()
        lastname = splitname[-1] + '_' + disambiguation

    splitname.pop()
    newname = ' '.join(splitname)
    newname = newname.replace(' ', '_')
    # newname = newname.replace('\-', '=')
    text = "https://dblp.uni-trier.de/pers/hd"
    lastinitial = lastname[0].lower()
    text += "/" + lastinitial + "/" + lastname + ":" + newname
    return text


def json_file_to_list(fname: str) -> list:
    print('\nRunning json_file_to_list() on file: ' + fname)
    data = []

    with open(fname, 'r', encoding='utf-8') as fh:
        allpubs = fh.readlines()

    for line in tqdm(allpubs):
        pub = json.loads(line)
        data.append(pub)

    return data


def get_special_url(old_urls: list) -> (dict, list):
    special = dict()

    # Add Others
    github = []
    for url in old_urls:
        if 'dblp.uni-trier.de' in url:
            special['dblp'] = url
            old_urls.remove(url)
        if 'orcid.org/' in url:
            special['orcid'] = url
            old_urls.remove(url)
        elif 'scholar.google.com/' in url:
            special['gs'] = url
            old_urls.remove(url)
        elif 'twitter.com/' in url:
            special['twitter'] = url
            old_urls.remove(url)
        elif 'github.com/' in url:
            github.append(url)
            old_urls.remove(url)
        elif 'linkedin.com/' in url:
            special['linkedin'] = url
            old_urls.remove(url)

    if github:
        special['github'] = github

    return special, old_urls


if __name__ == '__main__':
    # d = get_dict_venues()
    # print(d)
    print(get_dblp_url("K. V. Rashmi"))
