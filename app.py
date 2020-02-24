"""app.py

Simple Python site to interact with LAPPS services and service chains.

To get a list of services ordered on the outputs they generate go to the main
page at http://127.0.0.1:5000/ (if running locally in development mode). You can
also run a chain of services by using http://127.0.0.1:5000/run_chain, for
example:

http://127.0.0.1:5000/run_chain?id=stanford-tok-pos-par&data=http://127.0.0.1:5000/get_file?fname=data/example.txt

This runs the stanford-tok-pos-par chain on the file in the data field. The
available chains are hard coded in the ServiceChains.CHAINS variable in the
services module.

The site also includes a REST API to get a listing of all known services or just
an individual service. The first invocation below gets you the information from
all service in the Brandeis and Vassar service managers, the second gets you the
information for one service.

$ curl -v http://127.0.0.1:5000/api/services
$ curl -v http://127.0.0.1:5000/api/services/anc:gate.ner_2.3.0

"""

import json

from flask import Flask, request, render_template
from flask_restful import Resource, Api
import requests

from services import LappsServices, ServiceChains
from builder import HtmlBuilder
from utils import get_var, get_vars


app = Flask(__name__)
api = Api(app)


LAPPS_SERVICES = LappsServices()
LAPPS_SERVICE_CHAINS = ServiceChains(LAPPS_SERVICES)


def debug(message):
    print('DEBUG:', message)


@app.route('/', methods=['GET', 'POST'])
def index():
    """List all the services, ordered on what they produce."""
    return render_template("index.html",
                           builder=HtmlBuilder(),
                           services=LAPPS_SERVICES)


@app.route('/get_file', methods=['GET', 'POST'])
def get_file():
    """Return a file from the server."""
    fname = get_var(request, "fname")
    return open(fname).read()


@app.route('/run_chain', methods=['GET', 'POST'])
def chain():
    """Present the results of running a chain on a file."""
    chain_identifier, url = get_vars(request, ["id", "data"])
    debug('chain: ' + chain_identifier)
    chain = LAPPS_SERVICE_CHAINS.get_chain(chain_identifier)
    debug('Opening ' + url)
    data = requests.get(url).text
    result = chain.run({
        "discriminator": "http://vocab.lappsgrid.org/ns/media/text", 
        "payload": data})
    return render_template("chain.html",
                           chain=chain,
                           fname=url,
                           result=result,
                           builder=HtmlBuilder())


class Services(Resource):

    """Return a JDON dictionary of all services with the identifier of the service
    as the key and all information from the service manager as the value."""

    def get(self):
        services = {}
        for s in LAPPS_SERVICES:
            key = "%s::%s" % (s.server, s.identifier)
            services[key] = s.info
        return { "services":  services }


class Service(Resource):

    """Return the service manager info for a service, using the service's
    identifier."""
    
    def get(self, identifier):
        service = LAPPS_SERVICES.get_service(identifier)
        info = service.info if not service is None else "SERVICE NOT FOUND"
        return {'service': identifier,
                'info': info}


api.add_resource(Services, '/api/services')
api.add_resource(Service, '/api/services/<string:identifier>')


if __name__ == '__main__':

    app.run(debug=True)
