from flask import Flask

from api.routes import api
from database.database import initialize_database


def create_app():
    app = Flask(__name__)

    initialize_database()

    app.register_blueprint(api)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False,
        use_reloader=False
    )