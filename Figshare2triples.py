#!/usr/bin/env/python

from rdflib import  Graph, Literal, BNode, Namespace, RDF, URIRef, plugin
from rdflib.serializer import Serializer
from rdflib.namespace import RDF, FOAF, RDFS, DC
from rdflib.plugins.sparql import prepareQuery

import json

import requests
from requests.exceptions import HTTPError
import lxml.etree
import lxml.html

__author__ = "Simon Porter"
__copyright__ = "Copyright 2016 (c) Simon Porter"
__license__ = "Apache License 2.0"
__version__ = "0.01"


def get_triples(article_id):
    """
        convert article into triples
        """
    articleResult = requests.get('https://api.figshare.com/v2/articles/{}'.format(article_id)).content
    articleResult = json.loads(articleResult)
    g = Graph()
    sub_art = URIRef(articleResult['figshare_url'])
    sub_artns = Namespace('{}/'.format(articleResult["figshare_url"]))
    core = Namespace('http://vivoweb.org/ontology/core#')
    bibo = Namespace('http://purl.org/ontology/bibo/')
    skos = Namespace('http://www.w3.org/2004/02/skos/core#')
    g.add((sub_art,RDF.type,typeMappings[str(articleResult["defined_type"])]))
    g.add((sub_art,RDFS.label,Literal(articleResult['title'])))
    g.add((sub_art,bibo.abstract,Literal(articleResult['description'])))
    if 'doi' in articleResult.keys():
        g.add((sub_art,bibo.doi,Literal(articleResult['doi'])))
    if 'tags' in articleResult.keys():
        for tag in articleResult["tags"]:
            g.add((sub_art,bibo.freetextKeyword,Literal(tag)))
    g.add((sub_art,core.dateTime,sub_artns.createdDate))
    g.add((sub_artns.createdDate,RDF.type,core.DateTimeValue))
    g.add((sub_artns.createdDate,URIRef('http://www.w3.org/2001/XMLSchema#dateTime'),Literal(articleResult['created_date'])))
    if 'authors' in articleResult.keys():
        for i, author in enumerate(articleResult['authors']):
            authorship = URIRef('{0}/authorship{1}'.format(sub_art,author['id']))
            rank = i + 1
            g.add((sub_art,core.relatedBy,authorship))
            g.add((authorship,RDF.type,core.Authorship))
            g.add((authorship,core.rank,Literal(rank)))
            g.add((authorship,RDF.type,core.Relationship))
            authuri = URIRef('https://figshare.com/authors/{}/{}'.format(author['url_name'],author['id']))
            g.add((authorship,core.relates,authuri))
            g.add((authorship,core.relates,sub_art))
            g.add((authuri,RDFS.label,Literal(author['full_name'])))
            g.add((authuri,RDF.type,FOAF.Person))
            if len(author['url_name']) > 1:
                try:
                    authpage = requests.get('https://figshare.com/authors/{}/{}'.format(author['url_name'],author['id']))
                    app_data = lxml.html.fromstring(authpage.content).xpath('//script[@id="app-data"]/text()')
                    app_data = json.loads(app_data[0])
                    g.add((authuri,core.orcid,Literal(app_data["user"]["orcid"])))
                except:
                    pass
    #Categories
    for cat in articleResult['categories']:
        categoryURI = URIRef('https://figshare.com/categories/{}/{}'.format(cat['title'].replace(' ','_'),cat['id'])
                             g.add((sub_art,core.hasSubjectArea,categoryURI))
                             g.add((categoryURI,RDF.type,skos.Concept))
                             #OAI-ORE triples
                             ore = Namespace('http://www.openarchives.org/ore/terms/')
                             g.add((sub_art,RDF.type,ore.Aggregation))
                             g.add((sub_art,ore.describes,sub_art))
                             g.add((sub_art,DC.created,Literal(articleResult['created_date'])))
                             g.add((sub_art,DC.modified,Literal(articleResult['modified_date'])))
                             metadataCitations = 'https://figshare.com/articles/{}/{}/citations/'.format(article_id,articleResult['version'])
                             preformedMetadata = ['refworks',
                                                  'bibtex',
                                                  'reference_manager',
                                                  'mendeley',
                                                  'endnote',
                                                  'datacite',
                                                  'nlm',
                                                  'dc']
                             for mformat in preformedMetadata:
                             g.add((sub_art,ore.isDescribedBy,URIRef(metadataCitations + mformat)))
                             
                             for f in articleResult['files']:
                             file_uri = URIRef('https://ndownloader.figshare.com/files/{}'.format(f['id']))
                             g.add((sub_art,ore.aggregates,file_uri))
                             g.add((file_uri,ore.aggregatedBy,sub_art))
                             g.add((file_uri,DC.title,Literal(f['name'])))
                             
                             #get additional triples from files
                             fmappings = [('.rdf','xml'),
                                          ('.nt','nt'),
                                          ('.n3','n3'),
                                          ('.ttl','turtle'),
                                          ('.jsonld','json-ld')]
                             for f in articleResult['files']:
                             try:
                             for fmap in fmappings:
                             if f['name'].endswith(fmap[0]):
                             g.parse(location='https://ndownloader.figshare.com/files/{}'.format(f['id']), format=fmap[1])
                             except:
                             pass
                             return g


