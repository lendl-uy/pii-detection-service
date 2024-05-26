class ValidationPreprocessor:

    def __init__(self):
        pass

    # Function to remove 'B-' and 'I-' prefixes
    def remove_prefixes(self, labels):
        new_sublist = []
        for item in labels:
            if item.startswith('B-') or item.startswith('I-'):
                new_sublist.append(item[2:])
            else:
                new_sublist.append(item)
        return new_sublist

    def handle_new_labels(self):
        pass