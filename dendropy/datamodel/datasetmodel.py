#! /usr/bin/env python

##############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2010-2014 Jeet Sukumaran and Mark T. Holder.
##  All rights reserved.
##
##  See "LICENSE.txt" for terms and conditions of usage.
##
##  If you use this work or any portion thereof in published work,
##  please cite it as:
##
##     Sukumaran, J. and M. T. Holder. 2010. DendroPy: a Python library
##     for phylogenetic computing. Bioinformatics 26: 1569-1571.
##
##############################################################################

"""
This module defines the :class:`DataSet`: a top-level data container object
that manages collections of :class:`TaxonNamespace`, :class:`TreeList`, and
(various kinds of) :class:`CharacterMatrix` objects.
"""

import warnings
try:
    from StringIO import StringIO # Python 2 legacy support: StringIO in this module is the one needed (not io)
except ImportError:
    from io import StringIO # Python 3
import copy
import sys
from dendropy.utility import container
from dendropy.utility import error
from dendropy.datamodel import basemodel
from dendropy.datamodel import taxonmodel
from dendropy.datamodel import treemodel
from dendropy import dataio

###############################################################################
## DataSet

class DataSet(
        basemodel.Annotable,
        basemodel.Readable,
        basemodel.Writeable,
        basemodel.DataObject):
    """
    A phylogenetic data object that coordinates collections of
    :class:`TaxonNamespace`, :class:`TreeList`, and (various kinds of)
    :class:`CharacterMatrix` objects.

    A :class:`DataSet` has three attributes:

        `taxon_namespaces`
            A list of :class:`TaxonNamespace` objects, each representing
            a distinct namespace for operational taxononomic unit concept
            definitions.

        `tree_lists`
            A list of :class:`TreeList` objects, each representing a
            collection of :class:`Tree` objects.

        `char_matrices`
            A list of :class:`CharacterMatrix`-derived objects (e.g.
            :class:`DnaCharacterMatrix`).

    Multiple :class:`TaxonNamespace` objects within a :class:`DataSet` are
    allowed so as to support reading/loading of data from external sources that
    have multiple independent taxon namespaces defined within the same source
    or document (e.g., a Mesquite file with multiple taxa blocks, or a NeXML
    file with multiple OTU sections). Ideally, however, this would not
    be how data is managed. Recommended idiomatic usage would be to use a
    :class:`DataSet` to manage multiple types of data that all share and
    reference the same, single taxon namespace.

    Note that unless there is a need to collect and serialize a collection of
    data to the same file or external source, it is probably better
    semantically to use more specific data structures (e.g., a
    :class:`TreeList` object for trees or a :class:`DnaCharacterMatrix`
    object for an alignment). Similarly, when deserializing an external
    data source, if just a single type or collection of data is needed (e.g.,
    the collection of trees from a file that includes both trees and an
    alignment), then it is semantically cleaner to deserialize the data
    into a more specific structure (e.g., a :class:`TreeList` to get all the
    trees). However, when deserializing a mixed external data source
    with, e.g. multiple alignments or trees and one or more alignments, and you
    need to access/use more than a single collection, it is more efficient to
    read the entire data source at once into a :class:`DataSet` object and then
    independently extract the data objects as you need them from the various
    collections.

    """

    ###########################################################################
    ### Lifecycle and Identity

    def __init__(self, *args, **kwargs):
        """
        The constructor can take one argument. This can either be another
        :class:`DataSet` instance or an iterable of :class:`TaxonNamespace`,
        :class:`TreeList`, or :class:`CharacterMatrix`-derived instances.

        In the former case, the newly-constructed :class:`DataSet` will be a
        shallow-copy clone of the argument.

        In the latter case, the newly-constructed :class:`DataSet` will have
        the elements of the iterable added to the respective collections
        (``taxon_namespaces``, ``tree_lists``, or ``char_matrices``, as
        appropriate). This is essentially like calling :meth:`DataSet.add()`
        on each element separately.
        """
        if len(args) > 1:
            # only allow 1 positional argument
            raise error.TooManyArgumentsError(func_name=self.__class__.__name__, max_args=1, args=args)
        if "stream" in kwargs or "schema" in kwargs:
            raise TypeError("Constructing from an external stream is no longer supported: use the factory method 'DataSet.get_from_stream()'")
        elif len(args) == 1 and isinstance(args[0], DataSet):
            self._clone_from(args[0], kwargs)
        else:
            basemodel.DataObject.__init__(self, label=kwargs.pop("label", None))
            self.taxon_namespaces = container.OrderedSet()
            self.tree_lists = container.OrderedSet()
            self.char_matrices = container.OrderedSet()
            self.comments = []
            if len(args) == 1 and not isinstance(args[0], DataSet):
                for item in args[0]:
                    self.add(item)
        if kwargs:
            raise TypeError("Unrecognized or unsupported arguments: {}".format(kwargs))

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def _clone_from(self, dataset, kwargs_dict):
        raise NotImplementedError

    def __copy__(self):
        raise NotImplementedError

    def taxon_namespace_scoped_copy(self, memo=None):
        raise NotImplementedError

    def __deepcopy__(self, memo=None):
        raise NotImplementedError

    def add_tree_list(self, tree_list):
        if tree_list.taxon_namespace not in self.taxon_namespaces:
            self.taxon_namespaces.add(tree_list.taxon_namespace)
        self.tree_lists.add(tree_list)

