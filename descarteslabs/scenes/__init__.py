"""
The Scenes submodule provides a higher-level, object-based
interface that makes most interactions with the Descartes Labs platform easier.

* :doc:`Collection <docs/collection>`: convenience methods for mapping and filtering
* :doc:`geocontext <docs/geocontext>`: consistent spatial parameters to use when loading a raster
* :doc:`Scene <docs/scene>`: metadata about a single scene
* :doc:`SceneCollection <docs/scenecollection>`: conveniently work with Scenes in aggregate
* :doc:`search <docs/search>`: search for Scenes
* :doc:`display <docs/display>`: display ndarrays with matplotlib

It's available under ``dl.scenes``.

Example
=======

.. include:: init_example.rst
"""

from .geocontext import AOI, DLTile, XYZTile, GeoContext
from ._display import display
from ._search import search
from .scene import Scene
from .collection import Collection
from .scenecollection import SceneCollection

__all__ = ["Scene", "SceneCollection", "Collection", "AOI", "DLTile", "XYZTile", "GeoContext", "search", "display"]
