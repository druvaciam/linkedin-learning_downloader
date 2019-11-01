# linkedin-learning_downloader
script for downloading courses content from LinkedIn Learning

# how to use
<blockquote>python -m pip install -r requirements.txt</blockquote>

<blockquote>python linkedin-learning_downloader.py -login you_linkedin@mail.cc -p your_linkedin_password -dir d:/downloads/linkedin-learning/ -driver d:/downloads/tools/geckodriver.exe --courses https://www.linkedin.com/learning/advanced-sql-for-data-scientists https://www.linkedin.com/learning/python-advanced-design-patterns</blockquote>

# requirements
python 3.5+

<blockquote>
selenium

argparse

bs4
</blockquote>

geckodriver.exe https://github.com/mozilla/geckodriver/releases

compatible with geckodriver firefox version https://www.mozilla.org/ru/firefox/new/
