import openai
import pandas as pd
import re
import time
from datetime import datetime

# Define OpenAI api key
openai.api_key = 'sk-!xUtQb!kEsCUllLWAmC!T3BlbkFJgIka!wEt6K!cu!dp5U4!'

# Define pattern for tags and shortcodes
pattern = r'\[.*?\]|{.*?}|<\/?[a-zA-Z][^>]*>'

# Define patterns for replacements
img_pattern = r'<img[^>]*>'
heading_open_pattern = r'<(h[2-5]|blockquote)[^>]*>'
heading_close_pattern = r'</(h[2-5]|blockquote)>'

# Get the current date and time
now = datetime.now()
date_for_filename = now.strftime("%Y%m%d-%H%M")

# Define filename
filename = 'translatedresults'+date_for_filename+'.xlsx'

# Function to make the API request
def translate_text(text):
    max_retries = 5  # Define a maximum number of retries.
    retry_count = 0
    common_retry_delay = 10

    while retry_count < max_retries:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You will be provided with a sentence in a foreign language, and your task is to translate it into English."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0,
                max_tokens=1024,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            # Get the content of the response
            response_content = response['choices'][0]['message']['content']

            # Remove the initial phrase
            response_content = response_content.replace(
                "Sure, I can help you with that. Please provide me with the sentence in the foreign language you would like me to translate into English.",
                ""
            )
            # If the translation response is an error message, extract the original word
            error_pattern = r"I'm sorry, but \"(.*?)\" is not a sentence in a foreign language\. It appears to be a word or a title\. Can you please provide a sentence for translation\?"
            match = re.search(error_pattern, response_content)
            if match:
                response_content = match.group(1)
            # Remove the ending phrase
            response_content = response_content.replace("Here's your translation:", "").strip()
            return response_content

        except openai.error.RateLimitError as e:
            print(f"Rate limit reached. Error: {str(e)}")
            print(f"Rate limit reached. Waiting for {common_retry_delay} seconds before retrying...")
            time.sleep(common_retry_delay)

        except openai.error.Timeout as e:
            print(f"Timeout error: {str(e)}")
            print(f"Request timed out. Waiting for {common_retry_delay} seconds before retrying...")
            time.sleep(common_retry_delay)

        except openai.error.ServiceUnavailableError as e:
            print(f"Service unavailable: {str(e)}")
            print(f"Server is overloaded or not ready yet. Waiting for {common_retry_delay} seconds before retrying...")
            time.sleep(common_retry_delay)

        except openai.error.APIError as e:
            if e.http_status == 502:
                print(f"APIError 502: Bad Gateway. Waiting for {common_retry_delay} seconds before retrying...")
                time.sleep(common_retry_delay)
            else:
                raise e
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            retry_delay = 10 + (retry_count * 10) + random.uniform(0, 5)  # Add some randomness to the delay
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_count += 1

    print("Max retries reached. Please try again later.")
    return None

# Read the excel file
df = pd.read_excel("test1.xlsx", engine='openpyxl')

# Create a new columns
df['Translated_Content'] = ""
df['Skipped'] = ""

articlestotranslate = len(list(df['Content'].items()))

# Process each cell in the "Content" column
for idx, value in df['Content'].items():
    text = str(value)  # Convert the cell content to a string
    if text.isspace():  # Skip if the cell is empty or contains only whitespaces
        continue

    matches = re.findall(pattern, text)  # Find all matches
    non_matches = re.split(pattern, text)  # Find all non-matching strings

    blockstotranslate = len(non_matches)

    translations = []
    skipped_parts = []

    # Translate all non-matching strings
    for index, piece in enumerate(non_matches):
        print('translating ', index+1, '/', blockstotranslate, ' in article ', idx+1, '/', articlestotranslate)
        # Skip if the piece is empty or ...
        tokens = len(piece.split()) # Counting tokens as words might not be the exact way tokens are counted in the OpenAI API
        if not piece.strip() or len(piece) < 12 or tokens > 1024:
            translations.append(piece)
            skipped_parts.append(piece)
            continue
        translation = translate_text(piece)
        translations.append(translation)

        # Delay for 1 seconds
        time.sleep(1)

    # Store skipped parts in the 'Skipped' column
    df.at[idx, 'Skipped'] = "|".join(skipped_parts)

    for i in range(len(matches)):
        # Add newline before and after each img tag
        if re.fullmatch(img_pattern, matches[i]):
            matches[i] = '\n\n' + matches[i] + '\n\n'

        # Add newline before opening heading tags and after closing heading tags
        elif re.fullmatch(heading_open_pattern, matches[i]):
            matches[i] = '\n' + matches[i]
        elif re.fullmatch(heading_close_pattern, matches[i]):
            matches[i] = matches[i] + '\n'

    # Reconstruct the text with the translated parts and the non-translated parts
    translated_text_list = []
    for i in range(max(len(translations), len(matches))):
        if i < len(translations):
            translated_text_list.append(translations[i])
        if i < len(matches):
            translated_text_list.append(matches[i])

    translated_text = ''.join(translated_text_list)

    # Remove points before the closing header tags
    pattern_point_header = r'\.(</h[2-5]>)'
    translated_text = re.sub(pattern_point_header, r'\1', translated_text)

    translated_text = translated_text.strip()
    translated_text = re.sub(' +', ' ', translated_text)

    # Update the cell in the DataFrame
    df.at[idx, 'Translated_Content'] = translated_text

    # Save DataFrame back to Excel
    df.to_excel(filename, engine='xlsxwriter', index=False)