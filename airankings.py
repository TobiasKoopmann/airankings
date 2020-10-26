from app import app
from gevent.pywsgi import WSGIServer


def main():
    print("Website up and running. ")
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()


if __name__ == '__main__':
    main()
