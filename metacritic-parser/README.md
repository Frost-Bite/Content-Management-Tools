# Metacritic Parser
The Metacritic Parser is a tool designed to retrieve and parse ratings from the popular website metacritic.com. It is specifically built as part of a self-updating game rating system for https://www.progamer.ru/top

## Installation
To install the necessary dependencies, run the following command:
```
pip install -r requirements.txt
```
## Usage
To use the Metacritic Parser, execute the following Python script:
```
python parsemeta.py
```
## Notes

The requirement for proxy servers has been replaced with a free plan from Best-Proxies.ru. For more speed you will need more proxies and more threads (default max_workers=3)

The incoming data about the addresses of the updated data has been replaced with a text file. Please make sure to update the relevant text file with the correct addresses (example: pc/neon-white) before running the parser.

The API functionality has been replaced with writing the retrieved data to a CSV file. The parsed ratings will be stored in a CSV format for further processing or analysis.

The ratings obtained from Metacritic are used for rating recalculation in PHP. Additionally, genres and categories are used for checking the current data in the database.

## Contact
If you have any questions or need further assistance, please feel free to contact the project maintainers at info@progamer.ru