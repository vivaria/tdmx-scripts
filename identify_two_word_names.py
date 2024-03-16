import re
from collections import Counter


def find_two_word_names(text):
    # Regular expression pattern to find two-word names
    pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'

    # Find all occurrences of two-word names in the text
    two_word_names = re.findall(pattern, text)
    return two_word_names


def main():
    # Open the text file for reading
    file_name = "names.txt"
    try:
        with open(file_name, 'r') as file:
            # Read lines from the file
            lines = file.readlines()

            # List to store all two-word names
            all_two_word_names = []

            # Iterate through each line
            for line in lines:
                # Find two-word names in the current line
                two_word_names = find_two_word_names(line)

                # Add two-word names from the current line to the list
                all_two_word_names.extend(two_word_names)

            # Count the occurrences of each two-word name
            name_counts = Counter(all_two_word_names)

            # Sort the names based on counts in descending order
            sorted_names = sorted(name_counts.items(), key=lambda x: x[0])

            # Print the sorted names with counts
            print("Two-word names found in the file:")
            for name, count in sorted_names:
                print(f"{name}")

    except FileNotFoundError:
        print("File not found.")


if __name__ == "__main__":
    main()
