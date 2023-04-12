import csv
from lxml import etree

XCRI_NS = 'http://xcri.org/profiles/1.2/catalog'
XCRI_TERMS_NS = 'http://xcri.org/profiles/1.2/catalog/terms'
XCRI_TERMS = '{' + XCRI_TERMS_NS + '}'
XCRI_TERMS_PREFIX = 'xcriTerms'

LSIP_NS = 'https://www.businessldn.co.uk/schemas/lsip'
LSIP_PREFIX = 'lsip'
LSIP = '{' + LSIP_NS + '}'

MLO_NS = 'http://purl.org/net/mlo'
MLO_PREFIX = 'mlo'
MLO = '{' + MLO_NS + '}'

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
XSI = '{' + XSI_NS + '}'

DC_NS = 'http://purl.org/dc/elements/1.1/'
DC = '{' + DC_NS + '}'
DC_PREFIX = 'dc'
DCTERMS_NS  = 'http://purl.org/dc/terms/'
DCTERMS = '{' + DCTERMS_NS + '}'
DCTERMS_PREFIX = 'dcterms'

# Vpcab identifiers
SOC2020 = 'lsip:SOC2020'
SSA2 = 'lsip:SSA2'
UKPRN_TYPE = 'lsip:UKPRN'
LAR_TYPE = 'lsip:LAR'
NVQ_TYPE = 'lsip:NVQ-equivalent'

SCHEMA_LOCATIONS = "http://xcri.org/profiles/1.2/catalog ../schemas/lsip_xcri_profile.xsd " \
        "http://xcri.org/profiles/1.2/catalog/terms ../schemas/xcri_cap_terms_1_2.xsd " \
        "http://purl.org/net/mlo ../schemas/lsip_mlo_profile.xsd " \
        "http://purl.org/dc/elements/1.1/ ../schemas/dc.xsd " \
        "https://www.businessldn.co.uk/schemas/lsip ../schemas/lsip_extensions.xsd " \
        "http://purl.org/dc/terms/ ../schemas/dcterms.xsd"


class Element:
    def __init__(self):
        self.mappings = {'example': 'test'}
        self.required = []
        self.element_name = self.__class__.__name__.lower()
        self.xsi_type = None

    def map_attributes(self, obj):
        for k, v in self.mappings.items():
            if v in obj and obj[v] is not None and obj[v] != '':
                self.__setattr__(k, obj[v])

    def has_identifier(self, obj, collection):
        if 'identifier' in obj.__dict__:
            for item in collection:
                if 'identifier' in item.__dict__:
                    if item.__getattribute__('identifier') == obj.__getattribute__('identifier'):
                        return True
        return False

    def is_valid(self):
        for item in self.required:
            if item not in self.__dict__:
                return False
        return True

    def to_xml(self, parent_element):
        element: etree.Element = etree.SubElement(parent_element, self.element_name)
        if self.xsi_type:
            element.set(XSI+'type', self.xsi_type)
        for attr in self.__dict__:
            if attr not in ['mappings', 'required', 'xsi_type', 'element_name']:
                if issubclass(type(self.__getattribute__(attr)), Element):
                    self.__getattribute__(attr).to_xml(element)
                elif attr == 'text':
                    element.text = self.__getattribute__(attr)
                elif type(self.__getattribute__(attr)) == list:
                    for item in self.__getattribute__(attr):
                        item.to_xml(element)
                elif type(self.__getattribute__(attr)) == ExtendedElement:
                    self.__getattribute__(attr).to_xml(element)
                elif attr == 'type':
                    elem = etree.SubElement(element, DC+'type')
                    elem.text = self.__getattribute__(attr)
                else:
                    elem = etree.SubElement(element, attr)
                    elem.text = str(self.__getattribute__(attr))
        return element


class ExtendedElement(Element):
    def __init__(self, type, value, name=DC + 'identifier'):
        super().__init__()
        self.type = type
        self.value = value
        self.element_name = name

    def to_xml(self, parent):
        element = etree.SubElement(parent, self.element_name)
        element.set(XSI+'type', self.type)
        element.text = str(self.value)
        return element


class Provider(Element):
    def __init__(self, obj):
        super().__init__()
        self.mappings = {
            DC+'identifier': 'Provider.identifier',
            DC+'title': 'Provider.name'
        }
        self.required = [DC+'identifier']
        self.map_attributes(obj)
        self.__setattr__(DC +'identifier', ExtendedElement(UKPRN_TYPE, self.__getattribute__(DC + 'identifier')))


class Presentation(Element):
    def __init__(self, obj):
        super().__init__()
        self.mappings = {
            DC+'identifier': 'Presentation.identifier',
            MLO+'start': "Presentation.start",
            'studyMode': "Presentation.studyMode",
            'attendanceMode': "Presentation.attendanceMode",
            'attendancePattern': "Presentation.attendancePattern",
            MLO + 'places': 'Places'
        }
        self.map_attributes(obj)
        self.cost = Cost(obj)
        self.venue = Venue(obj)
        self.mappings = {
            LSIP+'flexibleStartDate': "Presentation.flexibleStartDate",
            LSIP + 'placesTaken': 'Enrolments'
        }
        self.map_attributes(obj)


class Cost(Element):
    def __init__(self, obj):
        super().__init__()
        self.element_name = MLO+"cost"
        self.mappings = {
            LSIP+"price": 'Presentation.cost',
            LSIP+'priceCurrency': "Presentation.costCurrency",
            DC+"description": "Presentation.costDescription"
        }
        self.required=[LSIP+"amount"]
        self.map_attributes(obj)


class Course(Element):
    def __init__(self, obj):
        super().__init__()
        self.subjectArea = []
        self.subjectArea.append(SubjectArea(obj))
        self.mappings = {
            DC+'identifier': 'Course.identifier',
            DC+'title': 'Course.name',
            MLO+'prerequisite': 'Course.entryRequirements',
            MLO+'url': 'Course.url'
        }
        self.required = [DC+'identifier']
        self.map_attributes(obj)
        self.qualification = Qualification(obj)
        self.presentation = Presentation(obj)

    def update(self, obj):
        subject = SubjectArea(obj)
        if subject.is_valid() and not self.has_identifier(subject, self.subjectArea):
            self.subjectArea.append(SubjectArea(obj))
        self.qualification.update(obj)


class CareerOutcome(Element):
    def __init__(self, obj):
        super().__init__()
        self.element_name = XCRI_TERMS + 'careerOutcome'
        #self.xsi_type = XCRI_TERMS_PREFIX + ':careerOutcome'
        self.mappings = {
            DC+'identifier': 'Qualification.occupation.code',
            DC+'description': 'Qualification.occupation.description'
        }
        self.required = [DC+'identifier']
        self.map_attributes(obj)

        self.__setattr__(DC +'identifier', ExtendedElement(SOC2020, self.__getattribute__(DC + 'identifier')))


class SubjectArea(Element):
    def __init__(self, obj):
        super().__init__()
        self.element_name = DC + 'subject'
        self.mappings = {
            DC+'identifier': 'Course.subject.code',
            DC+'description': 'Course.subject.description'
        }
        self.required = ['identifier']
        self.map_attributes(obj)
        self.__setattr__(DC +'identifier', ExtendedElement(SSA2, self.__getattribute__(DC + 'identifier')))


class Venue(Element):
    def __init__(self, obj):
        super().__init__()
        self.provider = ProviderVenue(obj)


class ProviderVenue(Element):
    def __init__(self, obj):
        super().__init__()
        self.element_name = 'provider'
        self.mappings = {
            DC + 'identifier': 'Provider.identifier',
            DC + 'title': 'Location.name'
        }
        self.map_attributes(obj)
        self.__setattr__(DC +'identifier', ExtendedElement(UKPRN_TYPE, self.__getattribute__(DC + 'identifier')))
        self.location = Location(obj)


class Location(Element):
    def __init__(self, obj):
        super().__init__()
        self.element_name = MLO + 'location'
        self.mappings = {
            MLO + 'street': 'Location.address1',
            MLO + 'town': 'Location.town',
            MLO + 'postcode': 'Location.postcode',
            MLO + 'address': 'Location.address2',
            MLO + 'email': 'Location.email',
            MLO + 'phone': 'Location.phone'
        }
        self.map_attributes(obj)


class Qualification(Element):
    def __init__(self, obj):
        super().__init__()
        self.element_name = MLO + 'qualification'
        self.mappings = {
            DC+'identifier': 'Qualification.identifier',
            DC+'title': 'Qualification.name',
            MLO+'level': 'Qualification.educationalLevel',
        }
        self.required = [DC+'identifier', DC+'title']
        self.map_attributes(obj)
        self.__setattr__(DC+'identifier', ExtendedElement(LAR_TYPE, self.__getattribute__(DC + 'identifier')))
        self.__setattr__(MLO+'level', ExtendedElement(NVQ_TYPE, self.__getattribute__(MLO + 'level'), name=MLO+'level'))
        self.career_outcome = []
        career_outcome = CareerOutcome(obj)
        if career_outcome.is_valid():
            self.career_outcome.append(career_outcome)

    def update(self, obj):
        career_outcome = CareerOutcome(obj)
        if career_outcome.is_valid() and not self.has_identifier(career_outcome, self.career_outcome):
            self.career_outcome.append(CareerOutcome(obj))


class Xcri:
    def __init__(self, courses=None):
        self.provider = None
        if courses is None:
            self.courses = []
        else:
            self.courses = []
            for row in courses:
                self.populate(row)

    def get_course(self, course_to_find):
        for course in self.courses:
            if course.__getattribute__(DC+'title') == course_to_find.__getattribute__(DC+'title'):
                return course
        return None

    def populate(self, row):
        if not self.provider:
            self.provider = Provider(row)
        course = Course(row)
        # if we have this course already, fill rather than append
        if self.get_course(course):
            self.get_course(course).update(row)
        else:
            self.courses.append(Course(row))

    def load(self, csv_file):
        with open(csv_file) as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.populate(row)

    def to_xml(self):
        NSMAP = {
            None: XCRI_NS,
            DC_PREFIX: DC_NS,
            DCTERMS_PREFIX: DCTERMS_NS,
            'xsi': XSI_NS,
            XCRI_TERMS_PREFIX: XCRI_TERMS_NS,
            LSIP_PREFIX: LSIP_NS,
            MLO_PREFIX: MLO_NS
        }
        catalog = etree.Element("catalog", nsmap=NSMAP)
        catalog.set('generated', '2013-12-21T17:45:00Z')
        catalog.set(XSI + 'schemaLocation', SCHEMA_LOCATIONS)
        provider_element = self.provider.to_xml(catalog)
        for course in self.courses:
            course.to_xml(provider_element)
        return catalog
