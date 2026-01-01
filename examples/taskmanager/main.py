# Entry point of the application
import typer

app = typer.Typer()

@app.command()
def main():
    typer.echo("Task Manager CLI")

if __name__ == "__main__":
    app()