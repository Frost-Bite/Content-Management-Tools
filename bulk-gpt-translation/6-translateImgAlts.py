import pandas as pd
from bs4 import BeautifulSoup
import translators as ts
import time


# Function to extract alt attributes from img tags in HTML content
def extract_and_translate_alts(html_content):
    if not isinstance(html_content, str):
        return html_content

    soup = BeautifulSoup(html_content, 'html.parser')
    imgs = soup.find_all('img')

    for img in imgs:
        if img.has_attr('alt'):
            original_alt = img['alt']
            print('Translating text:', original_alt)
            if not original_alt.strip():
                print("Text is empty. Skipping translation.")
            else:
                success = False
                retries = 33  # Set a maximum number of retries
                while not success and retries > 0:
                    try:
                        translated_alt = ts.translate_text(original_alt, translator='google', from_language='ru', to_language='en')
                        img['alt'] = translated_alt
                        success = True
                    except Exception as e:
                        print(f"Error while translating: {e}")
                        print(f"Error word: {original_alt}")
                        print(f"Retrying in 5 seconds...")
                        time.sleep(5)  # Wait for 5 seconds
                        retries -= 1

                if retries == 0:
                    print("Failed to translate after 33 attempts. Moving to next alt text.")

    return str(soup)


# Read the xlsx file
df = pd.read_excel('5-mergeddata.xlsx', engine='openpyxl')

# Replace alts and translate them
for index, row in df.iterrows():
    if not row['NewContentn'] or not isinstance(row['NewContentn'], str):
        print(f'Skipping empty cell at index {index}')
        continue
    df.at[index, 'NewContentnenalts'] = extract_and_translate_alts(row['NewContentn'])
    # Write to a new xlsx file
    df.to_excel('6-imgaltstrans.xlsx', index=False, engine='xlsxwriter')
    print('The article is written to a file', index)


print("File has been updated and written to destination_file.xlsx")