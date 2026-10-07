# AI Usage

EDIT THIS FILE BEFORE SUBMITTING. Replace the example prompts and notes with your own real experience. The reviewer will ask you about it.

## Tools used

- Claude (Anthropic): planning the project structure and writing the first version of the code and tests.

## What each tool was used for

- Designing the folder structure and the common data model.
- Writing the first version of the scrapers, cleaning, validation, deduplication, main.py and tests.
- Writing the first draft of the README.

## Representative prompts

1. "Read the assignment and reference document and give me the full project folder with simple code and no comments."
2. (add your own follow-up prompts here)

## Parts that were AI-assisted

Almost all files were AI-assisted. I reviewed every file and I can explain each function.

## Changes I made after reviewing the AI output

- (write what you changed, for example the delay, the rules in validation, the duplicate rule)

## Mistakes or gaps found in AI output

- (write anything you found wrong, for example a selector, a missing edge case, a wrong test)
- Note: the code was tested offline with fake pages and a local test server. The real websites were not reachable from the AI tool, so I ran the real scrape myself.

## How I tested and verified

- Ran `python -m pytest` (unit tests for cleaning, validation, deduplication and scraper parsing with fake pages).
- Ran `python main.py` and checked that the CSV has rows from both sources, prices are numbers, ratings are 1 to 5.
- Compared the totals in `summary_report.json` with the CSV row count.
- Deleted `venv`, created a new one, installed from `requirements.txt` and ran again.
