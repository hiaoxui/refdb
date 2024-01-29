import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter


mapping = {
    'AAAI': 'Association for the Advancement of Artificial Intelligence',
    'ACL': 'Annual Meeting of the Association for Computational Linguistics',
    'AI': 'Artificial Intelligence',
    'AISTATS': 'Artificial Intelligence and Statistics',
    'ASRU': 'IEEE Automatic Speech Recognition and Understanding Workshop',
    'CAV': 'Computer Aided Verification',
    'CHI': 'Conference on Human Factors in Computing Systems',
    'CLCLing': 'International Conference on Computational Linguistics and Intelligent Text Processing',
    'COLING': 'International Conference on Computational Linguistics',
    'CoNLL': 'The SIGNLL Conference on Computational Natural Language Learning',
    'CVPR': 'The IEEE/CVF Conference on Computer Vision and Pattern Recognition',
    'COLT': 'Conference on Learning Theory',
    'EACL': 'Annual Conference of the European Chapter of the Association for Computational Linguistics',
    'ECCV': 'European Conference on Computer Vision',
    'EMNLP': 'Conference on Empirical Methods in Natural Language Processing',
    'FOCS': 'Foundations of Computer Science',
    'HLT': 'Human Language Technology',
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
    'JAIR': 'Journal of Artificial Intelligence Research',
    'JASA': 'Journal of the American Statistical Association',
    'JMLR': 'Journal of Machine Learning Research',
    'KDD': 'International Conference on Knowledge Discovery and Data Mining',
    'LREC': 'Language Resources and Evaluation Conference',
    'MLSLP': 'Symposium on Machine Learning in Speech and Language Processing',
    'NAACL': 'Annual Conference of the North American Chapter of the Association for Computational Linguistics',
    'NeurIPS': 'Conference on Neural Information Processing Systems',
    'NODALIDA': 'Nordic Conference on Computational Linguistics',
    'OSDI': 'Operating Systems Design and Implementation',
    'PAMI': 'IEEE Transactions on Pattern Analysis and Machine Intelligence',
    'PNAS': 'Proceedings of the National Academy of Sciences of the United States of America',
    'RECSYS': 'ACM Conference on Recommender Systems',
    'SALT': 'Semantics and Linguistic Theory',
    'SIGIR': 'ACM Special Interest Group on Information Retreival',
    'SODA': 'Symposium on Discrete Algorithms',
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


def abbr2full(abbr: str):
    abbr = abbr.replace('{', '').replace('}', '')
    parts = abbr.split('-')
    is_abbr = [part in mapping for part in parts]
    if all(is_abbr):
        ret = ''
        for part in parts:
            ret += ' and ' + mapping[part]
        ret = ret[5:] + f' ({abbr})'
        return ret.replace('  ', ' ').strip()
    elif not is_abbr[0]:
        return abbr.replace('  ', ' ').strip()
    else:
        raise Exception(f'Unrecognized abbreviation: {abbr}')


def raw2all():
    parser = BibTexParser(common_strings=False, ignore_nonstandard_types=False)
    raw_path = './raw.bib'
    bib_db = bibtexparser.loads(open(raw_path, 'r', encoding='utf8').read(), parser)

    def process_entry(entry):
        # remove illegal items
        if 'author' not in entry or entry['author'] == '':
            return None
        if 'nobib' in entry.get('keywords', ''):
            return None
        # clean up fields
        if 'date' in entry and 'year' not in entry:
            entry['year'] = entry['date'][:4]
            del entry['date']
        if entry['ENTRYTYPE'] == 'article':
            entry['journal'] = abbr2full(entry['journaltitle'])
            entry.pop('journaltitle', None)
            entry.pop('booktitle', None)
        elif entry['ENTRYTYPE'] == 'inproceedings':
            entry['booktitle'] = 'Proceedings of ' + abbr2full(entry['booktitle']).strip()
            for to_remove in ['journal', 'volumn', 'number', 'pages', 'publisher', 'issue']:
                entry.pop(to_remove, None)
        else:
            entry['ENTRYTYPE'] = 'misc'
            for to_remove in ['journal', 'volumn', 'number', 'pages', 'publisher', 'issue', 'booktitle']:
                entry.pop(to_remove, None)

        if 'url' in entry:
            # prefer using https
            entry['url'] = entry['url'].replace('http://', 'https://')
            if not entry['url'].startswith('http'):
                entry.pop('url', None)
        elif 'doi' in entry:
            entry['url'] = 'https://doi.org/' + entry['doi']

        tokeep = [
            'author', 'booktitle', 'year', 'url', 'journal', 'volumn', 'number',
            'pages', 'issue', 'ENTRYTYPE', 'ID', 'title',
        ]
        for k in list(entry):
            if k not in tokeep:
                entry.pop(k, None)
        return entry

    bib_db.entries = list(filter(lambda z: z is not None, map(process_entry, bib_db.entries)))

    writer = BibTexWriter()
    writer.indent = '  '
    # writer.comma_first = True
    with open('ref.bib', 'w') as bibfile:
        bibfile.write(writer.write(bib_db))


if __name__ == '__main__':
    raw2all()
