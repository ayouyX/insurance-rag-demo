import re

# 1. Read the document
with open("data/home_policy.txt", "r", encoding="utf-8") as file:
    document = file.read()


# 2. Split the document using blank lines
text = document.strip()
splits = text.split("\n\n")


# 3. Lists / variables
items = []
final_chunks = []
current_chunk = ""


# 4. Go through every split
for index, split in enumerate(splits, start=1):

    # Remove unnecessary spaces/newlines
    split = split.strip()

    # Ignore empty splits
    if not split:
        continue

    # Store the raw split
    item = {
        "id": index,
        "text": split
    }

    items.append(item)

    # Document title
    if split.startswith("HOME"):
        print(f"TITLE:\n{split}")

    # Main section
    elif split.startswith("SECTION"):
        print(f"SECTION:\n{split}")

    # New subsection: 1.1, 1.2, 2.1, 2.2...
    elif re.match(r"^\d+\.\d+", split):

        # Save the previous subsection first
        if current_chunk:
            final_chunks.append(current_chunk)

        # Start a new subsection
        current_chunk = split

        print(f"SUBSECTION:\n{split}")

    # Continuation of the current subsection
    else:
        current_chunk += "\n" + split

        print(f"CONTINUATION:\n{split}")

    print()


# 5. Save the last subsection
if current_chunk:
    final_chunks.append(current_chunk)


# 6. Print the final merged chunks
print("\n----- FINAL CHUNKS -----\n")

#for index, chunk in enumerate(final_chunks, start=1):#
#    print(f"FINAL CHUNK {index}:")
#    print(chunk)
 #   print()

structured_chunks = []
for chunk in final_chunks:
        lines = chunk.splitlines()
        num_title = lines[0].split(" ",1)
        combined = "\n".join(lines[1:])
        section = num_title[0]
        title = num_title[1]  
        data = {
            "section" : section,
            "title" : title,
            "text" : combined
        }
        structured_chunks.append(data)

for item in structured_chunks:
    print(item)
    print()        

