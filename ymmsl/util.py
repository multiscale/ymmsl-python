def remove_trailing_whitespace(text: str) -> str:
    """Remove trailing whitespace from each line in text

    This ensures that each line in text ends with only a newline, with no whitespace in
    between the text and that newline.
    """
    return '\n'.join([line.rstrip() for line in text.split('\n')]) + '\n'
