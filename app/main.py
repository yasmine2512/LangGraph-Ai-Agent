from app.graph import graph

def main():
    print("AI Agent started!")
    print("Type 'exit' to quit.\n")

    while True:
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
            ]
        })
        # print("\n--- Messages ---")
        # for msg in result["messages"]:
        #     print("\nTYPE:", type(msg).__name__)
        #     print("CONTENT:", msg.content)

        #     if hasattr(msg, "tool_calls"):
        #         print("TOOL CALLS:", msg.tool_calls)

        # print("\n--- Final answer ---")
        print(result["messages"][-1].content)
        print()


if __name__ == "__main__":
    main()