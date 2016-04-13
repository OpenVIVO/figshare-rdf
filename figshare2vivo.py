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
__version__ = "0.02"

#   Constants

uri_prefix = 'http://openvivo.org/a/doi'
date_prefix = 'http://openvivo.org/a/date'
author_prefix = 'http://openvivo.org/a/orcid'
vcard_prefix = 'http://openvivo.org/a/vcard'

VIVO = Namespace('http://vivoweb.org/ontology/core#')
BIBO = Namespace('http://purl.org/ontology/bibo/')
OBO = Namespace('http://purl.obolibrary.org/obo/')
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

# Setup logging

logging.basicConfig()

#   Helper functions


def add_authors(uri, work):
    # TODO: If no orcid for the author, add the author as a vcard (see openVIVO for examples)
    g = Graph()
    if 'authors' in work:
        rank = 0
        for author in work['authors']:
            rank += 1
            authorship_uri = URIRef(str(uri) + '-authorship' + str(rank))
            if 'orcid_id' in author and len(author['orcid_id']) > 0:
                author_uri = URIRef(author_prefix + author['orcid_id'])

            else:

                #   Make a vcard for the author.  The vcard has the name of the author

                name_parts = [x.strip('.') for x in author['full_name'].split(' ')]
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

                author_uri = URIRef(vcard_prefix + author['family_name'] + '--' + author['given_name'] + '-' +
                                    author['additional_name'] + '-')
                g.add((author_uri, RDF.type, VCARD.Individual))
                name_uri = URIRef(str(author_uri) + 'name')
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
    g.add((uri, OBO.ARG_2000058, vcard_uri))

    #   Add Figshare URL

    url_rank = 1
    vcard_figshare_uri = URIRef(str(vcard_uri) + '-figshare')
    g.add((vcard_figshare_uri, RDF.type, VCARD.URL))
    g.add((vcard_uri, VCARD.hasURL, vcard_figshare_uri))
    g.add((vcard_figshare_uri, VCARD.url, URIRef(work['figshare_url'].strip())))
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
    article_result = requests.get('https://api.figshare.com/v2/articles/{}'.format(article_id)).content
    article_result = json.loads(article_result)
    return article_result


def get_figshare_articles_by_tag(tag):
    """
    Given a figshare tag, return a JSON object containing the articles matching the tag
    :param tag: articles with the specified tag will be returned
    :return: JSON object containing Figshare metadata
    """
    import urllib2
    url = 'https://api.figshare.com/v2/articles/search'
    data = '{ "search_for": "{}" }'.replace('{}', tag)
    req = urllib2.Request(url, data)
    rsp = urllib2.urlopen(req)
    article_results = json.loads(rsp.read())

    # #   Remove articles that do not contain the specified tag
    #
    # for article_result in article_results:
    #     delete = True
    #     if 'tags' in article_result:
    #         for tag_value in work['tags']:
    #             if tag_value == tag:
    #                 delete = False
    #     if delete:
    #         article_results.remove(article_result)
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

    return g


#   Main starts here
if __name__ == '__main__':
    figshare_graph = Graph()
    triples_file = open('figshare.rdf', 'w')
    works_2016 = get_figshare_articles_by_tag('force2016')
    print len(works_2016), "works identified by force2016 tag"

    works_16 = get_figshare_articles_by_tag('force16')
    print len(works_16), "works identified by force16 tag"

    works_collection = get_figshare_articles('131')  # 36 is VIVO, 131 is Force16
    print len(works_collection), "works identified by collection"
    #
    # work = get_figshare_article('3117808')  # Krafft and Conlon Duraspace Summit presentation
    # print 'Recent work by Krafft and Conlon\n', work
    # make_figshare_rdf(work)

    #  Make RDF for each work

    count = 0
    added = 0
    for figshare_work in works_2016 + works_16 + works_collection:
        count += 1
        if count % 10 == 0:
            print count
        article = get_figshare_article(str(figshare_work['id']))
        if 'force2016' in [x.lower() for x in article['tags']] or 'force16' in [x.lower() for x in article['tags']]:
            print '\n', article['title']
            print article
            return_graph = make_figshare_rdf(article)
            if return_graph is not None:
                figshare_graph += return_graph
                added += 1

    print added, "works with DOI added"
    print >>triples_file, figshare_graph.serialize(format='n3')
    triples_file.close()
