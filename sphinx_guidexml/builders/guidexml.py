# -*- coding: utf-8 -*-
"""
    sphinx.builders.guidexml
    ~~~~~~~~~~~~~~~~~~~~

    Gentoo's GuideXML Sphinx builder.

    :copyright: Copyright 2011- by the Gentoo Foundation.
    :license: BSD, see LICENSE for details.
    :codeauthor: Jesus Rivero <neurogeek@gentoo.org>
"""

import shutil
from datetime import datetime
import os
from docutils.io import StringOutput
from sphinx.builders import Builder
from sphinx.writers.guidexml import GuideXmlWriter

SEP = os.path.sep 
GuideXMLHeader = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE guide SYSTEM "http://www.gentoo.org/dtd/guide.dtd">
<!-- $Header$ -->
"""

class GuideXML(Builder):
    """Sphinx builder for generating Gentoo's GuideXML 
       documents"""

    #Required by Sphinx
    name = 'guidexml'
    format = 'xml'
    out_suffix = '.xml'

    def get_outdated_docs(self):
        """Returns 'all_documents' to force the 
           building of all the documents"""

        return 'all documents'

    def prepare_writing(self, docnames):
        """Sphinx Builder's prepare_writing"""

        self.writer = GuideXmlWriter(self)

    def get_target_uri(self, docname, typ=None):
        """Sphinx Builder's get_target_uri"""
        
        return ''

    def write_doc(self, docname, doctree):
        """Sphinx Builder's write_doc"""
        destination = StringOutput(encoding='utf-8')
        self.writer.write(doctree, destination)

    def find_section_output(self, docname):
        """Finds a Document in the doc Dict and return
           its contents"""

        for doc in self.writer.get_output():
            if doc["DOC"].endswith(".".join([docname, 'rst'])):
                return doc["CONTENTS"]

    def finish(self):
        """Sphinx Builder's finish
           Here we should have the whole parsed document.
           What gets done here is prepare the GuideXML doc and
           write it to the provided location"""

        #Let's copy the statics
        for path in self.config.html_static_path:

            if os.path.exists(SEP.join([self.outdir, path])):
                shutil.rmtree(SEP.join([self.outdir, path]))

            shutil.copytree(SEP.join([self.srcdir, path]), 
                SEP.join([self.outdir, path]))

        with open(SEP.join([self.outdir, "guidexml.xml"]), "w") as fd:
            #Let's build the first part of the document
            fd.write(GuideXMLHeader)
            #-----
            
            #Then we will need the <guide> tag
            fd.write("<guide>\n")
            #-----
            
            #Then the title. We can get it from the conf.py (html_title) prop.
            if self.config.html_title:
                glb_title = self.config.html_title
                fd.write("\t<title>%s</title>\n" % glb_title)
            else:
                raise AttributeError("Can't find html_title in conf.py")
            #-----

            #At this point, we are missing author and abstract. 
            fd.write("\t<license />\n")
            fd.write("\t<version>%s</version>\n" % self.config.version)
            fd.write("\t<date>%s</date>\n" % datetime.now().strftime("%Y-%m-%d"))

            index = self.config.master_doc
            toctree = self.env.tocs[index]

            try:
                toc = [toc for toc in toctree.traverse() 
                    if toc.tagname == 'toctree'][0]

                doc_order = toc.attributes['entries']

                for name, doc in doc_order:
                    fd.write("\t<chapter>\n\t\t<title>%s</title>\n" % name)
                    sects = self.find_section_output(doc)

                    for sect in sects:
                        fd.write(sect.get_output())

                    fd.write("\t</chapter>\n")

            except IndexError:
                raise Exception("Could not find Index")

            #Now, we close the guide
            fd.write("</guide>\n")
            fd.close()
