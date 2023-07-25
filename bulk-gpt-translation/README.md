# Bulk GPT translation
This script is designed to take input from an excel file, translate the content of a specific column using OpenAI's GPT API, and write the translated content to excel file. Html layout, images and shortcodes are not sent for translation and will be carefully returned to the final result.

## Installation
To install the necessary dependencies, run the following command:
```
pip install -r requirements.txt
```
You need to replace the API key with your own https://platform.openai.com/account/api-keys
## Usage
To use the Metacritic Parser, execute the following Python script:
```
python translate.py
```
## Notes

Any parts of the content that were skipped during translation are also recorded in a separate column.
