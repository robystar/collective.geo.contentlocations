from zope.interface import Interface

from collective.geo.contentlocations import ContentLocationsMessageFactory as _
from zope import schema


class IContentlocationsLayer(Interface):
    """A layer specific to my product
    """


class IGeoManager(Interface):
    """ Interface for shape management
    """

    wkt = schema.Text(
        title=_(u"Shape in WKT format"),
        description=_(u"Insert below the shape coordinates in WKT format."),
        required=False
    )
    

    filecsv = schema.Bytes(
        title=_(u"File"),
        description=_(u"A GPS track (boh ci aggingiamo qualcosaltro) file holding a coordinate per row and enough "
                      u"coordinate pairs for selected type."),
        required=False)

    def isGeoreferenceable(self):
        """Check if an object is isGeoreferenceable
        """

    def getCoordinates(self):
        """Return the coordinates  assigned to an object
        """

    def setCoordinates(self):
        """set coordinates to an object
        """


class IGeoMarker(Interface):
    pass


class IGeoMarkerUtility(Interface):
    pass
