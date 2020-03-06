"""builder.py

Utility to help build web pages. The HtmlBuilder uses classes from html_utils to
create the HTML for the application.

categories(self, services)

    Builds an html <div> tag which contains a bunch of paragraphs like the
    following:

    <p>
      <a href=http://vocab.lappsgrid.org/Token>http://vocab.lappsgrid.org/Token</a>
      <br/>
      <blockquote>
        brandeis_eldrad_grid_1:gate.annie.tokenizer_0.0.1<br/>
        brandeis_eldrad_grid_1:gate.opennlp.tokenizer_0.0.1<br/>
      </blockquote>
    </p>

chain(self, chain)

result(self, result)

"""

import io
import json
from flask import Markup

from html_utils import Tag, Text, Href


class HtmlBuilder(object):

    """Utility class to help create HTML code for the LAPPS-Flask site."""

    def categories(self, services):
        """Builds an html <div> tag which contains a paragraph for each category."""
        div = Tag('div')
        for annotation_types in sorted(services.categories):
            p = Tag('p')
            if not annotation_types:
                p.add(Text('None'))
            else:
                for annotation_type in annotation_types:
                    p.add(Href(annotation_type, annotation_type))
                    p.add(Tag('br'))
            block = Tag('blockquote')
            for service in services.categories[annotation_types]:
                block.add(Text(service.identifier))
                block.add(Tag('br'))
            p.add(block)
            div.add(p)
        return Markup(str(div))

    def chain(self, chain):
        dl = Tag('dl', attrs={'class': 'bordered'})
        dl.add(Tag('dt', dtrs=Text(chain.identifier)))
        dd = Tag('dd')
        for service in chain.services:
            dd.add(Text(service.identifier))
            dd.add(Tag('br'))
        dl.add(dd)
        return Markup(str(dl))

    def result(self, result):
        text = result['payload']['text']['@value']
        json_str = json.dumps(result['payload'], indent=4)
        views = result['payload']['views']
        buttons = [tab_button('Text'), tab_button('LIF')]
        contents = [tab_text('Text', text), tab_text('LIF', json_str)]
        Identifier.count = 0
        for view in views:
            # TODO: use the id if there is one
            view_identifier = Identifier.new()
            annotation_types = view['metadata']['contains'].keys()
            annotation_types = [at.split('/')[-1] for at in annotation_types]
            buttons.append(tab_button(view_identifier))
            contents.append(tab_content(view_identifier, annotation_types, view, text))
        main_div = Tag('div')
        tabs = Tag('div', attrs={'class': 'tab'})
        tabs.add_all(buttons)
        main_div.add(tabs)
        main_div.add_all(contents)
        return Markup(str(main_div))


def tab_button(identifier):
    fun = "display(event, '%s', 'tab_c1', 'tab_b1')" % identifier
    attrs = {'class': "tab_b1", 'onclick': fun}
    return Tag('button', attrs=attrs, dtrs=Text(identifier))


def tab_button_sub(identifier):
    fun = "display(event, '%s', 'tab_c2', 'tab_b2')" % identifier
    attrs = {'class': "tab_b2", 'onclick': fun}
    return Tag('button', attrs=attrs, dtrs=Text(identifier.split(':')[-1]))


def tab_text(identifier, text):
    attrs = {'class': 'result pre'}
    return Tag('div',
               attrs=_attrs(identifier, 'tab_c1', "display: none;"),
               dtrs=[Tag('br'), Tag('div', attrs=attrs, dtrs=Text(text))])


def tab_content(identifier, annotation_types, view, text):
    content = Tag('div', attrs=_attrs(identifier, 'tab_c1', "display: none;"))
    sub_tabs = Tag('div', attrs={'class': 'tab'})
    sub_contents = []
    for atype in annotation_types:
        identifier_sub = identifier + ':' + atype
        sub_tabs.add(tab_button_sub(identifier_sub))
        sub_contents.append(
            Tag('div',
                attrs=_attrs(identifier_sub, 'tab_c2', "display: none;"),
                dtrs=[Tag('div',
                          attrs={'class': 'result pre'},
                          dtrs=visualize(identifier_sub, view, text))]))
    content.add(Tag('br'))
    content.add(sub_tabs)
    content.add(Tag('br'))
    for sub_content in sub_contents:
        content.add(sub_content)
    return content


def _attrs(_id, _class, style):
    """Utility method to create an attribute dictionary when you have identifier,
    class and style."""
    return {'id': _id, 'class': _class, 'style': style}


def visualize(identifier, view, text):
    """Given the identifier, determine what kind of visualization to use and return
    the visualization, typically as a text."""
    # TODO: this should go to its own module
    if identifier.endswith('Token'):
        return Text(token_visualization(view))
    elif identifier.endswith('Token#pos'):
        return Text(pos_visualization(view))
    else:
        return Text(table_visualization(view, text))


def token_visualization(view):
    s = io.StringIO()
    for token in view['annotations']:
        if token['@type'].endswith('Token'):
            s.write('%s ' % token['features']['word'])
    return s.getvalue()


def pos_visualization(view):
    s = io.StringIO()
    for token in view['annotations']:
        if token['@type'].endswith('Token#pos'):
            s.write('%s/%s ' % (token['features']['word'],
                                token['features']['pos']))
    return s.getvalue()


def table_visualization(view, text):
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


def dump(obj):
    return json.dumps(obj, indent=4)

        
class Identifier(object):
    count = 0
    @classmethod
    def new(cls):
        Identifier.count += 1
        return "View-%d" % Identifier.count
