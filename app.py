from doctrina import create_app

app = create_app()

app.app_context().push()

if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)
