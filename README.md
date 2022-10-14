# MScARTS Backend

## Running the Application
Before running the application, its dependencies must be available.
To download all the required dependencies:

- **create a virtual environment** by running `python3 -m venv venv`
- **activate the environment** by running `source venv/bin/activate`
- **install the dependencies** by executing `pip install --upgrade pip && pip install -r requirements.txt`

In a local development environment, the app can then be run directly with flask (by default on localhost, port 5000).
To do so, run:
```
(venv) $ flask db init
(venv) $ flask db migrate
(venv) $ flask db upgrade
(venv) $ flask run
```