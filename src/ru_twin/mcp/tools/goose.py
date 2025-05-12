import subprocess

class GooseMCP:
    def __init__(self, goose_cli_path="goose"):
        self.goose_cli_path = goose_cli_path

    def run_prompt(self, prompt, workdir="."):
        # Start a Goose session and send a prompt
        process = subprocess.Popen(
            [self.goose_cli_path, "session"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=workdir,
            text=True
        )
        out, err = process.communicate(input=prompt)
        return {"output": out, "error": err}

    def create_project(self, instructions, workdir="."):
        prompt = f"create a new project: {instructions}"
        return self.run_prompt(prompt, workdir=workdir) 