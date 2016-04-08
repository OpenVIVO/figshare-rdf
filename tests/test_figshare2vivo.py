"""
Tests for figshare2vivo
"""

import os
from unittest import TestCase
import vcr

from rdflib import URIRef, Literal

from figshare2vivo import make_figshare_rdf, get_figshare_article, uri_prefix
#namespace
from figshare2vivo import RDF, RDFS, BIBO, VIVO

# Directory where test data is stored.
TEST_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__))
)

my_vcr = vcr.VCR(
    cassette_library_dir=os.path.join(TEST_PATH, 'fixtures'),
)


class TestMappings(TestCase):
    work = '3117808'
    doi = '10.6084/m9.figshare.3117808.v2'

    @my_vcr.use_cassette()
    def test_get_article(self):
        meta = get_figshare_article(self.work)
        self.assertTrue(meta['citation'].startswith('Krafft, Dean; Conlon, Michael'))
        self.assertEqual(meta['doi'], self.doi)
        self.assertEqual(
            meta['description'],
            'Status of the VIVO Project -- research projects, sites, on-going c ollaborations'
        )

    @my_vcr.use_cassette()
    def test_make_figshare_rdf(self):
        meta = get_figshare_article(self.work)
        g = make_figshare_rdf(meta)

        #print g.serialize(format='turtle')

        created_uri = [u for u in g.subjects(RDF.type, BIBO.Slideshow)][0]

        # uri
        self.assertEqual(
            URIRef(uri_prefix + self.work),
            created_uri
        )

        # title
        self.assertEqual(
            g.value(created_uri, RDFS.label),
            Literal('VIVO Status -- Duraspace Summit March 16, 2016')
        )

        # date
        self.assertEqual(
            g.value(created_uri, VIVO.publishedDate),
            URIRef('http://openvivo.org/a/date2016-03-17')
        )

        # doi
        created_doi = g.value(created_uri, BIBO.doi)
        self.assertEqual(
            created_doi,
            Literal(self.doi)
        )




        #assert 1 == 2