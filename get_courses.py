"""Get all courses from the DGES website."""

import logging

import models
from utils import get_next, get_soup

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Base URL for course listings by letter
BASE_URL = "https://www.dges.gov.pt/guias/indcurso.asp?letra="
LETTERS = "ABCDEFGHIJLMNOPQRSTVZ"


# Iterate over each letter to get all courses
courses_info = []
year = 0  # pylint: disable=invalid-name
for letter in LETTERS:
    listing_url = BASE_URL + letter
    soup = get_soup(listing_url)
    if not soup:
        logging.warning("Failed to get soup for letter %s", letter)
        continue

    # Get the div with everything
    stuff_div = soup.select_one(
        "html body div.width div.minwidth div.layout div.container "
        "div.content div#bot-all div.bot-blue-center div#caixa-orange div.inside"
    )

    if not stuff_div:
        logging.warning("No content found for letter %s", letter)
        continue

    # Iterate over each item in the div (can be course, institution, br, etc...)
    last_course = {}
    print(list(stuff_div.children))
    for i, item in enumerate(stuff_div.children):
        if 'class="box10"' in repr(item):
            # Get the course ID and name
            course_id = get_next(get_next(item))
            logging.debug("Course ID: %s", course_id.text.strip())

            course_name = get_next(get_next(course_id))
            logging.debug("Course name: %s", course_name.text.strip())

            last_course = {
                "id": course_id.text.strip(),
                "name": course_name.text.strip(),
            }

            logging.info("Found course: %s", item.text.strip())
        elif 'class="lin-curso"' in repr(item) and last_course:
            if not year:
                logging.warning("Year not found before course.")
                continue

            if not last_course:
                logging.warning("Last course not found before institution.")
                continue

            # Get the institution ID and name
            institution_id = get_next(get_next(get_next(item)))
            logging.debug("Institution ID: %s", institution_id.text.strip())

            institution_name = get_next(get_next(institution_id))
            logging.debug("Institution name: %s", institution_name.text.strip())

            vacancies = get_next(get_next(get_next(institution_name)))
            logging.debug("Vacancies: %s", vacancies.text.strip())

            course_url = (
                "https://www.dges.gov.pt/guias/detcursopi.asp?"
                f"code={institution_id.text.strip()}&codc={last_course['id']}"
            )

            courses_info.append(
                models.Course(
                    id=last_course["id"],
                    name=last_course["name"],
                    institution=models.Institution(
                        id=institution_id.text.strip(),
                        name=institution_name.text.strip(),
                    ),
                    url=course_url,
                    vacancies=int(vacancies.text.strip())
                    if vacancies.text.strip().isdigit()
                    else -1,
                )
            )
        elif 'class="lin-curso"' in repr(item):
            year = int(item.text.strip().split(" ")[1])

json_data = models.Courses(courses=courses_info, year=year).model_dump_json(indent=4)
# Save to file
with open("courses.json", "w", encoding="utf-8") as f:
    f.write(json_data)
