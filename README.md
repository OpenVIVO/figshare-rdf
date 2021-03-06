# Figshare Harvester for OpenVIVO

Figshare (http://www.figshare.com) is a popular commercial repository for archiving scientific 
work -- presentations, data, pre-prints and more.  Works in Figshare can be assigned Document Object Identifiers (DOI) that are
indexed by CrossRef (http://crossref.org).  People in Figshare can identify themselves via an ORCiD identifier (http://orcid.org).
figshare provides a public API (https://github.com/figshare/user_documentation/blob/master/APIv2/index.md) that can be used to 
harvest metadata from Figshare.  The combination of identified people, identified works, and a public API, makes Figshare an ideal 
repository for open science.

## Harvesting by tag

The harvester supports harvesting by tag.  Given a tag, the harvester gathers all the content from Figshare with the specified tag,
producing RDF for each work.  The Harvester uses openVIVO URI conventions for dates and people.  Only identified works and identified
people are included in the RDF.

## Harvesting by ORCiD identifier

Same as above.  Given an ORCiD identifier, the harvester finds all content in Figshare for the author, producing RDF for each work.
The Harvester uses OpenVIVO URI conventions for dates and people.  Only identified works are included in the RDF.

*Note:  The Figshare Harvester for OpenVIVO was developed for a demonstration of OpenVIVO at 
Force2016 (http://force2016.org). It was then used for the 2016 VIVO Conference http://vivoconference.org/vivo2016*

## Development

* Clone the repository
* Install requirements in `requirements.txt`
* Run tests with `python -m unittest discover`

