from app.graph import graph
from app.database.DbConnection import test_connection

def main():
    thread_id = 0
    test_connection()
    print("AI Agent started!")
    print("Type 'exit' to quit.\n")

    while True:

        config = {
        "configurable": {
            "thread_id": thread_id
        }
        }

        message = input("You: ")
        
        if message.lower() == "exit":
            print("Goodbye!")
            break
                

        result = graph.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "tool_calls": 0
        },config)

        print(result["messages"][-1].content)
        print()


if __name__ == "__main__":
    main()