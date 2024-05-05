import re


def separate_text_file(input_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            text = file.read()

            # Use regular expression to find and separate connected words
            separated_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

            # Separate prices by inserting a space before the dollar sign
            separated_text = re.sub(r'(\w)\$', r'\1 $', separated_text)

            # Separate numbers from words by inserting a space
            separated_text = re.sub(
                r'(\D)(\d+\.\d+|\d+)(?=\D|$)', r'\1 \2', separated_text)

        with open(input_file, 'w', encoding='utf-8') as file:
            file.write(separated_text)


    except FileNotFoundError:
        print(f"File '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")