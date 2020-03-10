import io

from html_utils import Tag, Text


def visualize(identifier, view, text):
    """Given the identifier, determine what kind of visualization to use and return
    that visualization as a string. Use a table as the default."""
    if identifier.endswith('Token'):
        return tab_separated_tokens(view)
    elif identifier.endswith('Token#pos'):
        return tab_separated_tokens_with_pos(view)
    elif identifier.endswith('Sentence'):
        return one_sentence_per_line(view, text)
    elif identifier.endswith('NamedEntity'):
        return entities(view, text)
    elif identifier.endswith('PhraseStructure'):
        return phrase_structure(view, text)
    else:
        return table_of_annotations(view, text)


def tab_separated_tokens(view):
    """Print tokens separated by whitespace."""
    s = io.StringIO()
    for token in view['annotations']:
        if token['@type'].endswith('Token'):
            s.write('%s ' % token['features']['word'])
    return s.getvalue()


def tab_separated_tokens_with_pos(view):
    """Print tokens separated by whitespace and in the tok/pos format."""
    s = io.StringIO()
    for token in view['annotations']:
        if token['@type'].endswith('Token#pos'):
            s.write('%s/%s ' % (token['features']['word'],
                                token['features']['pos']))
    return s.getvalue()


def one_sentence_per_line(view, text):
    """Print one sentence per line, but do not use changes of whitespace to indicate
    token boundaries."""
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
        # TODO: a bit of a hack, and incomplete to boot
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
    """Simply return the penntree feature."""
    # TODO: horribly naieve and limited
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


def table_of_annotations(view, text):
    """Print all annotations in a table."""
    table = Tag('table', attrs={'cellpadding': 5, 'cellspacing': 0, 'border': 1})
    for token in view['annotations']:
        tr = table.add(Tag('tr', attrs={'valign': 'top'}))
        p1 = token.get('start')
        p2 = token.get('end')
        word = text[p1:p2] if (p1 is not None and p2 is not None) else '-'
        tr.add(Tag('td', dtrs=Text(token['@type'].split('/')[-1])))
        # TODO: add the target feature if it is used
        if p1 is not None and p2 is not None:
            tr.add(Tag('td', dtrs=Text("%s:%s" % (p1, p2))))
        else:
            tr.add(Tag('td', dtrs=Text("&nbsp;")))
        tr.add(Tag('td', dtrs=Text(features(token))))
    return str(table)


def features(token):
    label = token.get('label')
    features = token.get('features', {})
    table = Tag('table', attrs={'cellpadding': 0, 'cellspacing': 0, })
    # this part is a bit of a hack to deal with some old services that had the
    # label feature on the annotation type instead of in the features dictionary
    if label is not None:
        _add_key_value_row(table, 'label', label)
    for (k, v) in features.items():
        _add_key_value_row(table, k, v)
    return str(table)


def _add_key_value_row(table, k, v):
    table.add(Tag('tr',
                  attrs={'valign': 'top'},
                  dtrs=[Tag('td', dtrs=Text(k)),
                        Tag('td', dtrs=Text('&nbsp;&xrarr;&nbsp;')),
                        Tag('td', dtrs=Text(str(v)))]))


def _abbreviate_entity_type(atype):
    return atype[:3].lower()

