"""Make a list of all the URLs for the courses in the JSON file."""

import json

with open("courses.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    courses = data["courses"]

url_list = ""  # pylint: disable=invalid-name
for course in courses:
    url_list += (
        "https://www.dges.gov.pt/guias/detcursopi.asp?"
        f"codc={course['id']}&code={course['institution']['id']}\n"
    )

with open("urls.txt", "w", encoding="utf-8") as f:
    f.write(url_list[:-1])
print("URLs saved to urls.txt")
