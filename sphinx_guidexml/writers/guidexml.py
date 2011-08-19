# -*- coding: utf-8 -*-
"""
    sphinx.writers.guidexml
    ~~~~~~~~~~~~~~~~~~~

    docutils writers handling Sphinx' custom nodes.

    :copyright: Copyright 2011- by the Gentoo Foundation.
    :license: BSD, see LICENSE for details.
"""

import re
from docutils import nodes
from docutils.writers import Writer

def replace_function(*args, **kwargs):
    """Returns a proper replacement function.
       This is needed to map some DOM elements 
       to GuideXML elements"""

    def replace(m):
        elem = "%s" % args[0]
        if m.groups()[0] == "</":
            return "</" + elem 
        return "<" + elem
    return replace


GuideXmlReMapping = {
    "paragraph" : (re.compile(r'(.{1,2})(paragraph)>\s'), 
        replace_function("p>")),
    "image" : (re.compile(r'(.)(image)'), 
        replace_function("figure")),
    "desc_addname" : (re.compile(r'(.{1,2}desc_addname>)\s'), ''),
    "desc_name" : (re.compile(r'(.{1,2}desc_name>)\s'), ''),
    "desc_parameter" : (re.compile(r'(.{1,2}desc_parameter>)\s'), ''),
    "tgroup" : (re.compile(r'(.{1,2}tgroup.*>)\s'), ''),
    "thead" : (re.compile(r'(.{1,2}thead.*>)\s'), ''),
    "strong" : (re.compile(r'(.{1,2})(strong)>\s'), 
        replace_function("b>")),
    "emphasis" : (re.compile(r'(.{1,2})(emphasis)>\s'), 
        replace_function("e>")),
    "row" : (re.compile(r'(.{1,2})(row)>\s'), 
        replace_function("tr>")),
    "entry" : (re.compile(r'(.{1,2})(entry)>\s'), 
        replace_function("ti>")),
}

GuideXmlDftMappings = {
    "rubric" : "b",
    "literal_block" : "pre",
    "paragraph" : "p",
    "subtitle" : "h2",
    "bullet_list" : "ul",
    "enumerated_list" : "ol",
    "list_item" : "li",
}

re_phase = re.compile(r'^(visit|depart)_(.*)$')

class GuideXmlWriter(Writer):

    output = None

    def __init__(self, builder):
        Writer.__init__(self)
        self.builder = builder

    def translate(self):
        visitor = GuideXmlTranslator(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.output

    def get_output(self):
        return self.output

class GuideXmlSection():
    
    def __init__(self, node, parent):
        self.title = ""
        self.node = node
        self.parent = parent
        self.children = []
        self.blocks = []

    def get_node(self):
        return self.node

    def set_title(self, title):
        self.title = title

    def __str__(self):
        return "<Section %s..." % self.title

    def __repr__(self):
        return u"<Section %s..." % self.title

    def get_output(self):
        
        sect = "<section><title>%s</title>"
        block = "".join([sect % self.title,
                         "<body>",
                         "".join(self.blocks),
                         "</body>",
                         "</section>"])

        for ch in self.children:
            block += ch.get_output()
        return block

    def append_child(self, child):
        self.children.append(child)

    def append_block(self, block):
        self.blocks.append(block)

class GuideXmlTable(object):
    def __init__(self):
        self.rows = []
        self.c_row = None
    
    def get_output(self):
        contents = "<table>"
        for r in self.rows:
            contents += "<tr>%s</tr>" % ("".join(r)) 
        contents += "</table>"
        return contents
            
    def add_row(self):
        self.rows.append([])

    def add_entry(self, entry, is_head=False):
        if is_head:
            entry = "<th>" + entry + "</th>"
        else:
            entry = "<ti>" + entry + "</ti>"
            
        try:
            self.rows[-1].append(entry)
        except:
            self.rows[-1] = []
            self.rows[-1].append(entry)

class GuideXmlTranslator(nodes.NodeVisitor):

    output = []
    block = None
    current = None
    section = None


    def default_action_open(self, node):
        """Function to handle unhandled visit_* and
           depart_* functions. We just do nothing"""

        attr = GuideXmlDftMappings[node.__class__.__name__]
        self.section.append_block("".join(["<", attr, ">"]))

    def default_action_close(self, node):
        """Function to handle unhandled visit_* and
           depart_* functions. We just do nothing"""

        attr = GuideXmlDftMappings[node.__class__.__name__]
        self.section.append_block("".join(["</", attr, ">"]))

    def void_action(self, node):
        pass
        
    def __getattr__(self, attr):

        #This should always work in this env
        phase, attr = re_phase.match(attr).groups()

        if attr in GuideXmlDftMappings.keys():
            if phase == u"depart":
                return self.default_action_close
            else:
                return self.default_action_open
        else:
            return self.void_action

    def visit_section(self, node):
        section = GuideXmlSection(node, parent=self.section)

        if self.section == None:
            self.section = section
        else:
            self.section.append_child(section)

        self.section = section

    def depart_section(self, node):
        if self.section.parent is None:
            #No parents, We add it to Contents
            self.current["CONTENTS"].append(self.section)
        else:
            section = self.section
            self.section = section.parent

    def visit_document(self, node):
        self.current = {"DOC" : node.attributes["source"], "CONTENTS" : []}

    def depart_document(self, node):
        self.output.append(self.current)

    def visit_image(self, node):

        node.attributes['link'] =  \
            node.attributes['uri']

        rgx, repl = GuideXmlReMapping["image"]
        figure = rgx.sub(repl, node.asdom().toprettyxml())

        self.section.append_block(figure)

    def visit_note(self, node):

        rgx, repl = GuideXmlReMapping["paragraph"]
        note = rgx.sub(repl, node.asdom().toprettyxml())
        self.section.append_block(note)

        raise nodes.SkipNode

    def visit_comment(self, node):
        raise nodes.SkipNode

    def visit_Text(self, node):

        text = node.asdom().toprettyxml()

        if not self.section:
            raise nodes.SkipNode

        if node.parent and \
           node.parent.tagname == "title":
               self.section.set_title(text)

        self.section.append_block(text)

    def visit_desc(self, node):
        if node.attributes['desctype'] == u'function':
            self.block = [] 
        else:
            raise nodes.SkipNode

    def visit_desc_name(self, node):

        p_node = node.parent.next_node()

        rgx, repl = GuideXmlReMapping["desc_addname"]
        pkg = rgx.sub(repl, p_node.asdom().toprettyxml())

        rgx, repl = GuideXmlReMapping["desc_name"]
        name = rgx.sub(repl, node.asdom().toprettyxml())


        pkg, name = (pkg.strip(), name.strip())
        self.block += ["<pre caption='", pkg, name, "'>", pkg, name]

    def visit_desc_parameterlist(self, node):
        self.block.append("(")

    def visit_desc_parameter(self, node):
        rgx, repl = GuideXmlReMapping["desc_parameter"]
        param = rgx.sub(repl, node.asdom().toprettyxml())

        self.block.append(param.strip())
        self.block.append(", ")

    def depart_desc_parameterlist(self, node):
        self.block.pop()
        self.block.append(")")

    def depart_desc(self, node):
        self.block.append("</pre>")
        self.section.append_block("".join(self.block))
        self.block = None

    def visit_desc_content(self, node):
        #TODO: CleanUp
        self.block.append("<p>")
        self.block.append(node.astext().replace("<", "&lt;").replace(">", "&gt;"))
        self.block.append("</p>")

        raise nodes.SkipNode

    def visit_table(self, node):
        #TODO: CleanUp
        entry = None
        header = False
        tableob = GuideXmlTable()

        for sn in node.traverse():
            if sn.tagname == "thead":
                header = True
            elif sn.tagname == "tbody":
                if entry is not None:
                    tableob.add_entry(entry, header)
                    entry = None
                header = False
            elif sn.tagname == "row":
                if entry is not None:
                    tableob.add_entry(entry, header)
                    entry = None
                tableob.add_row()
            elif sn.tagname == "entry":
                if sn.astext() == "":
                    entry = ""
                if entry is not None:
                    tableob.add_entry(entry, header)
                    entry = None
            elif sn.tagname == "#text":
                if not entry:
                    entry = ""
                if sn.parent.tagname == "paragraph":
                    entry += sn.astext()
                elif sn.parent.tagname == "strong":
                    entry += "<b>" + sn.astext() + "</b>"
                elif sn.parent.tagname == "emphasis":
                    entry += "<e>" + sn.astext() + "</e>"
        if entry:
            #Last cell
            tableob.add_entry(entry)
        self.section.append_block(tableob.get_output())
        raise nodes.SkipNode

