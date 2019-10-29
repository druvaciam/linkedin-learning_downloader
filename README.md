# linkedin-learning_downloader
script for downloading courses content from LinkedIn Learning Premium

# how to use
run from cmd:

python linkedin-learning_downloader.py -login you_linkedin@mail.cc -p your_linkedin_password -dir d:/downloads/linkedin-learning/ -driver d:/downloads/tools/geckodriver.exe --courses https://www.linkedin.com/learning/advanced-sql-for-data-scientists https://www.linkedin.com/learning/python-advanced-design-patterns

# requirements
python 3.5+

pip install selenium

geckodriver.exe https://github.com/mozilla/geckodriver/releases

compatible with geckodriver firefox version https://www.mozilla.org/ru/firefox/new/
