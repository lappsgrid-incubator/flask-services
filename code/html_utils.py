"""html_utils.py

Utilities to help create HTML code. Contains classes that help build and print
HTML tags.

The two main classes are Tag and Text. To create a Text simply hand it the
string:

>>> text = Text("hello")

To wrap it in a paragraph and print the paragraph:

>>> p = Tag('p')
>>> p.add(text)
>>> print(str(p).strip())

This gives you something like

<p>hello</p>

You can add more text

>>> p.add(Text(" and goodbye"))

Now you have

<p>hello and goodbye</p>

Tags have daughters:

>>> Tag('div', dtrs=Tag('p', dtrs=[Text("hello "), Text(" world")]))

This would result in

<div>
  <p>hello world</p>
</div>

Adding attributes:

>>> Tag('div',
...     attrs={'class': 'example'},
...     dtrs=Tag('p', dtrs=[Text("hello world")]))

<div class="example">
  <p>hello world</p>
</div>

There are also some abbreviations:

>>> div({'class': 'example'},
...     Tag('p', dtrs=[Text("hello world")]))

<div class="example">
  <p>hello world</p>
</div>


"""

import io


class HtmlObject(object):

    """Abstract class."""

    def __str__(self):
        buffer = io.StringIO()
        self.write(buffer)
        return buffer.getvalue()

    
class Text(HtmlObject):

    """Class that implements a text span."""

    def __init__(self, text):
        self.text = text

    def write(self, buffer, indent=''):
        buffer.write(self.text.strip())


class Tag(HtmlObject):

    def __init__(self, tag, nl=True, attrs=None, dtrs=None):
        self.tag = tag
        self.nl = nl
        self.attrs = {}
        self.dtrs = []
        if attrs is not None:
            self.attrs = attrs
        if dtrs is not None:
            if isinstance(dtrs, list):
                self.dtrs = dtrs
            else:
                self.dtrs = [dtrs]

    def is_block(self):
        block_tags = {'div', 'p', 'blockquote', 'ol', 'ul'}
        return self.tag.lower() in block_tags

    def add(self, dtr):
        """Add a daughter, which is either a Tag or Text instance."""
        self.dtrs.append(dtr)
        return dtr

    def add_all(self, dtrs):
        """Add a list of daughters, which are either Tag or Text instances."""
        self.dtrs.extend(dtrs)

    def write(self, buffer, indent=''):
        attrs = self._attribute_string()
        if self.is_block():
               buffer.write("\n")
        if not self.dtrs:
            buffer.write("%s<%s%s/>" % (indent, self.tag, attrs))
        else:
            buffer.write("%s<%s%s>" % (indent, self.tag, attrs))
            for dtr in self.dtrs:
                dtr.write(buffer, indent=indent+'  ')
            if self.is_block():
                buffer.write("\n%s</%s>" % (indent, self.tag))
            else:
                buffer.write("</%s>" % self.tag)
        if self.is_block():
               buffer.write("\n")
#        if self.nl:
#            buffer.write("\n")

    def _attribute_string(self):
        attrs = ''
        if self.attrs:
            pairs = self.attrs.items()
            attrs = ' ' + ' '.join(["%s=\"%s\"" % (k, v) for k, v in pairs])
        return attrs


class Href(Tag):

    def __init__(self, href, content):
        self.tag = 'a'
        self.nl = False
        self.attrs = {'href': href}
        self.dtrs = [Text(content)]


def div(attrs, dtrs):
    return Tag('div', attrs=attrs, dtrs=dtrs)


def button(attrs, dtrs):
    return Tag('button', attrs=attrs, dtrs=dtrs)
