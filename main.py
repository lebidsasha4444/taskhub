import os

from taskhub import create_app

app = create_app()


if __name__ == "__main__":
    app.run(port=os.environ.get("PORT", 5000), debug=True, host=os.environ.get("HOST", "127.0.0.1"))
