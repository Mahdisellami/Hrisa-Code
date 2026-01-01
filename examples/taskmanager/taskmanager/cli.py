# CLI entry point for the task manager

import typer

app = typer.Typer()

@app.command()
def main():
    typer.echo('Task Manager is running!')

if __name__ == '__main__':
    app()