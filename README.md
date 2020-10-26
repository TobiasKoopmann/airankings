# AIRankings

Implementation of AIRankings page using Python & Flask.
The page allows to generate a ranking with different parameter settings, as selected venues, countries and selected years. 

## Setup 
In order to run this website locally, you need to make the following steps. 

1. Clone the repository.

2. Install the requirements.txt. 

3. Install a mysql database.

4. Generate the data by running the python script `pipeline_prepare_db.py`

5. Load the generated data into the database using `load_database.py`

6. Run the website using the script `airankings.py`. No need to use any flask command. 

(7.) In order to run some tests, run `pytest tests/testsMysql.py` or run the website and run `pytest tests/testsWebsite.py.py`