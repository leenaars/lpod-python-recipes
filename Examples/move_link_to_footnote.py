#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ok lpod 1.0
"""
Remove all links from a document, transforming each link information (URL, text)
into a footnote. Of course, removing links already inside notes, just keeping
plain text URL. (Side note: most office suite dislike notes in notes)
"""
import os
import sys

# Import from lpod
from lpod.document import odf_get_document

def get_default_doc():

    default = "collection2.odt"

    # For convenience we use some remote access to the document
    #from urllib2 import urlopen
    #default = urlopen("http://arsaperta.org/collection2.odt")
    return default


def remove_links(element):
    tag = 'text:a'
    keep_inside_tag = 'None'
    context=(tag, keep_inside_tag, False)
    element, is_modified = _tree_remove_tag(element, context)
    return is_modified

def _tree_remove_tag(element, context):
    """Remove tag in the element, recursive.
    - context = (tag to remove, protection tag, protection flag)
    - protection tag protect from change sub elements one sub level depth"""
    buffer = element.clone()
    modified = False
    sub_elements = []
    tag, keep_inside_tag, protected = context
    if keep_inside_tag and element.get_tag() == keep_inside_tag:
        protect_below = True
    else:
        protect_below = False
    for child in buffer.get_children():
        striped, is_modified = _tree_remove_tag(child, (tag, keep_inside_tag, protect_below))
        if is_modified:
            modified = True
        if type(striped) == type([]):
            for item in striped:
                sub_elements.append(item)
        else:
            sub_elements.append(striped)
    if not protected and element.get_tag() == tag:
        element = []
        modified = True
    else:
        if not modified:
            # no change in element sub tree, no change on element
            return (element, False)
        element.clear()
        try:
            for key, value in buffer.get_attributes().iteritems():
                element.set_attribute(key, value)
        except ValueError:
            print "Incorrect attribute in", buffer
    text = buffer.get_text()
    tail = buffer.get_tail()
    if text is not None:
        element.append(text)
    for child in sub_elements:
        element.append(child)
    if tail is not None:
        if type(element) == type([]):
            element.append(tail)
        else:
            element.set_tail(tail)
    return (element, True)

if __name__=="__main__":
    try:
        source = sys.argv[1]
    except IndexError:
        source = get_default_doc()

    document = odf_get_document(source)
    body = document.get_body()

    print "Moving links to footnotes from", source
    print "links occurrences:", len(body.get_links())
    print "footnotes occurences:", len(body.get_notes())

    counter_links_in_notes = 0
    for note in body.get_notes():
        for link in note.get_links():
            counter_links_in_notes += 1
            url = link.get_attribute("xlink:href")
            text = link.get_text(True)
            tail = link.get_tail()
            new_tail = " (link: %s) %s" % (url, tail)
            link.set_tail(new_tail)
            remove_links(note)

    print "links in notes:", counter_links_in_notes

    counter_added_note = 0    # added notes counter
    for paragraph in body.get_paragraphs():
        for link in paragraph.get_links():
            url = link.get_attribute("xlink:href")
            text = link.get_text(True)
            counter_added_note += 1
            paragraph.insert_note(
                after = link,   # citation is inserted after current link
                note_id = "my_note_%s" % counter_added_note,
                citation = u"1",  # The symbol the user sees to follow the footnote.
                body = (          # The footnote itself, at the end of the page.
                        u'. %s, link: %s' %(text, url) )
                )
        remove_links(paragraph)

    print "links occurrences:", len(body.get_links())
    print "footnotes occurences:", len(body.get_notes())

    if not os.path.exists('test_output'):
        os.mkdir('test_output')

    output = os.path.join('test_output', "my_LN_" + source)

    document.save(target=output, pretty=True)
