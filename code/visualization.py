import io

from html_utils import Tag, Text


def tab_separated_tokens(view):
    s = io.StringIO()
    for token in view['annotations']:
        if token['@type'].endswith('Token'):
            s.write('%s ' % token['features']['word'])
    return s.getvalue()


def tab_separated_tokens_with_pos(view):
    s = io.StringIO()
    for token in view['annotations']:
        if token['@type'].endswith('Token#pos'):
            s.write('%s/%s ' % (token['features']['word'],
                                token['features']['pos']))
    return s.getvalue()


def one_sentence_per_line(view, text):
    s = io.StringIO()
    for sent in view['annotations']:
        if sent['@type'].endswith('Sentence'):
            p1 = sent.get('start')
            p2 = sent.get('end')
            s.write('%s\n\n' % text[p1:p2])
    return s.getvalue()


def entities(view, text):
    entities = []
    starts = {}
    ends = {}
    for a in view['annotations']:
        atype = a['@type'].split('/')[-1]
        # a bit of a hack, and incomplete to boot
        if atype in ('NamedEntity', 'Person', 'Location'):
            entities.append(a)
            starts[a.get('start')] = atype
            ends[a.get('end')] = atype
    s = io.StringIO()
    for (i, c) in enumerate(text):
        if i in starts:
            s.write('<e style="color:blue;">')
        if i in ends:
            s.write('</e>')
            s.write('<sup>%s</sup>' % _abbreviate_entity_type(ends[i]))
        s.write(c)
    return s.getvalue()


def phrase_structure(view, text):
    s = io.StringIO()
    phrases = []
    for a in view['annotations']:
        atype = a['@type'].split('/')[-1]
        if atype in ('PhraseStructure',):
            phrases.append(a)
    for phrase in phrases:
        s.write(phrase['features']['sentence'] + '\n\n')
        s.write(phrase['features']['penntree'] + '\n')
    return s.getvalue()


def table_of_markables(view, text):
    table = Tag('table', attrs={'cellpadding': 8})
    for token in view['annotations']:
        tr = table.add(Tag('tr'))
        p1 = token.get('start')
        p2 = token.get('end')
        word = text[p1:p2] if (p1 is not None and p2 is not None) else '-'
        tr.add(Tag('td', dtrs=Text(token['@type'].split('/')[-1])))
        tr.add(Tag('td', dtrs=Text(str(token.get('start', '-')))))
        tr.add(Tag('td', dtrs=Text(str(token.get('end', '-')))))
        tr.add(Tag('td', dtrs=Text(token.get('label', '-'))))
        tr.add(Tag('td', dtrs=Text(word)))
    return str(table)


def _abbreviate_entity_type(atype):
    return atype[:3].lower()

