#!/usr/bin/env/python

"""
    figshare2vivo.py -- Read Figshare data, make VIVO RDF

    Perhaps this is a "sufficient" draft -- including the features needed for OpenVIVO.

    Links to Figshare output formats could be provided
    Links to the Figshare files (rather than the web page) could be provided

"""

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDFS, RDF, XSD
import json
import logging

__author__ = "Michael Conlon"
__copyright__ = "Copyright 2016 (c) Michael Conlon"
__license__ = "Apache License 2.0"
__version__ = "0.01"

#   Constants

uri_prefix = 'http://openvivo.org/a/figshare'
date_prefix = 'http://openvivo.org/a/date'
author_prefix = 'http://openvivo.org/a/person'

VIVO = Namespace('http://vivoweb.org/ontology/core#')
BIBO = Namespace('http://purl.org/ontology/bibo/')

# Setup logging

logging.basicConfig()

#   Helper functions


def add_authors(uri, work):
    if 'authors' in work:
        rank = 0
        for author in work['authors']:
            rank += 1
            print "Author",author
            if 'orcid_id' in author and len(author['orcid_id']) > 0:
                author_uri = URIRef(author_prefix + author['orcid_id'])
                authorship_uri = URIRef(str(uri) + '-authorship' + str(rank))
                g.add((authorship_uri, RDF.type, VIVO.Authorship))
                g.add((authorship_uri, VIVO.rank, Literal(str(rank), datatype=XSD.integer)))
                g.add((authorship_uri, VIVO.relates, author_uri))
                g.add((authorship_uri, VIVO.relates, uri))


def add_vcard(uri, work):

    if 'figshare_url' not in work or len(work['figshare_url']) == 0:
        return

    VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
    vcard_uri = URIRef(str(uri)+'-vcard')
    g.add((vcard_uri, RDF.type, VCARD.organization))  # check this
    g.add((uri, VIVO.hasContactInfo, vcard_uri))

    #   Add Figshare URL

    url_rank = 1
    vcard_figshare_uri = URIRef(str(vcard_uri) + '-figshare')
    g.add((vcard_uri, VCARD.hasURL, vcard_figshare_uri))
    g.add((vcard_figshare_uri, VCARD.url, URIRef(work['figshare_url'].strip())))
    g.add((vcard_figshare_uri, VIVO.rank, Literal(str(url_rank), datatype=XSD.integer)))
    g.add((vcard_figshare_uri, RDFS.label, Literal('Figshare Page')))


def get_figshare_article(article_id):
    """
    Given a figshare article id, return a JSON object containing the article metadata
    :param article_id:
    :return: JSON object containing Figshare metadata
    """
    import requests
    article_result = requests.get('https://api.figshare.com/v2/articles/{}'.format(article_id)).content
    article_result = json.loads(article_result)
    return article_result


def get_figshare_articles_by_tag(tag):
    """
    Given a figshare article id, return a JSON object containing the article metadata
    :param tag: articles with the specified tag will be returned
    :return: JSON object containing Figshare metadata
    """
    import requests
    article_results = requests.get('https://api.figshare.com/v2/articles?search_for={}'.format(tag)).content
    article_results = json.loads(article_results)

    #   Remove articles that do not contain the specified tag

    for article_result in article_results:
        delete = True
        if 'tags' in article_result:
            for tag_value in work['tags']:
                if tag_value == tag:
                    delete = False
        if delete:
            article_results.remove(article_result)
    return article_results


def get_figshare_articles(institution_id):
    """
    Given a figshare institution id, return a JSON object containing the article metadata for articles with
    that institution id
    :param institution_id: institution id
    :return: JSON object containing Figshare metadata
    """
    import requests
    article_results = requests.get(
        'https://api.figshare.com/v2/articles?institution={}&page_size=1000'.format(institution_id)).content
    article_results = json.loads(article_results)
    return article_results


def make_figshare_rdf(work):
    """
    Given a work in JSON format, from Figshare, add triples to the graph representing the work

    :param work: a dict containing the work's Figshare data
    :return: triples added to global graph
    """
    type_map = [VIVO.Figure, VIVO.Video, VIVO.Dataset, VIVO.Fileset, VIVO.Poster, BIBO.Article, VIVO.Presentation,
                BIBO.Thesis, VIVO.Software]

    uri = URIRef(uri_prefix + str(work['id']))

    if 'defined_type' in work:
        try:
            g.add((uri, RDF.type, type_map[-1 + work['defined_type']]))  # Python is zero-based, Figshare is not
        except IndexError:
            g.add((uri, RDF.type, BIBO.InformationResource))  # If unknown, just add the parent type

    if 'title' in work:
        g.add((uri, RDFS.label, Literal(work['title'])))

    if 'description' in work:
        g.add((uri, BIBO.abstract, Literal(work['description'])))

    if 'doi' in work:
        g.add((uri, BIBO.doi, Literal(work['doi'])))

    if 'tags' in work:
        for tag in work['tags']:
            g.add((uri, BIBO.freetextKeyword, Literal(tag)))

    if 'published_date' in work:
        date_uri = URIRef(date_prefix + work['published_date'][0:10])
        g.add((uri, VIVO.publishedDate, date_uri))

    if 'created_date' in work:
        date_uri = URIRef(date_prefix + work['created_date'][0:10])
        g.add((uri, VIVO.createdDate, date_uri))

    if 'modified_date' in work:
        date_uri = URIRef(date_prefix + work['modified_date'][0:10])
        g.add((uri, VIVO.modifiedDate, date_uri))

    add_authors(uri, work)  # add an authorship for each author with an orcid
    add_vcard(uri, work)  # adds the figshare URL


#   Main starts here

g = Graph()

# works = get_figshare_articles_by_tag('force2016')
# print 'FORCE16 works\n', works

works = get_figshare_articles('36')  # 36 is VIVO, 131 is Force16
print 'VIVO 2016 works\n', works
#
# work = get_figshare_article('3117808')  # Krafft and Conlon Duraspace Summit presentation
# print 'Recent work by Krafft and Conlon\n', work
# make_figshare_rdf(work)

#  Make RDF for each work

count = 0
for work in works:
    count += 1
    if count % 10 == 0:
        print count
    article = get_figshare_article(str(work['id']))
    make_figshare_rdf(article)

#  Generate the RDF file

triples_file = open('figshare.rdf', 'w')
print >>triples_file, g.serialize(format='nt')
triples_file.close()
