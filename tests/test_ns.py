from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parent.parent
NS = Namespace("https://omeka-s-contrib.github.io/omeka-s-ref/ns#")
ONTOLOGY = URIRef("https://omeka-s-contrib.github.io/omeka-s-ref/ns")
VANN = Namespace("http://purl.org/vocab/vann/")


def load():
    return Graph().parse(ROOT / "ns.ttl", format="turtle")


def test_ontology_describes_the_namespace():
    g = load()
    assert (ONTOLOGY, RDF.type, OWL.Ontology) in g
    for p in (DCTERMS.title, DCTERMS.description, DCTERMS.license, OWL.versionInfo):
        assert g.value(ONTOLOGY, p) is not None, p
    assert g.value(ONTOLOGY, VANN.preferredNamespacePrefix) == Literal("o-ref")
    assert str(g.value(ONTOLOGY, VANN.preferredNamespaceUri)) == str(NS)


def test_terms_are_the_two_properties():
    g = load()
    terms = {s for s in g.subjects(RDF.type, RDF.Property) if str(s).startswith(str(NS))}
    assert terms == {NS.id, NS.ref}
    for term in terms:
        assert g.value(term, RDFS.label) is not None
        assert g.value(term, RDFS.comment) is not None
        assert g.value(term, RDFS.isDefinedBy) == ONTOLOGY
        assert g.value(term, RDFS.domain) is None
        assert g.value(term, RDFS.range) is None
