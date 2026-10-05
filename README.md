# MailMate - NLP Email Reply Generator
```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py        # open http://127.0.0.1:5000
```
NLP used: spaCy tokenization, lemmatization, NER (PERSON/DATE/TIME/ORG/MONEY), keyword-weighted intent scoring, lexicon sentiment, urgency + signature-name detection, regex for times, amounts, order refs.

## Dataset
`dataset/email_dataset.csv` - 230 labelled synthetic emails (200 standard + 30 hard cases) covering the 10 intents.
Columns: id, subject, email, intent, sentiment, urgent, sender, date, time, reference, level.
Rebuild with `python dataset/make_dataset.py`, evaluate with `python dataset/evaluate.py` (writes dataset/results.json).
