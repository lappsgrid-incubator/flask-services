"""service.py

Code to run a LAPPS service.

For notes on how to get the client using zeep:
https://python-zeep.readthedocs.io/en/master/transport.html#http-authentication

Some notes:

- The URL is the URL for the WSDL file, not the URL for the invoker. If you use
  the invoker URL in the service data from the ServiceManager (which is in the
  endpointUrl attribute) then you willl get an error.

- The invoker is listed in the WSDL document under <wsdlsoap:address> in the
  <wsdl:service> tag.

To send a request to a service you either can use getMetadata() or execute(),
for the latter you give a string like

{
    "discriminator": "http://vocab.lappsgrid.org/ns/media/text", 
    "payload": "The door is open."
}

If you use LIF you need to make it complete in that you want to add explicit
metadata and views properties, without them you will get errors:

{
    "discriminator": "http://vocab.lappsgrid.org/ns/media/jsonld#lif", 
    "payload": {
        "@context": "http://vocab.lappsgrid.org/context-1.0.0.jsonld",
        "metadata": {},
        "text": {
            "@value": "The door is open."
        },
        "views": []
    }
}

Update: it seems like you can go without the views, but not the metadata.

"""

import os
import sys
import io
import json
import urllib
import requests
import zeep
import operator

import lif_examples

from utils import info, debug
from config import BRANDEIS_USER, BRANDEIS_PASSWORD
from config import VASSAR_USER, VASSAR_PASSWORD


# set to True if yu want to save the output of each step in a chain
SAVE_STEPS = False

# set to True in order to use the output example as the output of the LAPPS
# processing, useful while debugging when you have no internet connection
BYPASS_CHAIN_PROCEESING = False


BRANDEIS = 'brandeis'
VASSAR = 'vassar'

BRANDEIS_SERVICES = 'https://api.lappsgrid.org/services/brandeis'
VASSAR_SERVICES = 'https://api.lappsgrid.org/services/vassar'

WSDL_PATH_BRANDEIS = 'http://eldrad.cs-i.brandeis.edu:8080/service_manager/wsdl/'
WSDL_PATH_VASSAR = 'http://vassar.lappsgrid.org/wsdl/'


# Local directories that store cashed information of services, including the
# meta data retrieved from services and the services list from the Brandeis and
# Vassar APIs.
SERVICE_METADATA = 'data/services/metadata'
BRANDEIS_SERVICES_INFO = 'data/services/info/brandeis.json'
VASSAR_SERVICES_INFO = 'data/services/info/vassar.json'


class LappsServices(object):

    """Class to load all LAPPS services. Services are stored in the services
    instance variable as LappsService objects.

    Instance variables:
       services       list of all services
       services_idx   services indexed on serviceId
       categories     services grouped on output types

    """

    def __init__(self):
        info("Loading LAPPS services...")
        brandeis_services = self._load_services(BRANDEIS)
        vassar_services = self._load_services(VASSAR)
        self.services = []
        self.services_idx = {}
        self.categories = {}
        for service_info in brandeis_services:
            self._add_service(BRANDEIS, service_info)
        for service_info in vassar_services:
            self._add_service(VASSAR, service_info)
        self.categorize()
        
    def _load_services(self, server):
        """Return the service information from all services registered in the
        ServiceManager on the server. Use local cached results if available."""
        if server == BRANDEIS:
            local_info = BRANDEIS_SERVICES_INFO
            services_url = BRANDEIS_SERVICES
        elif server == VASSAR:
            local_info = VASSAR_SERVICES_INFO
            services_url = VASSAR_SERVICES
        else:
            exit("Unknown server: %s" % server)
        if os.path.exists(local_info):
            info("Loading local cache with information for services on %s..." % server)
            with open(local_info) as fh:
                services = json.loads(fh.read())
        else:
            info("Pinging %s service manager for list of services..." % server)
            http_response = urllib.request.urlopen(services_url)
            response_code = http_response.getcode()
            services = json.loads(http_response.read())['elements']
            json.dump(services, open(local_info, 'w'), indent=4)
        return services
    
    def _add_service(self, server, service_info):
        service_id = service_info['serviceId']
        if server == VASSAR:
            if 'opennlp' in service_id or 'gost' in service_id:
                return
        try:
            service = LappsService(server, service_id, service_info)
            self.services.append(service)
            self.services_idx[service_id] = service
        except Exception as e:
            print('ERROR with %s' % service_id)
            print(e)

    def __len__(self):
        return len(self.services)

    def __getitem__(self, i):
        return self.services[i]

    def get_service(self, identifier):
        return self.services_idx.get(identifier)

    def categorize(self):
        self.categories = {}
        for service in self.services:
            try:
                produces = service.metadata['payload']['produces']['annotations']
            except KeyError:
                produces = tuple()
            produces = tuple(sorted(produces))
            self.categories.setdefault(produces, []).append(service)

    def print_categorized_services(self, fh=sys.stdout):
        fh.write('\n')
        for output in sorted(self.categories):
            fh.write('\n'.join(output) + '\n')
            services = sorted(self.categories[output],
                              key=operator.attrgetter('identifier'))
            for service in services:
                fh.write('    %s\n' % service.identifier)
            fh.write('\n')

    def categorized_services_as_string(self):
        buffer = io.StringIO()
        self.print_categorized_services(fh=buffer)
        return buffer.getvalue()
        

class LappsService(object):

    """An object that has all the information needed to allow our interface to
    interact with a LAPPS service."""
    
    def __init__(self, server, tool_identifier, service_manager_info=None):
        """Initialize a service and extract its metadata. A service is identified
        by the server, the service id and may optionally be given the information
        from the ServiceManager."""
        self.server = server
        self.identifier = tool_identifier
        self.info = service_manager_info
        self.wsdl = self._get_wsdl_path()
        self.metadata_file = self._get_metadata_file()
        # Lazy initialization of the zeep client, will initialize if needed when
        # you get the metadata from the service or when you run its execute()
        # method.
        self.client = None
        self._load_metadata()

    def __str__(self):
        return "<Service id='%s'>" % self.identifier

    def _get_wsdl_path(self):
        if self.server == BRANDEIS:
            return WSDL_PATH_BRANDEIS + self.identifier
        elif self.server == VASSAR:
            return WSDL_PATH_VASSAR + self.identifier

    def _get_metadata_file(self):
        return os.path.join(SERVICE_METADATA, self.identifier + '.json')
        
    def _connect(self):
        """Connect the object to the service by creating the zeep client. Only done
        if needed, that is, when self.client is None and the client is required."""
        if self.client is None:
            session = requests.Session()
            if self.server == BRANDEIS:
                user, password = BRANDEIS_USER, BRANDEIS_PASSWORD
            elif self.server == VASSAR:
                user, password = VASSAR_USER, VASSAR_PASSWORD
            else:
                exit("Unknown server: %s" % self.server)
            session.auth = requests.auth.HTTPBasicAuth(user, password)
            transport = zeep.transports.Transport(session=session)
            self.client = zeep.Client(self.wsdl, transport=transport)
        
    def _load_metadata(self):
        """Load metadata from local directory if you have it, if not, get it from
        the service itself and save it to disk. There is now no mechansim in the
        code to update the local metadata, but you can do it simply delete the
        contents of data/services/metadata."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file) as fh:
                self.metadata_string = fh.read()
            self.metadata = json.loads(self.metadata_string)
        else:
            self._connect()
            info("Retrieving metadata from %s" % self.identifier)
            self.metadata_string = self.client.service.getMetadata()
            self._fix_return_type()
            self.metadata = json.loads(self.metadata_string)
            json.dump(self.metadata, open(self.metadata_file, 'w'), indent=4)

    def _fix_return_type(self):
        """Sometimes when getting the metadata the zeep client returns a string
        and sometimes an object with type <class 'zeep.objects.string'>. In the
        latter case the JSON metadata string is embedded in a field named
        '_value_1', this code retrieves that field and uses it to set the
        metadata string.

        You can see the difference with
        
             brandeis_eldrad_grid_1:opennlp.parser_2.0.3
             brandeis_eldrad_grid_1:opennlp.splitter_2.0.3
        
        where the first has the string and the other the weird zeep object. With
        SoapUI you see a difference in that the xsi-type of getMetadataReturn is
        either xsd:string or soapenc:string.

        """
        if not isinstance(self.metadata_string, str):
            self.metadata_string = self.metadata_string['_value_1']

    def getMetadata(self):
        """Return service metadata as a JSON object."""
        return self.metadata

    def execute(self, service_input):
        """Execute the service on an input JSON object, returns a JSON object."""
        self._connect()
        # the client expects a string so get it from the JSON
        service_input = json.dumps(service_input)
        return json.loads(self.client.service.execute(service_input))


class ServiceChains(object):

    CHAINS = {
        'stanford-tok-pos': (
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.tokenizer_2.0.4'),
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.postagger_2.0.4')),
        'stanford-tok-pos-par': (
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.tokenizer_2.0.4'),
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.postagger_2.0.4'),
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.parser_2.0.4')),
        'stanford-tok-pos-sen-ner-par': (
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.tokenizer_2.0.4'),
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.splitter_2.0.4'),
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.postagger_2.0.4'),
            #('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.namedentityrecognizer_2.1.1'),
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.namedentityrecognizer_2.0.4'),
            ('brandeis', 'brandeis_eldrad_grid_1:stanfordnlp.parser_2.0.4'))
    }

    def __init__(self, services):
        self.chains = {}
        for chain_id, chain in ServiceChains.CHAINS.items():
            services = [LappsService(server, s) for server, s in chain]
            self.chains[chain_id] = ServiceChain(chain_id, services)

    def get_chain(self, chain_identifier):
        return self.chains.get(chain_identifier)

    def pp(self):
        print()
        for chain_id in sorted(self.chains.keys()):
            chain = self.chains[chain_id]
            chain.pp()
            print()


class ServiceChain(object):

    """Defines a service chain, which is a sequence of LappsService objects. With
    this, you can run a sequence of services on some input."""

    def __init__(self, identifier, services):
        self.identifier = identifier
        self.services = services

    def run(self, chain_input):
        """Run all the services in sequence on the JSON input."""
        if BYPASS_CHAIN_PROCEESING:
            return json.loads(open('data/example.lif').read())
            #return {"payload": json.loads(open('data/example.lif').read())}
        json_obj = chain_input
        step = 0
        for service in self.services:
            step += 1
            info("service=%s" % service.identifier)
            json_obj = service.execute(json_obj)
            info("discriminator=%s" % json_obj.get('discriminator'))
            if SAVE_STEPS:
                tmp_file = "%02d-%s.lif" % (step, service.identifier.split(':')[-1])
                with open(tmp_file, 'w') as fh:
                    json.dump(json_obj, fh, indent=4)
        return json_obj

    def pp(self):
        print(self.identifier)
        for service in self.services:
            print('   ', service.identifier)

                
def print_separator(c):
    print()
    print(c * 80)
    print()

def print_service_metadata(service):
    print(service, '\n')
    print(service.metadata_string)

def print_io(service, data, result):
    print_separator('>')
    print(service, '\n')
    print_json(data, indent=True)
    print_separator('=')
    print_json(result, indent=False)
    print_separator('<')
        
def print_json(json_obj, indent=True):
    if indent:
        print(json.dumps(json_obj, indent=4))
    else:
        print(json.dumps(json_obj))
    

def test_service(service, data):
    """Test running one service."""
    result = service.execute(data)
    #print_service_metadata(service)
    print_io(service, data, result)

def test_chain(*services):
    """Testing a chain of two services."""
    chain = ServiceChain('test_chain', services)
    result = chain.run(lif_examples.lif0)
    print_json(result, indent=True)
    
        
if __name__ == '__main__':

    tool1 = 'brandeis_eldrad_grid_1:stanfordnlp.tokenizer_2.0.4'
    tool2 = 'brandeis_eldrad_grid_1:stanfordnlp.postagger_2.0.4'
    tool3 = 'brandeis_eldrad_grid_1:stanfordnlp.parser_2.0.4'
    tool4 = 'anc:gate.tokenizer_2.2.0'

    service = LappsService(BRANDEIS, tool3)
    service = LappsService(VASSAR, tool4)

    exit()
    
    services = LappsServices()

    stanford_tokenizer = services.get_service(tool1)
    stanford_tagger = services.get_service(tool2)
    stanford_parser = services.get_service(tool3)

    # test_service(stanford_tokenizer, lif_examples.lif0)
    # test_chain(stanford_tokenizer, stanford_tagger)
    # test_chain(stanford_tokenizer, stanford_tagger, stanford_parser)

    # services.print_categorized_services()

    chains = ServiceChains(services)
    chains.pp()
