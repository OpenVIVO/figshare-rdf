# Figshare Harvester for OpenVIVO

Figshare (http://www.figshare.com) is a popular commercial repository for archiving scientific 
work such as presentations, data, pre-prints and more.  Works in Figshare can be assigned Document Object 
Identifiers (DOI) that are indexed by CrossRef (http://crossref.org).  People in Figshare can identify 
themselves via an ORCiD identifier (http://orcid.org). Figshare provides a public API 
(https://github.com/figshare/user_documentation/blob/master/APIv2/index.md) that can be used to 
harvest metadata from Figshare.  The combination of identified people, identified works, and a public API, 
makes Figshare an ideal repository for open science.

## Harvesting by tag

The harvester supports harvesting by tag.  Given a tag, the harvester gathers all the content from Figshare with the specified tag,
producing RDF for each work.  The Harvester uses openVIVO URI conventions for dates and people.  Only identified works and identified
people are included in the RDF.

## Harvesting by ORCiD identifier

Same as above.  Given an ORCiD identifier, the harvester finds all content in Figshare for the author, producing RDF for each work.
The Harvester uses OpenVIVO URI conventions for dates and people.  Only identified works are included in the RDF.

*Note:  The figshare2vivo was developed for a demonstration of OpenVIVO at Force2016 (http://force206.org). 
figshare2vivo will also be used for the 2016 VIVO conference (http://vivoconference.org), Aug 17-19 in Denver.*

## Figshare Version Numbers

Figshare issues new DOI for each version of each item stored in Figshare.  VIVO is only interested in the most
current version of a work, not its previous versions.  figshare2vivo removes figshare version numbers from DOI and
retrieves and processes only the most recent version of each item stored in figshare.

## Development

To assist with development,

1. Clone the repository
1. Install requirements in `requirements.txt`
1. Run tests with `python -m unittest discover`

