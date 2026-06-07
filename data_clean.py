import requests
import base64
import os

os.makedirs("data", exist_ok=True)

# Add as many professors as you want here
PROFESSORS = [
    {"id": "421976", "name": "Professor Hadar Ziv"},  # name is just a label for your reference
    {"id": "2512998", "name": "Professor Michael Shindler"},
    {"id": "17490", "name": "Professor Raymond Klefstad"},
    {"id": "1751393", "name": "Professor Alexander Ihler"},
    {"id": "2223956", "name": "Professor Kalev Kask"},
    {"id": "2763913", "name": "Professor Vijay Vazirani"},
    {"id": "2409085", "name": "Professor Jennifer Wong-Ma"},
    {"id": "2285930", "name": "Professor Erik Sudderth"},
    {"id": "240643", "name": "Professor Scott Jordan"},
    {"id": "2127710", "name": "Professor Xiaohui Xie"},
]

url = "https://www.ratemyprofessors.com/graphql"

headers = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.ratemyprofessors.com/",
    "Origin": "https://www.ratemyprofessors.com",
}

query = """
query TeacherRatingsPageQuery($id: ID!) {
  node(id: $id) {
    ... on Teacher {
      firstName
      lastName
      department
      school { name city state }
      avgRating
      avgDifficulty
      numRatings
      wouldTakeAgainPercent
      ratings(first: 20) {
        edges {
          node {
            date
            class
            comment
            helpfulRating
            clarityRating
            difficultyRating
          }
        }
      }
    }
  }
}
"""

def fetch_and_save(professor_id):
    encoded_id = base64.b64encode(f"Teacher-{professor_id}".encode()).decode()
    payload = {"query": query, "variables": {"id": encoded_id}}

    response = requests.post(url, json=payload, headers=headers)
    print(f"ID {professor_id} — Status: {response.status_code}")

    data = response.json()

    # Guard against bad responses
    node = data.get("data", {}).get("node")
    if not node:
        print(f"  ⚠️  No data returned for ID {professor_id}, skipping.")
        return

    teacher = node
    ratings = teacher["ratings"]["edges"]
    last_name = teacher["lastName"].replace(" ", "_")  # handle multi-word last names
    filename = f"data/reviews_{last_name}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {teacher['firstName']} {teacher['lastName']}\n\n")
        f.write(f"**Department:** {teacher['department']}  \n")
        f.write(f"**School:** {teacher['school']['name']}, {teacher['school']['city']}, {teacher['school']['state']}  \n")
        f.write(f"**Avg Rating:** {teacher['avgRating']} | **Difficulty:** {teacher['avgDifficulty']} | **# Reviews:** {teacher['numRatings']}\n\n")
        f.write("---\n\n")

        for i, edge in enumerate(ratings, 1):
            r = edge["node"]
            f.write(f"## Review #{i} — {r['date']}\n\n")
            f.write(f"**Class:** {r['class']}  \n")
            f.write(f"**Clarity:** {r['clarityRating']} | **Helpful:** {r['helpfulRating']} | **Difficulty:** {r['difficultyRating']}  \n\n")
            f.write(f"{r['comment']}\n\n")
            f.write("---\n\n")

    print(f"  ✅ Saved: {filename}")

# Run for all professors
for prof in PROFESSORS:
    fetch_and_save(prof["id"])