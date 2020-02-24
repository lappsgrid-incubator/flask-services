"""builder.py

Utility to help build web pages. The HtmlBuilder uses classes from html_utils to
create the HTML for the application.

categories(self, services)

    Builds an html <div> tag which contains a bunch of paragraphs like the
    following:

    <p>
    <a href=http://vocab.lappsgrid.org/Token>http://vocab.lappsgrid.org/Token</a><br/>
    <blockquote>
    brandeis_eldrad_grid_1:gate.annie.tokenizer_0.0.1<br/>
    brandeis_eldrad_grid_1:gate.opennlp.tokenizer_0.0.1<br/>
    </blockquote>
    </p>

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
        views = result['payload']['views']
        buttons = []
        contents = []
        buttons.append(create_tab_button('Text'))
        contents.append(create_text_tab_content('Text', text))
        Identifier.count = 0
        for view in views:
            # TODO: want to use the view id if it is available
            identifier = Identifier.new()
            button = create_tab_button(identifier)
            content = create_view_tab_content(identifier, view)
            buttons.append(button)
            contents.append(content)
        all = Tag('div')
        tabs = Tag('div', attrs={'class': 'tab'})
        for b in buttons:
            tabs.add(b)
        all.add(tabs)
        for c in contents:
            all.add(c)
        return Markup(str(all))


def create_tab_button(identifier):
    attrs = {'class': "tablinks", 'onclick': "display(event, '%s')" % identifier}
    return Tag('button', attrs=attrs, dtrs=Text(identifier))


def create_text_tab_content(identifier, text):
    attrs = {'class': 'result pre'}
    return Tag('div',
               attrs={'id': identifier, 'class': 'tabcontent'},
               dtrs=Tag('div', attrs=attrs, dtrs=Text(text)))


def create_view_tab_content(identifier, view):
    attrs1 = {'class': 'result pre header'}
    attrs2 = {'class': 'result pre'}
    return Tag('div',
               attrs={'id': identifier, 'class': 'tabcontent'},
               dtrs=[Tag('div', attrs=attrs1, dtrs=Text('Contains')),
                     Tag('div',
                         attrs=attrs2,
                         dtrs=Text(dump(view['metadata']['contains']))),
                     Tag('div', attrs=attrs1, dtrs=Text('Annotations')),
                     Tag('div',
                         attrs=attrs2,
                         dtrs=Text(dump(view['annotations'])))])


def dump(obj):
    return json.dumps(obj, indent=4)

        
class Identifier(object):
    count = 0
    @classmethod
    def new(cls):
        Identifier.count += 1
        return "View-%d" % Identifier.count
