# AIRankings

Implementation of AIRankings page using Python & Flask.
The page allows to generate a ranking with different parameter settings, as selected venues, countries and selected years. 

```
AI-Rankings is a tool to create customizable AI Researcher rankings based on 
the DBLP publication dataset. The page is set up with support of the 
University of Würzburg and the BMBF project REGIO. With the ongoing interest 
in AI and AI research, Kristian Kersting (TU Darmstadt) and Andreas Hotho 
(Universität Würzburg) came up with the idea of this tool, which allows for an 
easy check of research activities in different AI research domains. While DBLP 
provides the basic list of publications, citation information is added using 
the Semantic Scholar dataset. Please keep in mind that this dataset is 
independent of Google Scholar and in the consequence/ therefore h-Indexes will 
be different. For the Google Scholar Citations page of an author, please 
follow the Google Scholar icon. For further information about the dataset, 
please visit our FAQ. 

In case of missing conferences or other issues that should be addressed, 
please email us.
```

## Setup 
In order to run this website locally, you need to make the following steps. 

1. Clone the repository.

2. Install the requirements.txt. 

3. Install a mysql database.

4. Generate the data by running the python script `pipeline_prepare_db.py`

5. Load the generated data into the database using `load_database.py`

6. Run the website using the script `airankings.py`. No need to use any flask command. 

(7.) In order to run some tests, run `pytest tests/testsMysql.py` or run the website and run `pytest tests/testsWebsite.py.py`