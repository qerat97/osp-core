from abc import ABC, abstractmethod
import rdflib
import logging

logger = logging.getLogger(__name__)


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, namespace, name, iri_suffix):
        """Initialise the ontology entity

        :param namespace: The namespace of the entity
        :type namespace: OntologyNamespace
        :param name: The name of the entity
        :type name: str
        """
        self._name = name
        self._iri_suffix = iri_suffix
        self._namespace = namespace

    def __str__(self):
        return "%s.%s" % (self.namespace._name, self._name)

    def __repr__(self):
        return "<%s %s.%s>" % (
            self.__class__.__name__,
            self._namespace._name,
            self._name
        )

    def __eq__(self, other):
        return isinstance(other, OntologyEntity) and self.iri == other.iri

    @property
    def name(self):
        """Get the name of the entity"""
        return self._name

    @property
    def iri(self):
        """Get the IRI of the Entity"""
        return rdflib.URIRef(self._namespace.get_iri() + self._iri_suffix)

    @property
    def tblname(self):
        return "%s___%s" % (self.namespace._name, self._iri_suffix)

    @property
    def namespace(self):
        """Get the name of the entity"""
        return self._namespace

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: List[OntologyEntity]
        """
        return set(self._direct_superclasses())

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._direct_subclasses())

    @property
    def subclasses(self):
        """Get the subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._subclasses())

    @property
    def superclasses(self):
        """Get the superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._superclasses())

    @property
    def description(self):
        """Get the description of the entity

        :return: The description of the entity
        :rtype: str
        """
        desc = self.namespace._graph.value(
            self.iri, rdflib.RDFS.isDefinedBy, None)
        if desc is None:
            return "To Be Determined"
        return str(desc)

    def get_triples(self):
        """ Get the triples of the entity """
        return self.namespace._graph.triples((self.iri, None, None))

    def is_superclass_of(self, other):
        return self in other.superclasses

    def is_subclass_of(self, other):
        return self in other.subclasses

    @abstractmethod
    def _direct_superclasses(self):
        pass

    @abstractmethod
    def _direct_subclasses(self):
        pass

    @abstractmethod
    def _superclasses(self):
        pass

    @abstractmethod
    def _subclasses(self):
        pass

    def _transitive_hull(self, predicate_iri, inverse=False, blacklist=()):
        """Get all the entities connected with the given predicate.

        Args:
            predicate_iri (URIRef): The IRI of the predicate
            inverse (bool, optional): Use the inverse instead.
                Defaults to False.
            blacklist (collection): A collection of IRIs not to return.

        Yields:
            OntologyEntity: The connected entities
        """
        visited = {self.iri}
        frontier = {self.iri}
        while frontier:
            current = frontier.pop()
            yield from self._directly_connected(predicate_iri=predicate_iri,
                                                inverse=inverse,
                                                blacklist=blacklist,
                                                _frontier=frontier,
                                                _visited=visited,
                                                _iri=current)

    def _special_cases(self, triple):
        """Some supclass statements are often omitted in the ontology.
        Replace these with safer triple patterns.

        Args:
            triple (Tuple[rdflib.term]): A triple pattern to possibly replace.

        Returns:
            triple (Tuple[rdflib.term]): Possibly replaced triple.
        """
        if triple == (None, rdflib.RDFS.subClassOf, rdflib.OWL.Thing):
            return (None, rdflib.RDF.type, rdflib.OWL.Class)
        if triple == (rdflib.OWL.Nothing, rdflib.RDFS.subClassOf, None):
            return (None, rdflib.RDF.type, rdflib.OWL.Class)

        if triple == (None, rdflib.RDFS.subPropertyOf,
                      rdflib.OWL.topObjectProperty):
            return (None, rdflib.RDF.type, rdflib.OWL.ObjectProperty)
        if triple == (rdflib.OWL.bottomObjectProperty,
                      rdflib.RDFS.subPropertyOf, None):
            return (None, rdflib.RDF.type, rdflib.OWL.ObjectProperty)

        if triple == (None, rdflib.RDFS.subPropertyOf,
                      rdflib.OWL.topDataProperty):
            return (None, rdflib.RDF.type, rdflib.OWL.DataProperty)
        if triple == (rdflib.OWL.bottomDataProperty,
                      rdflib.RDFS.subPropertyOf, None):
            return (None, rdflib.RDF.type, rdflib.OWL.DataProperty)
        return triple

    def _directly_connected(self, predicate_iri, inverse=False, blacklist=(),
                            _frontier=None, _visited=None, _iri=None):
        """Get all the entities directly connected with the given predicate.

        Args:
            predicate_iri (URIRef): The IRI of the predicate
            inverse (bool, optional): Use the inverse instead.
                Defaults to False.
            blacklist (collection): A collection of IRIs not to return.
            Others: Helper for _transitive_hull method.

        Yields:
            OntologyEntity: The connected entities
        """
        triple = (_iri or self.iri, predicate_iri, None)
        if inverse:
            triple = (None, predicate_iri, _iri or self.iri)

        if predicate_iri in [rdflib.RDFS.subClassOf,
                             rdflib.RDFS.subPropertyOf]:
            triple = self._special_cases(triple)
        for x in self.namespace._graph.triples(triple):
            o = x[0 if triple[0] is None else 2]
            if _visited and o in _visited:
                continue
            if not isinstance(o, rdflib.BNode):
                if _visited is not None:
                    _visited.add(o)
                if _frontier is not None:
                    _frontier.add(o)
                if o not in blacklist:
                    yield self.namespace._namespace_registry.from_iri(o)

    def __hash__(self):
        return hash(self.iri)
