#!/usr/bin/env/python

"""
    figshare2vivo.py -- Read Figshare data, make VIVO RDF
"""

# TODO:  Handle all attributes
# TODO:  Remove legacy code

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
VIVO = Namespace('http://vivoweb.org/ontology/core#')
BIBO = Namespace('http://purl.org/ontology/bibo/')

# Setup logging

logging.basicConfig()

#   Helper functions


def add_external_ids(uri, work):
    if 'external_ids' in work:
        if 'ISNI' in work['external_ids']:
            for isni in work['external_ids']['ISNI']:
                g.add((uri, VIVO.isni, Literal(isni)))
        if 'FundRef' in work['external_ids']:
            for fund_ref in work['external_ids']['FundRef']:
                g.add((uri, VIVO.fundRefId, Literal(fund_ref)))


def add_acronyms(uri, work):
    if 'acronyms' in work:
        for acronym in work['acronyms']:
            g.add((uri, VIVO.abbreviation, Literal(acronym)))


def add_aliases(uri, work):
    if 'aliases' in work:
        for alias in work['aliases']:
            g.add((uri, RDFS.label, Literal(alias)))


def add_established(uri, work):
    if 'established' in work and work['established'] is not None:
        year = str(work['established'])
        date_uri = URIRef(uri_prefix + 'date' + year)
        g.add((uri, VIVO.dateEstablished, date_uri))


def add_type(uri, work):

    type_table = {
        'Facility': None,
        'Company':	VIVO.Company,
        'Government': 	VIVO.GovernmentAgency,
        'Other': None,
        'Healthcare': VIVO.HealthcareOrganization,
        'Nonprofit': VIVO.NonProfitCompany,
        'Education': VIVO.EducationOrganization,
        'Archive': 	VIVO.ArchiveOrganization
    }
    if 'types' in work:
            for grid_type in work['types']:
                vivo_type = type_table.get(grid_type, None)
                if vivo_type is not None:
                    g.add((uri, RDF.type, vivo_type))


def add_relationships(uri, work):
    if 'relationships' in work:
        for relationship in work['relationships']:
            to_uri = URIRef(uri_prefix + relationship['id'])
            relationship_type = relationship['type']
            if relationship_type == 'Affiliated':
                g.add((uri, VIVO.hasAffiliatedOrganization, to_uri))
                g.add((to_uri, VIVO.hasAffiliatedOrganization, uri))  # own inverse
            elif relationship_type == 'Child':
                g.add((uri, VIVO.hasSubOrganization, to_uri))  # sub class of BFO_0000051 (has part)
            elif relationship_type == 'Parent':
                g.add((uri, VIVO.hasSuperOrganization, to_uri))  # sub class of BFO_0000050 (part of)
            else:
                raise KeyError(relationship_type)


def add_vcard(uri, work):

    if 'addresses' not in work or len(work['addresses']) == 0:
        return

    address = work['addresses'][0]
    url_rank = 0

    VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
    vcard_uri = URIRef(str(uri)+'-vcard')
    g.add((vcard_uri, RDF.type, VCARD.organization))
    g.add((uri, VIVO.hasContactInfo, vcard_uri))

    #   Add Address

    vcard_address_uri = URIRef(str(vcard_uri) + '-address')
    g.add((vcard_uri, VCARD.hasAddress, vcard_address_uri))
    if 'city' in address and address['city'] is not None and len(address['city']) > 0:
        g.add((vcard_address_uri, VCARD.locality, Literal(address['city'])))
    if 'postcode' in address and address['postcode'] is not None and len(address['postcode']) > 0:
        g.add((vcard_address_uri, VCARD.postalCode, Literal(address['postcode'])))

    lines = []
    for line in ['line_1', 'line_2', 'line_3']:
        if address[line] is not None and len(address[line]) > 0:
            lines.append(address[line])
    street_address = ';'.join(lines)
    if len(street_address) > 0:
        g.add((vcard_address_uri, VCARD.streetAddress, Literal(street_address)))

    if 'state' in address and address['state'] is not None and len(address['state']) > 0:
        g.add((vcard_address_uri, VCARD.region, Literal(address['state'])))
    if 'country' in address and address['country'] is not None and len(address['country']) > 0:
        g.add((vcard_address_uri, VCARD.country, Literal(address['country'])))

    #   Add geolocation

    if 'lat' in address and address['lat'] is not None and 'lng' in address and address['lng'] is not None:
        vcard_geo_uri = URIRef(str(vcard_uri) + '-geo')
        g.add((vcard_uri, VCARD.hasGeo, vcard_geo_uri))
        g.add((vcard_geo_uri, VCARD.geo, Literal('geo:'+str(address['lat'])+','+str(address['lng']))))

    #   Add Email

    if 'email_address' in work and work['email_address'] is not None:
        vcard_email_uri = URIRef(str(vcard_uri) + '-email')
        g.add((vcard_uri, VCARD.hasEmail, vcard_email_uri))
        g.add((vcard_email_uri, VCARD.email, Literal(work['email_address'])))

    #   Add Wikipedia URL

    if 'wikipedia_url' in work and work['wikipedia_url'] is not None:
        url_rank += 1
        vcard_wikipedia_uri = URIRef(str(vcard_uri) + '-wikipedia')
        g.add((vcard_uri, VCARD.hasURL, vcard_wikipedia_uri))
        g.add((vcard_wikipedia_uri, VCARD.url, URIRef(work['wikipedia_url'].strip())))
        g.add((vcard_wikipedia_uri, VIVO.rank, Literal(str(url_rank), datatype=XSD.integer)))
        g.add((vcard_wikipedia_uri, RDFS.label, Literal('Wikipedia Page')))

    # Add Links

    if 'links' in work:
        for link in work['links']:
            if link is not None and len(link) > 0:
                url_rank += 1
                vcard_link_uri = URIRef(str(vcard_uri) + '-link' + str(url_rank))
                g.add((vcard_uri, VCARD.hasURL, vcard_link_uri))
                g.add((vcard_link_uri, VCARD.url, URIRef(link.strip())))
                g.add((vcard_link_uri, VIVO.rank, Literal(str(url_rank), datatype=XSD.integer)))
                if link == work['links'][0]:
                    link_text = "Home Page"
                else:
                    link_text = "Additional Link"
                g.add((vcard_link_uri, RDFS.label, Literal(link_text)))


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


def make_figshare_rdf(work):
    """
    Given a work in JSON format, from Figshare, add triples to the graph representing the work

    :param work: a dict containing the work's Figshare data
    :return: triples added to global graph
    """
    type_map = [VIVO.Figure, VIVO.Video, VIVO.Dataset, VIVO.Fileset, VIVO.Poster, BIBO.Article, VIVO.Presentation,
                BIBO.Thesis, VIVO.Software]

    uri = URIRef(uri_prefix + str(work['id']))

    g.add((uri, RDF.type, type_map[-1 + work['defined_type']]))  # Python is zero-based, Figshare is not
    g.add((uri, RDFS.label, Literal(work['title'])))
    g.add((uri, BIBO.abstract, Literal(work['description'])))
    g.add((uri, BIBO.doi, Literal(work['doi'])))



work = get_figshare_article('3117808')
print work

g = Graph()
make_figshare_rdf(work)
#
#
#
# #   Make RDF for each work
#
# count = 0
# for work in figshare:
#     count += 1
#     if count % 100 == 0:
#         print count
#     make_figshare_rdf(work)
#
# #   Generate the RDF file
#
triples_file = open('figshare.rdf', 'w')
print >>triples_file, g.serialize(format='nt')
triples_file.close()
