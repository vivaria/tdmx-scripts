def read_names_from_file(file_path):
    with open(file_path, 'r') as file:
        names = file.readlines()
    return [name.strip() for name in names]


def detect_transposed_names(names):
    transposed_names = set()
    for name1 in names:
        first_name1, last_name1 = name1.split()
        for name2 in names:
            first_name2, last_name2 = name2.split()
            if first_name1 == last_name2 and last_name1 == first_name2 and name1 != name2:
                transposed_names.add((name1, name2))
    return transposed_names


def main():
    file_path = "names.txt"  # Update with your file path
    names = read_names_from_file(file_path)
    transposed_names = detect_transposed_names(names)

    if transposed_names:
        print("Transposed names detected:")
        for name_pair in transposed_names:
            print(name_pair[0])
    else:
        print("No transposed names detected.")


if __name__ == "__main__":
    main()
