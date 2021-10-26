# Example CSV Viewer Application

The CSV Viewer provides a simple [Flask](https://flask.palletsprojects.com/en/2.0.x/) application to load and view data archive files. In the backend, ParData is used to easily extract the data files that is ultimately displayed in the UI.

## Included Files
* `/data`: directory that stores the uploaded archive files
* `/static`: contains custom CSS and Javascript code
* `/templates`: contains the HTML files
* `app.py`: the main Flask application code
* `requirements.txt`: list of all the Python libraries needed to run the application

## Running the Application
1. First, download the example and go to the directory
```
cd csv-viewer
```

2. (Optional) Create a virtual environment (use `deactivate` to deactivate the environment)
```
virtualenv venv
source venv/bin/activate
```

3. Install the requirements

```
pip install -r requirements.txt
```

4. Load the Flask application
```
python app.py
```

5. Copy paste the URL to a browser

6. In the browser you can now:
	1. Upload an data archive file (e.g. [dakota-height-history.tar.gz](https://pardata.readthedocs.io/en/latest/_static/dakota-height-history.tar.gz))
	2. Click upload
	3. View the CSV files extracted with `pardata`
