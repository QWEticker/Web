from vega import app
from vega import routes


# timer = Timer(interval=45, function=routes.verify_server_connection).start()
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
