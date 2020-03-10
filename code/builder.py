"""builder.py

Utility to help build web pages. The HtmlBuilder class uses classes from
html_utils to create the HTML for the application.

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

import os
import io
import json
from flask import Markup

from visualization import visualize
from utils import dump
from html_utils import Tag, Text, Href, div, button


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
                block.add_all([Text(service.identifier), Tag('br')])
            p.add(block)
            div.add(p)
        return Markup(str(div))

    def chain(self, chain):
        """Builds an HTML <dl> tag with the name of the chain and a list of services as
        the definition."""
        dt = Tag('dt', dtrs=Text(chain.identifier))
        dd = Tag('dd')
        dl = Tag('dl', attrs={'class': 'bordered'}, dtrs=[dt, dd])
        for service in chain.services:
            dd.add_all([Text(service.identifier), Tag('br')])
        return Markup(str(dl))

    def result(self, result):
        """Builds a <div> tag which contains the results of the analysis."""
        text = result['payload']['text']['@value']
        json_str = dump(result['payload'])
        views = result['payload']['views']
        buttons = [tab_button('Text'),
                   tab_button('LIF')]
        contents = [tab_text('Text', text),
                    tab_text('LIF', json_str)]
        ViewIdentifier.count = 0
        for view in views:
            view_identifier = view.get('id', ViewIdentifier.new())
            annotation_types = view['metadata']['contains'].keys()
            annotation_types = [os.path.basename(at) for at in annotation_types]
            buttons.append(tab_button(view_identifier))
            contents.append(tab_content(view_identifier, annotation_types, view, text))
        main_div = Tag('div')
        main_div.add(div({'class': 'tab'}, buttons))
        main_div.add_all(contents)
        return Markup(str(main_div))


def tab_button(identifier):
    """The button used for a top-level clickable tab."""
    fun = "display(event, '%s', 'tab_c1', 'tab_b1')" % identifier
    return button({'class': "tab_b1", 'onclick': fun}, Text(identifier))


def tab_button_sub(identifier):
    """The button used for a second-level clickable tab."""
    fun = "display(event, '%s', 'tab_c2', 'tab_b2')" % identifier
    return button({'class': "tab_b2", 'onclick': fun}, Text(identifier.split(':')[-1]))


def tab_text(identifier, text):
    return tab_text_aux(identifier, 'tab_c1', text)


def tab_text_sub(identifier, content):
    return tab_text_aux(identifier, 'tab_c2', content)


def tab_text_aux(identifier, _class, content):
    return div({'id': identifier, 'class': _class, 'style': "display: none;"},
               div({'class': 'result pre'}, Text(content)))


def tab_content(identifier, annotation_types, view, text):
    meta_id = "%s:Metadata" % identifier
    anno_id = "%s:Annotations" % identifier
    content = div({'id': identifier, 'class': 'tab_c1', 'style': "display: none;"}, [])
    sub_tabs = content.add(div({'class': 'tab2'},
                               [tab_button_sub(meta_id), tab_button_sub(anno_id)]))
    content.add_all([
        tab_text_sub(meta_id, dump(view.get('metadata'))),
        tab_text_sub(anno_id, dump(view.get('annotations')))])
    for annotation_type in annotation_types:
        id_sub = identifier + ':' + annotation_type
        sub_tabs.add(tab_button_sub(id_sub))
        content.add(tab_text_sub(id_sub, visualize(id_sub, view, text)))
    return content

        
class ViewIdentifier(object):
    """Class that generates new view identifiers if needed."""
    count = 0
    @classmethod
    def new(cls):
        ViewIdentifier.count += 1
        return "View-%d" % ViewIdentifier.count
