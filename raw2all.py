import re
import traceback
from copy import deepcopy
from collections import defaultdict

import bibtexparser
from bibtexparser.model import Entry, Field
from bibtexparser.library import Library
from bibtexparser.writer import BibtexFormat


mapping = {
    '*SEM': 'Conference on Lexical and Computational Semantics',
    'AAAI': 'Association for the Advancement of Artificial Intelligence',
    'ACL': 'Annual Meeting of the Association for Computational Linguistics',
    'ANLC': 'Applied Natural Language Processing',
    'AI': 'Artificial Intelligence',
    'AISTATS': 'Artificial Intelligence and Statistics',
    'ASRU': 'IEEE Automatic Speech Recognition and Understanding Workshop',
    'CAV': 'Computer Aided Verification',
    'CHI': 'Conference on Human Factors in Computing Systems',
    'CL': 'Computational Linguistics',
    'CLCLing': 'International Conference on Computational Linguistics and Intelligent Text Processing',
    'COLING': 'International Conference on Computational Linguistics',
    'CoNLL': 'SIGNLL Conference on Computational Natural Language Learning',
    'CVPR': 'the IEEE/CVF Conference on Computer Vision and Pattern Recognition',
    'COLT': 'Conference on Learning Theory',
    'EACL': 'Conference of the European Chapter of the Association for Computational Linguistics',
    'ECCV': 'European Conference on Computer Vision',
    'EMNLP': 'Conference on Empirical Methods in Natural Language Processing',
    'FOCS': 'Foundations of Computer Science',
    'HLT': 'Human Language Technology',
    'ICASSP': 'International Conference on Acoustics, Speech, and Signal Processing',
    'ICCV': 'IEEE International Conference on Computer Vision',
    'ICIPS': 'IEEE International Conference on Intelligent Processing Systems',
    'ICLR': 'International Conference on Learning Representations',
    'ICML': 'International Conference on Machine Learning',
    'ICRA': 'International Conference on Robotics and Automation',
    'ICSE': 'International Conference on Software Engineering',
    'ICTAI': 'IEEE International Conference on Tools with Artificial Intelligence',
    'IJCAI': 'International Joint Conference on Artificial Intelligence',
    'IJCNLP': 'International Joint Conference on Natural Language Processing',
    'ILSVRC': 'ImageNet Large Scale Visual Recognition Challenge',
    'INLG': 'International Natural Language Generation Conference',
    'IROS': 'International Conference on Intelligent Robots and Systems',
    'ISER': 'International Symposium on Experimental Robotics',
    'IWCS': 'International Conference on Computational Semantics',
    'IWSLT': 'International Conference on Spoken Language Translation',
    'JAIR': 'Journal of Artificial Intelligence Research',
    'JASA': 'Journal of the American Statistical Association',
    'JMLR': 'Journal of Machine Learning Research',
    'KDD': 'International Conference on Knowledge Discovery and Data Mining',
    'LREC': 'Language Resources and Evaluation Conference',
    'MLSLP': 'Symposium on Machine Learning in Speech and Language Processing',
    'NAACL': 'Conference of the North American Chapter of the Association for Computational Linguistics',
    'NAACL25': 'Annual Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics',
    'NeurIPS': 'Conference on Neural Information Processing Systems',
    'NCB': 'Nature Cell Biology',
    'NODALIDA': 'Nordic Conference on Computational Linguistics',
    'OSDI': 'Operating Systems Design and Implementation',
    'PAMI': 'IEEE Transactions on Pattern Analysis and Machine Intelligence',
    'PNAS': 'Proceedings of the National Academy of Sciences of the United States of America',
    'RECSYS': 'ACM Conference on Recommender Systems',
    'SALT': 'Semantics and Linguistic Theory',
    'SIGIR': 'ACM Special Interest Group on Information Retrieval',
    'SODA': 'Symposium on Discrete Algorithms',
    'SOSP': 'Symposium on Operating Systems Principles',
    'STOC': 'Symposium on Theory of Computing',
    'TACL': 'Transactions of the Association for Computational Linguistics',
    'TFS': 'IEEE Transaction on Fuzzy Systems',
    'TNN': 'IEEE Transaction on Neural Networks',
    'TOIS': 'ACM Transactions on Information Systems',
    'TSP': 'IEEE Transaction on Signal Processing',
    'UAI': 'Uncertainty in Artificial Intelligence',
    'UIST': 'User Interface Software and Technology',
    'WSDM': 'Web Search and Data Mining',
    'WMT': 'Conference on Machine Translation',
    'WWW': 'World Wide Web',
}


def abbr2full(abbr: str, year: int):
    abbr = abbr.replace('{', '').replace('}', '')
    parts = abbr.split('-')
    is_abbr = [part in mapping for part in parts]
    if all(is_abbr):
        ret = ''
        for part in parts:
            if int(year) >= 2025 and part == 'NAACL':
                part = 'NAACL25'
            ret += ' and ' + mapping[part]
        ret = ret[5:] + f' ({abbr})'
        return ret.replace('  ', ' ').strip()
    elif not is_abbr[0]:
        return abbr.replace('  ', ' ').strip()
    else:
        raise Exception(f'Unrecognized abbreviation: {abbr}')


def fix_name(authors):
    # BetterBibTex does not handle name prefix
    prefix_pattern = r'family=([\w. ]+), given=([\w. ]+), prefix=([\w. ]+), useprefix=(true|false)'
    for match in re.finditer(prefix_pattern, authors):
        name = match.string[match.start():match.end()]
        pieces = match.groups()
        new_name = f'{pieces[2]} {pieces[0]}, {pieces[1]}'
        assert name in authors
        authors = authors.replace(name, new_name)
    return authors


def shorten_name_list(authors):
    # for the case of many authors, only show the first a couple
    if len(authors) < 1024:
        return authors
    authors = list(map(lambda x: x.strip(), authors.split(' and ')))
    n_preserve = 10
    n_remove = len(authors) - n_preserve
    authors = authors[:n_preserve]
    authors.append(f'{n_remove} additional authors')
    return ' and '.join(authors)



def process_entry(entry1) -> Entry | None:
    entry1 = deepcopy(entry1)
    fields = entry1.fields_dict
    # remove illegal items
    if 'author' not in fields or fields['author'] == '':
        return None
    if 'keywords' in fields and 'nobib' in fields['keywords'].value:
        return None

    new = dict()
    if 'date' in fields and 'year' not in fields:
        new['year'] = fields['date'].value[:4]
    else:
        new['year'] = fields['year']

    if 'doi' in fields:
        new['url'] = 'https://doi.org/' + fields['doi'].value
    elif 'url' in fields:
        # prefer using https
        new['url'] = fields['url'].value.replace('http://', 'https://')
        if not new['url'].startswith('http'):
            new.pop('url', None)
    elif fields.get('eprinttype', '') == 'arxiv' and 'eprint' in fields:
        arxiv_patterns = [r'^\w+/\d+(v\d+)?$', r'^\d+\.\d+(v\d+)?$']
        if any([re.findall(pat, fields['eprint'].value) for pat in arxiv_patterns]):
            new['url'] = 'https://arxiv.org/abs/' + fields['eprint'].value

    new['author'] = shorten_name_list(fix_name(fields['author'].value))

    et = entry1.entry_type
    # clean up fields
    if entry1.entry_type == 'article':
        to_keep = ['volume', 'issue', 'publisher', 'pages']
        new['journal'] = abbr2full(fields['journaltitle'].value, new['year'])
        if 'number' in fields:
            new['issue'] = fields['number'].value
    elif entry1.entry_type == 'inproceedings':
        to_keep = []
        new['booktitle'] = abbr2full(fields['booktitle'].value, new['year']).strip()
    elif entry1.entry_type == 'incollection':
        to_keep = ['booktitle', 'pages', 'publisher']
    elif entry1.entry_type == 'thesis':
        to_keep = ['institution', 'type']
    else:
        et = 'misc'
        to_keep = []

    common_keeps = ['year', 'title']
    for k in list(fields):
        if k in common_keeps + to_keep:
            new[k] = fields[k].value
    return Entry(et, entry1.key, [Field(key, value) for key, value in new.items()])


def inspect(bib_db):
    entries = defaultdict(list)
    for entry in bib_db.entries:
        entries[entry['ENTRYTYPE']].append(entry)
    for entry_type, items in entries.items():
        print('-' * 20)
        print(entry_type, len(items))
        fields = set()
        for entry in items:
            fields.update(set(entry.keys()))
        print('fields:', ', '.join(fields))
        if len(items) < 10:
            print('They are: ', ', '.join([item['ID'] for item in items]))


def raw2all():
    raw_path = './raw.bib'
    bib_db = bibtexparser.parse_file(raw_path)
    # inspect(bib_db)

    new_entries = list()
    errored = list()
    for entry in list(bib_db.entries):
        try:
            processed = process_entry(entry)
        except Exception as e:
            print(traceback.format_exc())
            errored.append(entry.key)
            processed = None
        if processed:
            new_entries.append(processed)

    if errored:
        print('Error when processing', ' '.join(errored))

    new_db = Library(new_entries)
    bib_format = BibtexFormat()
    bib_format.indent = '  '
    bibtexparser.write_file('./ref.bib', new_db, bibtex_format=bib_format)


if __name__ == '__main__':
    raw2all()
