import requests


def fetch_todo():
    url = "https://jsonplaceholder.typicode.com/todos/1"
    response = requests.get(url)
    if response.status_code == 200:
        todo_data = response.json()
        print("Fetched todo:")
        print(todo_data)
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")


if __name__ == "__main__":
    fetch_todo()
