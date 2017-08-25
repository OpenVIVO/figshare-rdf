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
__copyright__ = "Copyright 2017 (c) Michael Conlon"
__license__ = "Apache License 2.0"
__version__ = "0.03"

#   Constants

uri_prefix = 'http://openvivo.org/a/doi'
date_prefix = 'http://openvivo.org/a/date'
author_prefix = 'http://openvivo.org/a/orcid'
vcard_prefix = 'http://openvivo.org/a/vcard'
orcid_prefix = 'http://orcid.org/'
event_uri = URIRef('http://openvivo.org/a/eventVIVO2017')

VIVO = Namespace('http://vivoweb.org/ontology/core#')
BIBO = Namespace('http://purl.org/ontology/bibo/')
OBO = Namespace('http://purl.obolibrary.org/obo/')
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
OWL = Namespace('http://www.w3.org/2002/07/owl#')

# Setup logging

logging.basicConfig()

#   Helper functions


def add_authors(uri, work):
    g = Graph()
    if 'authors' in work:
        rank = 0
        for author in work['authors']:
            rank += 1
            authorship_uri = URIRef(str(uri) + '-authorship' + str(rank))

            name_parts = [xn.strip('.') for xn in author['full_name'].split(' ')]
            if len(name_parts) == 1:
                author['family_name'] = name_parts[0]
                author['given_name'] = ''
                author['additional_name'] = ''
            elif len(name_parts) == 2:
                author['given_name'] = name_parts[0]
                author['additional_name'] = ''
                author['family_name'] = name_parts[1]
            elif len(name_parts) == 3:
                author['given_name'] = name_parts[0]
                author['additional_name'] = name_parts[1]
                author['family_name'] = name_parts[2]
            else:
                author['given_name'] = name_parts[0]
                author['additional_name'] = name_parts[1]
                author['family_name'] = name_parts[2:]

            author['full_name'] = author['family_name'] + ', ' + author['given_name'] + ' ' + author['additional_name']
            author['full_name'] = author['full_name'].strip()

            if 'orcid_id' in author and len(author['orcid_id']) > 0:
                author_uri = URIRef(author_prefix + author['orcid_id'])
                g.add((author_uri, RDF.type, FOAF.Person))
                orcid_uri = URIRef(orcid_prefix + author['orcid_id'])
                g.add((orcid_uri, RDF.type, OWL.Thing))
                g.add((author_uri, VIVO.orcidId, orcid_uri))
                g.add((author_uri, RDFS.label, Literal(author['full_name'])))

            else:

                #   Make a vcard for the author.  The vcard has the name of the author

                author_text = vcard_prefix + author['family_name'] + '--' + author['given_name'] + '-' + \
                                    author['additional_name'] + '-'
                author_uri = URIRef(author_text)
                g.add((author_uri, RDF.type, VCARD.Individual))
                name_uri = URIRef(author_text + 'name')
                g.add((name_uri, RDF.type, VCARD.Name))
                g.add((author_uri, VCARD.hasName, name_uri))
                if len(author['given_name']) > 0:
                    g.add((name_uri, VCARD.givenName, Literal(author['given_name'])))
                if len(author['family_name']) > 0:
                    g.add((name_uri, VCARD.familyName, Literal(author['family_name'])))
                if len(author['additional_name']) > 0:
                    g.add((name_uri, VCARD.additionalName, Literal(author['additional_name'])))

            # create an authorship linking the work to the author (or vcard)

            g.add((authorship_uri, RDF.type, VIVO.Authorship))
            g.add((authorship_uri, VIVO.rank, Literal(str(rank), datatype=XSD.integer)))
            g.add((authorship_uri, VIVO.relates, author_uri))
            g.add((authorship_uri, VIVO.relates, uri))

    return g


def add_vcard(uri, work):
    g = Graph()
    if 'figshare_url' not in work or len(work['figshare_url']) == 0:
        return

    vcard_uri = URIRef(str(uri)+'-vcard')
    g.add((vcard_uri, RDF.type, VCARD.Kind))  # check this
    g.add((uri, OBO.ARG_2000028, vcard_uri))
    g.add((vcard_uri, OBO.ARG_2000029, uri))

    #   Add Figshare URL

    url_rank = 1
    vcard_figshare_uri = URIRef(str(vcard_uri) + '-figshare')
    g.add((vcard_figshare_uri, RDF.type, VCARD.URL))
    g.add((vcard_uri, VCARD.hasURL, vcard_figshare_uri))
    g.add((vcard_figshare_uri, VCARD.url, Literal(work['figshare_url'].strip(), datatype=XSD.anyURI)))
    g.add((vcard_figshare_uri, VIVO.rank, Literal(str(url_rank), datatype=XSD.integer)))
    g.add((vcard_figshare_uri, RDFS.label, Literal('Figshare Page')))
    return g


def get_figshare_article(article_id):
    """
    Given a figshare article id, return a JSON object containing the article metadata
    :param article_id:
    :return: JSON object containing Figshare metadata
    """
    import requests
    import re
    version = re.compile('v[0-9]*')
    article_result = requests.get('https://api.figshare.com/v2/articles/{}'.format(article_id)).content
    article_result = json.loads(article_result)

    #   Figshare uses versioned DOI.  VIVO is only interested in the most recent version.
    #   If Figshare returns a versioned DOI, chop off the version

    if 'doi' in article_result and len(article_result['doi']) > 0:
        doi = article_result['doi']
        p = re.search(version, doi)
        if p is not None:
            doi = doi.replace('.' + p.group(), '')
            article_result['doi'] = doi
    return article_result


def get_figshare_articles_by_tag(tag):
    """
    Given a figshare tag, return a JSON object containing the articles matching the tag
    :param tag: articles with the specified tag will be returned
    :return: JSON object containing Figshare metadata
    """
    import urllib2
    url = 'https://api.figshare.com/v2/articles/search'
    data = '{ "search_for": "{}", "page_size": 1000}'.replace('{}', tag)
    req = urllib2.Request(url, data)
    rsp = urllib2.urlopen(req)
    article_results = json.loads(rsp.read())
    return article_results


def get_figshare_articles_by_orcid_id(orcid_id):
    """
    Given an orcid identifier, return a JSON object containing the article metadata for articles by the
    author with that orcid identifier
    :param orcid_id: orcid_id
    :return: JSON object containing Figshare metadata
    """
    import urllib2
    url = 'https://api.figshare.com/v2/articles/search'
    data = '{ "search_for": "{}", "page_size": 1000}'.replace('{}', orcid_id)
    req = urllib2.Request(url, data)
    rsp = urllib2.urlopen(req)
    article_results = json.loads(rsp.read())
    return article_results


def get_figshare_articles_by_institution(institution_id):
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
    g = Graph()

    type_map = [VIVO.Image, BIBO.AudioVisualDocument, VIVO.Dataset, BIBO.Collection, VIVO.ConferencePoster,
                VIVO.ConferencePaper, BIBO.Slideshow, BIBO.Thesis, OBO.ERO_0000071]

    if 'doi' in work and len(work['doi']) > 0:
        uri = URIRef(uri_prefix + str(work['doi']))
    else:
        return  # No DOI => no entry in OpenVIVO

    if 'defined_type' in work:
        try:
            g.add((uri, RDF.type, type_map[-1 + work['defined_type']]))  # Python is zero-based, Figshare is not
        except IndexError:
            g.add((uri, RDF.type, BIBO.InformationResource))  # If unknown, just add the parent type

    if 'title' in work:
        g.add((uri, RDFS.label, Literal(work['title'].replace('/', ''))))

    if 'description' in work:
        g.add((uri, BIBO.abstract, Literal(work['description'])))

    if 'doi' in work:
        g.add((uri, BIBO.doi, Literal(work['doi'])))

    if 'tags' in work:
        for tag in work['tags']:
            g.add((uri, BIBO.freetextKeyword, Literal(tag)))

    if 'published_date' in work:
        date_uri = URIRef(date_prefix + work['published_date'][0:10])
        g.add((uri, VIVO.datePublished, date_uri))
        g.add((uri, VIVO.dateTimeValue, date_uri))

    if 'created_date' in work:
        date_uri = URIRef(date_prefix + work['created_date'][0:10])
        g.add((uri, VIVO.dateCreated, date_uri))

    if 'modified_date' in work:
        date_uri = URIRef(date_prefix + work['modified_date'][0:10])
        g.add((uri, VIVO.dateModified, date_uri))

    g += add_authors(uri, work)  # add an authorship for each author with an orcid
    g += add_vcard(uri, work)  # adds the figshare URL

    #    Link work to event

    g.add((uri, OBO.RO_0002353, event_uri))
    g.add((event_uri, OBO.RO_0002234, uri))

    return g


#   Main starts here
if __name__ == '__main__':
    figshare_graph = Graph()
    triples_file = open('figshare.rdf', 'w')

    # orcid_id = '0000-0002-1304-8447'  # Conlon's orcid
    # works_by_orcid = get_figshare_articles_by_orcid_id(orcid_id)
    # print works_by_orcid
    # print len(works_by_orcid), "works identified for orcid identifier", orcid_id
    # count = 0
    # added = 0
    # for figshare_work in works_by_orcid:
    #     count += 1
    #     if count % 10 == 0:
    #         print count
    #     article = get_figshare_article(str(figshare_work['id']))
    #     return_graph = make_figshare_rdf(article)
    #     if return_graph is not None:
    #         figshare_graph += return_graph
    #         added += 1

    works_2017 = get_figshare_articles_by_tag('vivo2017')
    print len(works_2017), "works identified by vivo2017 tag"

    works_h2017 = get_figshare_articles_by_tag('#vivo2017')
    print len(works_h2017), "works identified by #vivo2017 tag"

    works_17 = get_figshare_articles_by_tag('vivo17')
    print len(works_17), "works identified by vivo17 tag"

    works_h17 = get_figshare_articles_by_tag('#vivo17')
    print len(works_h17), "works identified by #vivo17 tag"

    # works_collection = get_figshare_articles('131')  # 36 is VIVO, 131 is Force17
    # print works_collection
    # print len(works_collection), "works identified by collection"
    #
    # work = get_figshare_article('3117808')  # Krafft and Conlon Duraspace Summit presentation
    # print 'Recent work by Krafft and Conlon\n', work
    # make_figshare_rdf(work)

    #  Make RDF for each work
    doi_set = set()
    count = 0
    for figshare_work in works_2017 + works_17 + works_h2017 + works_h17:
        count += 1
        if count % 10 == 0:
            print count
        article = get_figshare_article(str(figshare_work['id']))
        if 'vivo2017' in [x.lower() for x in article['tags']] \
                or 'vivo17' in [x.lower() for x in article['tags']]\
                or '#vivo2017' in [x.lower() for x in article['tags']]\
                or '#vivo17' in [x.lower() for x in article['tags']]:
            return_graph = make_figshare_rdf(article)
            doi_set.add(article['doi'])
            if return_graph is not None:
                figshare_graph += return_graph

    print len(doi_set), "works with unique DOI added"
    print >>triples_file, figshare_graph.serialize(format='n3')
    triples_file.close()
