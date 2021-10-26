import pardata
from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
DATA_DIR = 'data'


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Uses a post/redirect/get pattern. Allows form submission to be reloaded:
    1. POST: user uploads file (`data_archive_file`), save the name in `session`
    2. Redirect: once the information is saved, redirect the page
    3. GET: now use `data_archive_name` saved in `session` to load data and display in UI
    """

    if request.method == 'POST':
        # Get the uploaded file
        data_archive_file = request.files.get("data_archive")

        if data_archive_file:
            filename = data_archive_file.filename
            # Store the file in DATA_DIR to access later
            data_archive_file.save(os.path.join(DATA_DIR, filename))
            # Save the filename in session
            session['data_archive_name'] = filename
        else:
            # No file uploaded so reset the filename in session
            session['data_archive_name'] = None

        return redirect(url_for('index'))

    else:
        df_objects = {}
        # Get the saved filename from session
        data_archive_name = session.get('data_archive_name')

        if data_archive_name:
            # Access the data that was stored in DATA_DIR
            file_path = os.path.join(DATA_DIR, data_archive_name)
            # Use pardata to extract the data
            df_objects = pardata.load_dataset_from_location(file_path)['table/csv']

        return render_template('index.html', df_objects=df_objects)


if __name__ == '__main__':
    app.secret_key = os.urandom(42)
    app.run()
