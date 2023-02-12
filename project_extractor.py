import prompt_toolkit

# This project allows anyone to enter an idea and a name for an imaginary repository
# and it will generate the full repository for you.

# Steps:
# 1. Ask for a name
# 2. Ask for a description
# 3. Potentially repeat:
#   - Ask chatGPT for a directory listing
#   - let the user inspect files and the structure of the repo
#   - The user can either retrieve the full project or regenerate everything
# 4. Recursively retrieve the project
#


# You can use either ChatGPT or OpenAI's models through their official API.
# If you want ot use the official API, provide the key with the OPENAI_API_KEY env variable. ou might also want to set the model below.
# To use some bootleg ChatGPT API that may or may not be up to date and still working, provide CHATGPT_SESSION_TOKEN.
# pyChatGPT is a wrapper around the unofficial API, which is not maintained by me and also not in requirements.txt

import os
official_api_key = os.environ.get("OPENAI_API_KEY", None)
chatgpt_session_token = os.environ.get("CHATGPT_SESSION_TOKEN", None)

if official_api_key:
    import openai
    openai.api_key = official_api_key

    # This class should keep track of a conversation with the official APIs
    class ChatAPI:
        def __init__(self, model="text-davinci-003"):
            self.model = model
            self.text = ""

        def send_message(self, message):
            response = openai.Completion.create(
                engine=self.model,
                prompt=self.text + '\n' + message,
            )

            response = response.choices[0].text

            self.text += response

            return response

        def reset_conversation(self):
            self.text = ""

    api = ChatAPI()
elif chatgpt_session_token:
    from pyChatGPT import ChatGPT
    api = ChatGPT(chatgpt_session_token)
else:
    print("Neither OPENAI_API_KEY nor CHATGPT_SESSION_TOKEN are set. Please set one of them.")


# gets us to a simulated linux terminal in the imaginary repo
template = lambda name, description: f"""I want you to act as a Linux terminal. I will type commands and you will reply with what the terminal should show. I want you to only reply with the terminal output inside one unique code block, and nothing else. do not write explanations. do not type commands unless I instruct you to do so. when I need to tell you something in English, I will do so by putting text inside curly brackets {{like this}}.
My first commands:
{{Project Description: {description}}}
NAME={name}
git clone --quiet https://github.com/$NAME.git 2>&1 > /dev/null && cd $NAME
"""

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter


def ls(folder=None):
    if folder is None:
        folder = ""

    # Preview the current directory
    response = api.send_message(
        "{On this computer, 'ls' produces a space-separated list of files and folders, with folders being prefixed by @ and files with a %. No trailing or leading slashes allowed.}\nls")

    response = response['message']
    # remove ´ and " from output
    response = response.replace("`", "").replace('"', "")
    lines = response.split("\n")
    lines = [line for line in lines if "@" in line or "%" in line]

    entries = []
    for line in lines:
        entries.extend(line.split(" "))

    files = [entry[1:] for entry in entries if entry.startswith("%")]
    folders = [entry[1:] for entry in entries if entry.startswith("@")]

    return files, folders


def get_recursively(pwd=None, files=None, folders=None, depth=0, current_depth=0):
    current_dir = {}

    if current_depth == depth:
        return current_dir

    if pwd:
        _ = api.send_message(f"cd {pwd}")

    if files is None and folders is None:
        files, folders = ls()

    for file in files:
        response = api.send_message(f"cat {file}")['message']

        # remove ´ and " from output
        response = response.replace("`", "").replace('"', "")
        current_dir[file] = response

    for folder in folders:
        current_dir[folder] = get_recursively(folder, depth=depth, current_depth=current_depth + 1)

    if pwd != "":
        _ = api.send_message(f"cd ..")

    return current_dir


def write_recursively(project, output_dir, pwd=None):
    if pwd is None:
        pwd = output_dir

    for file, content in project.items():
        if isinstance(content, dict):
            folder = pwd / file
            folder.mkdir()
            write_recursively(content, folder)
        else:
            with open(pwd / file, "w") as f:
                f.write(content)

def main():
    name = prompt("What is the name of your project? ", completer=prompt_toolkit.completion.WordCompleter(["helloworld"]))
    description = prompt("Describe your project: ", completer=prompt_toolkit.completion.WordCompleter(["A web shop written in Rust using an sqlite database"]))

    while True:
        # Go into the imaginary repository
        try:
            _ = api.send_message(template(name, description))
        except:
            print("Error: GPT is not responding. Please try again later.")
            continue

        files, folders = ls()
        if not files and not folders:
            api.reset_conversation()
            print("Something went wrong parsing the 'ls' output, resetting conversation")
            continue

        print("Folders:")
        for folder in folders:
            print(f"\t{folder}")
        print("Files:")
        for file in files:
            print(f"\t{file}")

        action = prompt("What would you like to do? ", completer=prompt_toolkit.completion.WordCompleter(["regenerate", "retrieve", "exit"]))
        if action == "regenerate":
            api.reset_conversation()
            continue
        elif action == "retrieve":
            print("Retrieving the full project")

            project = get_recursively(depth=2, files=files, folders=folders)

            import os
            import pathlib

            output_dir = pathlib.Path("output") / name
            if output_dir.exists():
                print("Error: output directory already exists")
                continue
            output_dir.mkdir(parents=True)

            write_recursively(project, output_dir)
        elif action == "exit":
            break

if __name__ == "__main__":
    main()
