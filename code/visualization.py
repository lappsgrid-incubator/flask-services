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
        tr.add(Tag('td', dtrs=Text(word)))
    return str(table)

