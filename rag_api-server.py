from app import app
from gevent.pywsgi import WSGIServer


http_server = WSGIServer(("", 6000), app)
http_server.serve_forever()
