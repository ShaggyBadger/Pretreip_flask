import os


def convert_tabs_to_spaces(dir_path, tab_size=2):
    """
    converts every file in here to have the same tab or space or whatever. Used to keep things clean when using both vs code AND pythonista
    """
    import os

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                with open(full_path, "r") as f:
                    content = f.read()
                    new_content = content.replace("\t", " " * tab_size)
                with open(full_path, "w") as f:
                    f.write(new_content)
                    print(f"Converted: {full_path}")


if __name__ == "__main__":
    convert_tabs_to_spaces("./")
