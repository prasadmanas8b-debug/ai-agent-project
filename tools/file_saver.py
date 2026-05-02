# File Saver Tool

def save_file(filename: str, content: str):
    with open(filename, 'w') as f:
        f.write(content)
