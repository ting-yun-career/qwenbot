import sqlite3

from memory import (
    DATABASE,
    create_database,
    save_memory,
    search_semantic_memories
)


create_database()

connection = sqlite3.connect(DATABASE)
connection.execute("DELETE FROM memories")
connection.commit()
connection.close()

save_memory(
    "My name is Pankaj.",
    "Nice to meet you, Pankaj."
)

save_memory(
    "I am learning Python.",
    "Python is useful for AI development."
)

save_memory(
    "I am learning about MCP.",
    "MCP allows AI applications to use tools."
)


results = search_semantic_memories(
    "What is my name"
)

print("\nRelevant Memories")
print("-----------------")

for result in results:
    print("\nScore:", result["score"])
    print("User:", result["user_message"])
    print("Assistant:", result["assistant_message"])
