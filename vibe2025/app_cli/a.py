import typer
import shutil
import os

app = typer.Typer()

"""
prompt:

a CLI app should be created: the app should support the following commands:

```
app mv file1 file2  #moves file1 to file2
app cp file1 file2 #copies file1 to file2, with -p will preserve timestamp
app cat file # just displays the content of file 
```

show how to write such an app Typer library, and write the app in python!
"""

@app.command()
def mv(file1: str, file2: str):
    """
    Move file1 to file2
    """
    shutil.move(file1, file2)
    typer.echo(f"Moved {file1} to {file2}")


@app.command()
def cp(
        file1: str,
        file2: str,
        p: bool = typer.Option(False, "--p", help="Preserve timestamp"),
):
    """
    Copy file1 to file2, optionally preserving timestamp with -p
    """
    shutil.copy(file1, file2)
    if p:
        src_stat = os.stat(file1)
        os.utime(file2, (src_stat.st_atime, src_stat.st_mtime))
    typer.echo(f"Copied {file1} to {file2} {'with timestamp preserved' if p else ''}")


@app.command()
def cat(file: str):
    """
    Display the content of the file
    """
    with open(file, "r") as f:
        typer.echo(f.read())


if __name__ == "__main__":
    app()
