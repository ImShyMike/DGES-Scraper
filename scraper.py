"""Scrapes all courses from DGES and saves them to an SQLite database."""

import logging
import time
from logging.handlers import MemoryHandler
from typing import Any, Dict, Optional

from bs4.element import NavigableString, Tag
from sqlmodel import Session, SQLModel

from models import (
    Averages,
    CalculationFormula,
    CandidateStats,
    Characteristics,
    Course,
    CourseData,
    EntranceExams,
    Exam,
    ExamBundle,
    Institution,
    MinimumClassification,
    OtherAccessPreferences,
    PhaseData,
    Prerequisites,
    PreviousApplications,
    Region,
    RegionalPreference,
    ShallowCourse,
    YearData,
    engine,
)
from utils import get_next, get_soup

# Set up logging
file_handler = logging.FileHandler("scraper.log")
memory_handler = MemoryHandler(
    capacity=100, flushLevel=logging.ERROR, target=file_handler
)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(formatter)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        memory_handler,
        logging.StreamHandler(),
    ],
)

# Clear the log file
with open("scraper.log", "w", encoding="utf-8"):
    pass


# Base URL for course listings by letter
BASE_URL = "https://www.dges.gov.pt/guias/indcurso.asp?letra="
LETTERS = "ABCDEFGHIJLMNOPQRSTVZ"


def build_candidate(
    stats: Dict[str, Any], is_placed: bool = False
) -> Optional[CandidateStats]:
    """Builds a CandidateStats object from the given dictionary."""

    if not stats:
        return None

    return CandidateStats(
        is_placed=is_placed,
        total=stats.get("total"),
        fem=stats.get("fem"),
        masc=stats.get("masc"),
        first_option=stats.get("first_option"),
    )


def build_averages(media: Dict[str, Any]) -> Optional[Averages]:
    """Builds an Averages object from the given dictionary."""

    if not media:
        return None
    return Averages(
        application_grade=media.get("application_grade"),
        entrance_exams=media.get("entrance_exams"),
        hs_average=media.get("hs_average"),
    )


def build_phase(phase_dict: Dict[str, Any]) -> PhaseData:
    """Builds a PhaseData object from the given dictionary."""

    return PhaseData(
        vacancies=phase_dict.get("vacancies"),
        candidates=build_candidate(
            {
                k: phase_dict[k]
                for k in ["total", "fem", "masc", "first_option"]
                if k in phase_dict
            }
        ),
        placed=build_candidate(
            {
                k[2:]: phase_dict[k]
                for k in ["p_total", "p_fem", "p_masc", "p_first_option"]
                if k in phase_dict
            },
            is_placed=True,
        ),
        averages=build_averages(
            {
                k: phase_dict[k]
                for k in ["application_grade", "entrance_exams", "hs_average"]
                if k in phase_dict
            }
        ),
        grade_last=phase_dict.get("grade_last"),
        info_url=phase_dict.get("info_url"),
    )


def parse_value(val: str) -> Any:
    """Parses a string value into an appropriate type (int, float, or str)."""

    val = val.strip()
    if not val or val == " ":
        return None

    val = val.replace(",", ".")
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def get_structured(header: Tag | NavigableString | None):
    """Get the structured data from a header tag."""
    if not header:
        return None, None, None

    current_element = get_next(get_next(header))

    if current_element.text == "Para mais informação consulte a instituição.":
        logging.debug(
            "No minimum classification/calculation data - institution specific info"
        )
    else:
        value1 = current_element.text.strip()

        current_element = get_next(get_next(current_element))
        value2 = current_element.text.strip()

        current_element = get_next(get_next(current_element))
        value3 = current_element.text.strip()

        return value1, value2, value3

    return None, None, None


start_time = time.time()

logging.info("Getting all courses from DGES...")

# Iterate over each letter to get all courses
courses = []
year = 0  # pylint: disable=invalid-name
for letter in LETTERS:
    listing_url = BASE_URL + letter

    soup = get_soup(listing_url)
    if not soup:
        logging.warning("Failed to get soup for letter %s", letter)
        continue

    logging.info("Processing letter %s", letter)

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

            course_url = (
                "https://www.dges.gov.pt/guias/detcursopi.asp?"
                f"code={institution_id.text.strip()}&codc={last_course['id']}"
            )

            courses.append(
                Course(
                    course_id=last_course["id"],
                    name=last_course["name"],
                    institution=Institution(
                        id=institution_id.text.strip(),
                        name=institution_name.text.strip(),
                    ),
                    url=course_url,
                )
            )
        elif 'class="lin-curso"' in repr(item):
            year = int(item.text.strip().split(" ")[1])

logging.info("Loaded %d courses", len(courses))

database = []
for n, course in enumerate(courses):
    logging.info("%s - Processing course: %s with URL: %s", n, course.name, course.url)
    soup = get_soup(course.url)
    if not soup:
        logging.warning("Failed to get soup for course %s", course.name)
        continue

    year_data = []
    table = soup.find("table")
    if table:
        if not isinstance(table, Tag):
            logging.error("Table is the wrong type for course %s", course.name)
            continue

        rows = table.find_all("tr")

        if len(rows) < 2:
            logging.error("Table has too few rows for course %s", course.name)
            continue

        # Extract column headers (first row)
        year_headers = []
        for cell in rows[0].find_all(["th", "td"])[1:]:
            text = cell.get_text(strip=True)

            span = cell.find("span", class_="bodyTitle")
            if span:
                text = span.get_text(strip=True)

            colspan = int(cell.get("colspan", "1"))
            if text and text != " ":  # avoid blank stuff
                year_headers.extend([text] * colspan)

        logging.debug("Extracted year headers: %s", year_headers)

        # Check if there are phase headers in the second row
        has_phase_headers = False  # pylint: disable=invalid-name
        phase_headers = []
        cells_second_row = rows[1].find_all(["td", "th"])

        # Skip the first cell which usually has a section label
        for cell in cells_second_row[1:]:
            text = cell.get_text(strip=True)

            if "Fase" in text:
                has_phase_headers = True  # pylint: disable=invalid-name
                phase_headers.append(text)
            else:
                phase_headers.append("1ª Fase")

        # If no phase headers were found, all data is for 1ª Fase
        if not has_phase_headers:
            logging.info("No phase headers found, assuming all data is for 1ª Fase")

        # Build column mapping
        col_mapping = {}
        for idx, (year, phase) in enumerate(zip(year_headers, phase_headers), start=1):
            col_mapping[idx] = (year, phase)
            logging.debug("Column %s maps to year %s, phase %s", idx, year, phase)

        data_struct: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for year in set(year_headers):
            data_struct[year] = {"1ª Fase": {}, "2ª Fase": {}}

        # Track section based on the first cell
        current_section = None  # pylint: disable=invalid-name
        rows_to_skip = 1 if len(rows) < 3 else 2  # pylint: disable=invalid-name
        if rows_to_skip == 1:
            logging.info(
                "Table has too few rows for course %s, assuming its only vacancies",
                course.name,
            )

        for row in rows[rows_to_skip:]:
            # Get the label (first cell)
            first_cell = row.find(["th", "td"])
            if not first_cell:
                continue

            label = first_cell.get_text(" ", strip=True).lstrip()

            # Improved section detection - check for <strong> or directly match the section text
            is_section_header = first_cell.find("strong") is not None

            if is_section_header or label in [
                "Vagas",
                "Candidatos",
                "Colocados",
                "Médias dos Colocados",
                "Nota de Candidatura do Último Colocado pelo Contingente Geral",
                "Informação Adicional Sobre Candidatos e Colocados",
            ]:
                current_section = label
                logging.debug("Found section: %s", current_section)

            # Get cells for this row (skip the first label cell)
            cells = row.find_all(["td", "th"])[1:]
            for idx, cell in enumerate(cells, start=1):
                # For the special section of PDFs, extract the url
                if (
                    current_section
                    == "Informação Adicional Sobre Candidatos e Colocados"
                ):
                    a_tag = cell.find("a")
                    value = None  # pylint: disable=invalid-name
                    if a_tag and a_tag.get("href"):
                        value = a_tag["href"]
                        logging.debug("Found info URL: %s", value)
                else:
                    cell_text = cell.get_text(strip=True)
                    value = parse_value(cell_text)

                # Determine the target field name:
                # pylint: disable=invalid-name
                field = None
                if current_section == "Vagas":
                    field = "vacancies"
                elif current_section == "Candidatos":
                    # Distinguish the "header" from the sub‑rows.
                    if label == "Candidatos":
                        field = "total"
                    elif label == "do Sexo Feminino":
                        field = "fem"
                    elif label == "do Sexo Masculino":
                        field = "masc"
                    elif label == "em 1ª Opção":
                        field = "first_option"
                elif current_section == "Colocados":
                    if label == "Colocados":
                        field = "p_total"
                    elif label == "do Sexo Feminino":
                        field = "p_fem"
                    elif label == "do Sexo Masculino":
                        field = "p_masc"
                    elif label == "em 1ª Opção":
                        field = "p_first_option"
                elif current_section == "Médias dos Colocados":
                    if label == "Nota de Candidatura":
                        field = "application_grade"
                    elif label == "Provas de Ingresso":
                        field = "entrance_exams"
                    elif label == "Média do Secundário":
                        field = "hs_average"
                elif (
                    current_section
                    == "Nota de Candidatura do Último Colocado pelo Contingente Geral"
                ):
                    field = "grade_last"
                elif (
                    current_section
                    == "Informação Adicional Sobre Candidatos e Colocados"
                ):
                    field = "info_url"
                # pylint: enable=invalid-name

                # Use the mapping from column index to (year, phase)
                if idx in col_mapping and field:
                    year, phase = col_mapping[idx]
                    phase_dictionary = data_struct[year][phase]
                    if field == "info_url":
                        if value:
                            value = f"https://www.dges.gov.pt/guias/{value}"  # pylint: disable=invalid-name
                    phase_dictionary[field] = value

        # Build the YearData for each year
        year_data = []
        for year, phases in data_struct.items():
            phase1 = build_phase(phases.get("1ª Fase", {}))
            phase2 = build_phase(phases.get("2ª Fase", {}))
            year_data.append(
                YearData(
                    year=int(year),
                    phase1=phase1,
                    phase2=phase2 if has_phase_headers else None,
                )
            )

    # Get extra stats url information
    extra_stats = None  # pylint: disable=invalid-name
    all_urls = soup.find_all("a")
    for url in all_urls:
        if "infocursos.mec.pt" in url.get("href", ""):
            extra_stats = str(url["href"])  # pylint: disable=invalid-name
            logging.debug("Found course stats URL: %s", url["href"])

    # Get even more info
    info_header = soup.find("h2", string="Características do par Instituição/Curso")
    if not info_header:
        logging.error("No info header found for course %s", course.name)
        continue

    info_header = info_header.next

    info_dict = {}
    while info_header:
        info_header = info_header.next
        if "<br/>" in repr(info_header):
            continue
        if repr(info_header).startswith("<a") or not info_header:
            break
        data_pair = info_header.text.strip().split(": ", 1)
        if len(data_pair) != 2:
            logging.warning(
                "Info data is not in the expected format: %s", info_header.text.strip()
            )
            continue

        key, value = data_pair
        info_dict[key] = value
        logging.debug("Found info: %s: %s", key, value)

    current_vacancies = None  # pylint: disable=invalid-name
    vacancies = [info_dict[i] for i in list(info_dict) if "Vagas para " in i]
    if vacancies:
        current_vacancies = int(vacancies[0])

    characteristics = Characteristics(
        degree=str(info_dict.get("Grau")),
        CNAEF=str(info_dict.get("Área CNAEF")),
        duration=str(info_dict.get("Duração")),
        ECTS=int(info_dict.get("ECTS", -1)),
        type=str(info_dict.get("Tipo de Ensino")),
        competition=str(info_dict.get("Concurso")),
        current_vacancies=current_vacancies,
    )

    # Get the entrance exam data
    entrance_exams = None  # pylint: disable=invalid-name
    entrance_exam_data = soup.find("h2", string="Provas de Ingresso")
    if entrance_exam_data:
        logging.info("Found entrance exam header.")
        entrance_exam_data = entrance_exam_data.next
        if entrance_exam_data:
            entrance_exam_data = entrance_exam_data.next
        exams = []
        counter = 0  # pylint: disable=invalid-name
        is_combination = False  # pylint: disable=invalid-name
        is_bundle = False  # pylint: disable=invalid-name
        exams_final_data = []
        exams_data = []

        while (
            entrance_exam_data
            and not entrance_exam_data.name == "h2"
            and not entrance_exam_data.text == "Classificações Mínimas"
        ):
            counter += 1
            if counter == 2 and entrance_exam_data.text.strip() == "e":
                is_combination = True  # pylint: disable=invalid-name
                entrance_exam_data = get_next(get_next(get_next(entrance_exam_data)))
                continue

            if entrance_exam_data.text.strip() == "ou":
                entrance_exam_data = entrance_exam_data.next
                exams_final_data.append(exams_data)
                exams_data = []
                continue

            entrance_exam_str = entrance_exam_data.text.strip()
            if entrance_exam_str == (
                "A informação sobre as condições de acesso deve"
                " ser obtida diretamente junto da universidade."
            ):
                break

            if entrance_exam_str in ("Um dos seguintes conjuntos:", ""):
                entrance_exam_data = entrance_exam_data.next
                continue

            if entrance_exam_str == "Duas das seguintes provas:":
                entrance_exam_data = entrance_exam_data.next
                is_bundle = True  # pylint: disable=invalid-name
                continue

            exam_lst = entrance_exam_str.split("  ", 1)
            if len(exam_lst) != 2:
                logging.warning(
                    "Entrance exam data is not in the expected format: %s",
                    entrance_exam_str,
                )
                entrance_exam_data = entrance_exam_data.next
                continue

            exam_code, exam_name = exam_lst
            exam_name = exam_name.split(" (", 1)[0].strip()
            exams.append(Exam(name=exam_name, code=exam_code))
            exams_data.append(Exam(name=exam_name, code=exam_code))

            entrance_exam_data = entrance_exam_data.next
            if entrance_exam_data:
                entrance_exam_data = entrance_exam_data.next

        # Group exams
        exams_final_data.append(exams_data)
        if not is_combination:
            exam_bundles = [ExamBundle(exams=exams) for exams in exams_final_data]
        else:
            first_exam = exams_final_data[0].pop(0)
            exam_bundles = [ExamBundle(exams=[first_exam])] + [
                ExamBundle(exams=exams) for exams in exams_final_data
            ]

        entrance_exams = EntranceExams(
            is_combination=is_combination, is_bundle=is_bundle, exams=exam_bundles
        )

    # Get the minimum classification
    min_classification = None  # pylint: disable=invalid-name
    min_classification_header = soup.find("h2", string="Classificações Mínimas")
    application_grade_value, entrance_exams_value, _ = get_structured(
        min_classification_header
    )
    if application_grade_value and entrance_exams_value:
        logging.info("Found minimum classification header.")
        min_classification = MinimumClassification(
            application_grade=parse_value(application_grade_value.rsplit(" ", 2)[1]),
            entrance_exams=parse_value(entrance_exams_value.rsplit(" ", 2)[1]),
        )

    # Get the calculation formula
    calc_formula = None  # pylint: disable=invalid-name
    calc_formula_header = soup.find("h2", string="Fórmula de Cálculo")

    hs_average_value, entrance_exams_value, prerequisites_value = get_structured(calc_formula_header)
    if hs_average_value and entrance_exams_value:
        logging.info("Found calculation formula header.")

        prerequisites = None
        if prerequisites_value and prerequisites_value.split(": ")[0] == "Pré-Requisito":
            prerequisites = prerequisites_value.split(": ")[1].strip()[:-1]

        calc_formula = CalculationFormula(
            hs_average=parse_value(hs_average_value.rsplit(" ", 2)[2][:-1]),
            entrance_exams=parse_value(entrance_exams_value.rsplit(" ", 2)[2][:-1]),
            prerequisites=prerequisites
        )

    # Get the regional preference
    regional_preference = None  # pylint: disable=invalid-name
    regional_preference_header = soup.find("h2", string="Preferência Regional")
    if regional_preference_header:
        logging.info("Found regional preference header.")
        regional_preference_header = get_next(get_next(regional_preference_header))

        percentage = regional_preference_header.text.strip()

        regional_preference_header = get_next(get_next(regional_preference_header))

        regions = regional_preference_header.text.strip().split(": ")[1].split(", ")
        regional_preference = RegionalPreference(
            percentage=parse_value(percentage[:-1].split(" ")[-1]),
            regions=[Region(name=region.strip()) for region in regions],
        )

    # Get the other access preferences
    other_access_preferences = None  # pylint: disable=invalid-name
    oa_preferences_header = soup.find("h2", string="Outros Acessos Preferenciais")
    if oa_preferences_header:
        logging.info("Found other access preferences header.")
        oa_preferences_header = get_next(get_next(oa_preferences_header))
        percentage = oa_preferences_header.text.strip()
        oa_preferences_header = get_next(
            get_next(get_next(get_next(oa_preferences_header)))
        )
        courses = []
        while True:
            if (
                not oa_preferences_header
                or oa_preferences_header.name == "a"
                or oa_preferences_header.text.strip() == ""
            ):
                break
            if oa_preferences_header.name == "br":
                oa_preferences_header = oa_preferences_header.next
                continue

            course_id, course_name = oa_preferences_header.text.strip().split(" ", 1)
            shallow_course = {
                "id": course_id,
                "name": course_name,
            }
            courses.append(shallow_course)
            oa_preferences_header = get_next(get_next(oa_preferences_header))

        if courses:
            other_access_preferences = OtherAccessPreferences(
                percentage=parse_value(percentage[:-1].split(" ")[-1]),
                courses=[
                    ShallowCourse(course_id=course["id"], name=course["name"])
                    for course in courses
                ],
            )

    # Get prerequisites
    prerequisites = None  # pylint: disable=invalid-name
    prerequisites_header = soup.find("h2", string="Pré-Requisitos")
    if prerequisites_header:
        logging.info("Found prerequisites header.")
        prerequisites_header = get_next(get_next(prerequisites_header))
        prerequisites_list = prerequisites_header.text.strip().split(": ", 1)
        if len(prerequisites_list) == 2:
            prerequisite_type = prerequisites_list[1]
            prerequisites_header = get_next(
                get_next(get_next(get_next(prerequisites_header)))
            )
            groups = []
            while True:
                if (
                    not prerequisites_header
                    or prerequisites_header.name == "h2"
                    or prerequisites_header.text.strip() == ""
                    or prerequisites_header.text.strip() == "Provas de Ingresso"
                ):
                    break
                if prerequisites_header.name == "br":
                    prerequisites_header = prerequisites_header.next
                    continue

                prerequisite_group = (
                    prerequisites_header.text.strip()
                    .split(" - ", 1)[0]
                    .split(" ", 1)[1]
                )
                logging.debug("Found prerequisite group: %s", prerequisite_group)
                groups.append(prerequisite_group)
                prerequisites_header = get_next(get_next(prerequisites_header))

            if groups:
                if len(groups) > 1:
                    logging.warning("Multiple prerequisite groups found: %s", groups)

                prerequisites = Prerequisites(
                    type=prerequisite_type,
                    group=groups[0],
                )
        else:
            logging.warning(
                "Prerequisites data is not in the expected format: %s",
                prerequisites_header.text.strip(),
            )

    database.append(
        CourseData(
            course=course,
            previous_applications=PreviousApplications(year_data=year_data),
            characteristics=characteristics,
            entrance_exams=entrance_exams,
            min_classification=min_classification,
            calculation_formula=calc_formula,
            regional_preference=regional_preference,
            other_access_preferences=other_access_preferences,
            prerequisites=prerequisites,
            extra_stats_url=extra_stats,
        )
    )

    logging.info("Sleeping for 0.1 seconds...")
    time.sleep(0.1)

logging.info("Finished processing all courses.")
logging.info("Saving data to the database...")

with Session(engine) as session:
    # Wipe the full database
    SQLModel.metadata.drop_all(engine)

    # Create the database tables if they don't exist
    SQLModel.metadata.create_all(engine)

    # First insert all unique institutions
    unique_institutions = {}
    for course_data in database:
        inst = course_data.course.institution
        if inst.id not in unique_institutions:
            # Check if institution already exists in DB
            existing = session.get(Institution, inst.id)
            if existing:
                unique_institutions[inst.id] = existing
            else:
                unique_institutions[inst.id] = inst
                session.add(inst)

    # Update all courses to use the unique institution instances
    for course_data in database:
        course_data.course.institution = unique_institutions[
            course_data.course.institution.id
        ]
        course_data.course.institution_id = course_data.course.institution.id

    # Convert or remove complex objects before database insertion
    for course_data in database:
        # Handle regional_preference correctly
        if course_data.regional_preference:
            # Create actual Region objects
            if hasattr(course_data.regional_preference, "regions"):
                region_objects = []
                for region in course_data.regional_preference.regions:
                    region_objects.append(region)

                # Update with our properly created regions
                course_data.regional_preference.regions = region_objects

            # Save the regional_preference to get an ID
            session.add(course_data.regional_preference)
            session.flush()

            # Update the reference ID
            course_data.regional_preference_id = course_data.regional_preference.id

        # Handle other_access_preferences correctly
        if course_data.other_access_preferences:
            # Create properly linked ShallowCourse objects
            if hasattr(course_data.other_access_preferences, "courses"):
                shallow_courses = []
                for shallow_course in course_data.other_access_preferences.courses:
                    shallow_courses.append(shallow_course)

                # Update with properly created shallow courses
                course_data.other_access_preferences.courses = shallow_courses

            # Add the OtherAccessPreferences to session to get ID
            session.add(course_data.other_access_preferences)
            session.flush()

            # Set the ID for reference
            course_data.other_access_preferences_id = course_data.other_access_preferences.id

            # Update the relationship on both sides
            for shallow_course in course_data.other_access_preferences.courses:
                shallow_course.other_access_preferences_id = course_data.other_access_preferences.id

        # Handle previous_applications correctly
        if (
            course_data.previous_applications
            and course_data.previous_applications.year_data
        ):
            # Add the PreviousApplications to session to get an ID
            session.add(course_data.previous_applications)
            session.flush()

            # Set the ID for reference on CourseData
            course_data.previous_applications_id = course_data.previous_applications.id

            # Update the relationship on all YearData objects
            for year in course_data.previous_applications.year_data:
                year.previous_applications_id = course_data.previous_applications.id

    # Add the courses to the database
    session.add_all(database)
    session.commit()

logging.info("Data saved to the database successfully.")

# Apply pragmas to the database
with engine.connect() as conn:
    conn.exec_driver_sql("PRAGMA analysis_limit=1000")
    conn.exec_driver_sql("PRAGMA optimize")
    conn.exec_driver_sql("PRAGMA vacuum")
    conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    conn.exec_driver_sql("PRAGMA locking_mode=NORMAL")
    conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
    conn.exec_driver_sql("ANALYZE")
    conn.exec_driver_sql("PRAGMA query_only=ON")
    conn.commit()

time_taken = time.time() - start_time

logging.info("Total courses processed: %d", len(database))
logging.info("Data processing completed in %.2f seconds", time_taken)
