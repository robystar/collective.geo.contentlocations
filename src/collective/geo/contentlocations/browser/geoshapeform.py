import csv
import cStringIO

from zope.interface import implements

from z3c.form import form, field, button

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone.utils import getToolByName

from plone.z3cform.layout import wrap_form
from plone.z3cform.fieldsets import extensible, group

from collective.geo.mapwidget.interfaces import IMapView
from collective.geo.mapwidget.browser.widget import MapWidget
from collective.geo.mapwidget.maplayers import MapLayer

from collective.geo.settings.interfaces import IGeoCustomFeatureStyle

from collective.z3cform.mapwidget.widget import MapFieldWidget

from .. import ContentLocationsMessageFactory as _
from .geostylesform import GeoStylesForm
from ..interfaces import IGeoManager


class CsvGroup(group.Group):
    fields = field.Fields(IGeoManager).select('filecsv')
    label = _(u"GPS Track")
    description = _(u"Import data from GPS file")


class GeoShapeForm(extensible.ExtensibleForm, form.Form):
    implements(IMapView)

    form_name = "edit_geometry"
    id = 'coordinates-form'
    description = _(u"Specify the geometry for this content")
    fields = field.Fields(IGeoManager).select('wkt')
    fields['wkt'].widgetFactory = MapFieldWidget
    mapfields = ['geoshapemap']

    groups = (GeoStylesForm, CsvGroup,)

    message_ok = _(u'Changes saved.')
    message_cancel = _(u'No changes made.')
    message_georeference_removed = _(u'Coordinates removed')
    message_coordinates_null = _(
        u"No coordinate has been set. Please, set "
        u"coordinates on the map or fill the WKT field.")

    message_error_wkt = _(u'WKT expression not correct. Verify input.')
    message_error_input = _(u'No valid input given.')
    message_error_csv = _(u'CSV File not correct. Verify file format.')

    myheaders = ('date','time','latitude_raw','longitude_raw','depth',);


    def __init__(self, context, request):
        super(GeoShapeForm, self).__init__(context, request)
        self.geomanager = IGeoManager(self.context)

        portal_url = getToolByName(self.context, 'portal_url')
        portal = portal_url.getPortalObject()
        props_tool = getToolByName(portal, 'portal_properties')
        site_props = getattr(props_tool, 'site_properties')
        self.typesUseViewActionInListings = list(
            site_props.getProperty('typesUseViewActionInListings')
        )

    def set(self, key, val):
        return self.context.__setitem__(key, val)

    @property
    def next_url(self):
        #Need to send the user to the view url for certain content types.
        url = self.context.absolute_url()
        if self.context.portal_type in self.typesUseViewActionInListings:
            url += '/view'

        return url

    def redirectAction(self):
        self.request.response.redirect(self.next_url)

    def setStatusMessage(self, message, level='info'):
        ptool = getToolByName(self.context, 'plone_utils')
        ptool.addPortalMessage(message, level)

    @button.buttonAndHandler(_(u'Save'))
    def handleApply(self, action):  # pylint: disable=W0613
        data, errors = self.extractData()
        if (errors):
            return



        csv_group = [gr for gr in self.groups if gr.__class__.__name__ == 'CsvGroup']
        filecsv = csv_group[0].widgets['filecsv'].value




        # set content geo style
        geostylesgroup = [
            gr for gr in self.groups
            if gr.__class__.__name__ == 'GeoStylesForm'
        ]
        if geostylesgroup:
            stylemanager = IGeoCustomFeatureStyle(self.context)
            fields = geostylesgroup[0].fields
            stylemanager.setStyles([(i, data[i]) for i in fields])

        







        #with open("/tmp/pippo.csv","w") as myfile:
            #myfile.write(data['filecsv'])

        

        # we remove coordinates if wkt is 'empty'
        message = self.message_ok
        if False:
            geo = IGeoManager(self.context)
            coord = geo.getCoordinates()
            if coord == (None, None):
                self.setStatusMessage(self.message_coordinates_null, 'warning')
            else:
                message = self.message_georeference_removed
                self.geomanager.removeCoordinates()

        else:
            ok, message = self.addCoordinates(filecsv)
            if not ok:
                self.status = message
                return

        self.setStatusMessage(message)
        self.redirectAction()

    @button.buttonAndHandler(_(u'Cancel'))
    def handleCancel(self, action):  # pylint: disable=W0613
        self.setStatusMessage(self.message_cancel)
        self.redirectAction()

    @button.buttonAndHandler(
        _(u'Remove georeference'), name='remove-georeference')
    def handleRemoveGeoreference(self, action):
        self.geomanager.removeCoordinates()
        self.setStatusMessage(self.message_georeference_removed)
        self.redirectAction()

    def addCoordinates(self, filecsv):
        import pdb
        data = []
        coord = []
        if filecsv:
            filecsv.seek(0)
            content = filecsv.read()
            reader = csv.DictReader(cStringIO.StringIO(str(content)), delimiter=';')
           
            for row in reader:
                if row['longitude_raw'] and row['latitude_raw']:
                    coord = []
                    coord.append(self.parseCoord(row['longitude_raw'].replace(",", ".")))    
                    coord.append(self.parseCoord(row['latitude_raw'].replace(",", "."))) 
                    try:
                        coord.append(float(row['depth'].replace(",", "."))) 
                    except:
                        coord.append(0) 
                    coord.append('2013-11-05T' + row['time'].replace(".", ":") + 'Z')
                    data.append(coord)

                # for col in self.myheaders
                #     if()
                # if not headers:
                #     headers = row
                # else:
                #     #data.append([row[i] for i in range(len(headers)) if headers[i] in self.myheaders])
                #     data.append(row)

            # # check for row existence ???
            # # are there any problems if the row is empty ???
            #     if row:
            #         # verify pairs of values are there
            #         #import pdb; pdb.set_trace()
            #         pdb.set_trace()
            #         try:
            #             longitude = row[10]
            #             latitude = row[11]
            #         except:
            #             #return False, self.message_error_csv

     
            #         # verify that longitude and latitude are non-empty and non-zero
            #         if longitude != '' and latitude != '':
            #             try:
            #                 # check for float convertible values
            #                 coords.append((longitude, latitude))
            #             except:
            #                 #return False, self.message_error_csv


            
            self.geomanager.setCoordinates('Track', data)
            #import pdb;pdb.set_trace()


            return True, self.message_ok
        #else:
            #return False, self.message_error_csv


    def verifyWkt(self, data):
        try:
            from shapely import wkt
            geom = wkt.loads(data)
            #geom = {"type":"Point","coordinates":"00000000"}
        except ImportError:
            from pygeoif.geometry import from_wkt
            geom = from_wkt(data)
        return geom

    def parseCoord(self, data):

        v = data.split('.')
        l = len(v[0])        
        d = float(v[0][0:l-2])
        m = float(data[l-2:l])/60
        s = float('0.' + v[1])/60

        return d+m+s


manageCoordinates = wrap_form(
    GeoShapeForm,
    label=_(u'Coordinates'),
    description=_(u"Modify geographical data for this content")
)
