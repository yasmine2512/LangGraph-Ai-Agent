from dotenv import load_dotenv
from app.graph import graph


load_dotenv()


def main():
    message = input("You: ")

    result = graph.invoke({
        "message": message,
        "response": ""
    })

    print("AI:", result["response"])


if __name__ == "__main__":
    main()