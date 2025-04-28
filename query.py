"""Query examples and txt dumper for the database."""

import gzip
import json
from typing import Sequence

from sqlalchemy import or_, true
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from models import (
    Averages,
    Characteristics,
    Course,
    CourseData,
    EntranceExams,
    ExamBundle,
    Institution,
    MinimumClassification,
    OtherAccessPreferences,
    PhaseData,
    PreviousApplications,
    RegionalPreference,
    YearData,
    engine,
)

QUERY_TEMPLATE = select(CourseData).options(
    joinedload(CourseData.course).joinedload(Course.institution),
    joinedload(CourseData.characteristics),
    joinedload(CourseData.previous_applications)
    .selectinload(PreviousApplications.year_data)
    .options(
        joinedload(YearData.phase1).options(
            joinedload(PhaseData.candidates),
            joinedload(PhaseData.placed),
            joinedload(PhaseData.averages),
        ),
        joinedload(YearData.phase2).options(
            joinedload(PhaseData.candidates),
            joinedload(PhaseData.placed),
            joinedload(PhaseData.averages),
        ),
    ),
    joinedload(CourseData.entrance_exams)
    .selectinload(EntranceExams.exams)
    .selectinload(ExamBundle.exams),
    joinedload(CourseData.min_classification),
    joinedload(CourseData.calculation_formula),
    joinedload(CourseData.regional_preference).selectinload(RegionalPreference.regions),
    joinedload(CourseData.other_access_preferences).selectinload(
        OtherAccessPreferences.courses
    ),
    joinedload(CourseData.prerequisites),
)

# Define default parameters
DEFAULT_PARAMETERS = {
    # Basic information
    "course_id": None,
    "course_id_operator": "contains",
    "course_name": None,
    "course_name_operator": "contains",
    "institution_id": None,
    "institution_id_operator": "contains",
    "institution_name": None,
    "institution_name_operator": "contains",
    "unique_id": None,
    # Characteristics
    "degree": None,
    "cnaef": None,
    "duration": None,
    "ects": None,
    "ects_operator": "equal",
    "ects_max": None,
    "type": None,
    "competition": None,
    "vacancies": None,
    "vacancies_operator": "equal",
    "vacancies_max": None,
    # Entrance exams
    "exam_code": None,
    "exam_combination": None,
    # Classification
    "min_app_grade": None,
    "min_app_grade_operator": "equal",
    "min_app_grade_max": None,
    "min_exam_grade": None,
    "min_exam_grade_operator": "equal",
    "min_exam_grade_max": None,
    # Regional
    "region": None,
    # Historical data
    "min_grade_last": None,
    "max_grade_last": None,
    "last_grade_operator": "between",
    "year_filter": None,
    # Search configuration
    "results_per_page": "10",
    "sort_by": "course_id",
    "grade_sort_phase": "1",
    "grade_sort_year": "latest",
}


def full_search(config: dict) -> Sequence[CourseData]:
    """Full search with all parameters for the webserver."""

    if not config:
        return []

    # Filter config to only include known options
    params = DEFAULT_PARAMETERS.copy()
    config = {
        k: v for k, v in config.items() if k in DEFAULT_PARAMETERS and v is not None
    }

    params.update(config)

    # Check and set default for results per page
    if params["results_per_page"] not in ("10", "25", "50", "100"):
        params["results_per_page"] = "10"
    limit = int(params["results_per_page"])

    with Session(engine) as session:
        query = QUERY_TEMPLATE

        # Basic information
        if params["course_id"]:
            if params["course_id_operator"] == "exact":
                query = query.where(
                    CourseData.course.has(Course.course_id == params["course_id"])
                )
            elif params["course_id_operator"] == "contains":
                query = query.where(
                    CourseData.course.has(
                        Course.course_id.like(f"%{params['course_id']}%")
                    )
                )
            elif params["course_id_operator"] == "starts_with":
                query = query.where(
                    CourseData.course.has(
                        Course.course_id.like(f"{params['course_id']}%")
                    )
                )

        if params["course_name"]:
            if params["course_name_operator"] == "exact":
                query = query.where(
                    CourseData.course.has(Course.name == params["course_name"])
                )
            elif params["course_name_operator"] == "contains":
                query = query.where(
                    CourseData.course.has(
                        Course.name.like(f"%{params['course_name']}%")
                    )
                )
            elif params["course_name_operator"] == "starts_with":
                query = query.where(
                    CourseData.course.has(Course.name.like(f"{params['course_name']}%"))
                )

        if params["institution_id"]:
            if params["institution_id_operator"] == "exact":
                query = query.where(
                    CourseData.course.has(
                        Course.institution_id == params["institution_id"]
                    )
                )
            elif params["institution_id_operator"] == "contains":
                query = query.where(
                    CourseData.course.has(
                        Course.institution_id.like(f"%{params['institution_id']}%")
                    )
                )
            elif params["institution_id_operator"] == "starts_with":
                query = query.where(
                    CourseData.course.has(
                        Course.institution_id.like(f"{params['institution_id']}%")
                    )
                )

        if params["institution_name"]:
            if params["institution_name_operator"] == "exact":
                query = query.where(
                    CourseData.course.has(
                        Course.institution.has(
                            Institution.name == params["institution_name"]
                        )
                    )
                )
            elif params["institution_name_operator"] == "contains":
                query = query.where(
                    CourseData.course.has(
                        Course.institution.has(
                            Institution.name.like(f"%{params['institution_name']}%")
                        )
                    )
                )
            elif params["institution_name_operator"] == "starts_with":
                query = query.where(
                    CourseData.course.has(
                        Course.institution.has(
                            Institution.name.like(f"{params['institution_name']}%")
                        )
                    )
                )

        if params["unique_id"]:
            query = query.where(CourseData.id == params["unique_id"])

        # Characteristics filters
        if params["degree"]:
            query = query.where(CourseData.characteristics.has(degree=params["degree"]))

        if params["cnaef"]:
            query = query.where(CourseData.characteristics.has(CNAEF=params["cnaef"]))

        if params["duration"]:
            query = query.where(
                CourseData.characteristics.has(duration=params["duration"])
            )

        if params["ects"]:
            if params["ects_operator"] == "equal":
                query = query.where(CourseData.characteristics.has(ECTS=params["ects"]))
            elif params["ects_operator"] == "less":
                query = query.where(
                    CourseData.characteristics.has(
                        Characteristics.ECTS < float(params["ects"])
                    )
                )
            elif params["ects_operator"] == "greater":
                query = query.where(
                    CourseData.characteristics.has(
                        Characteristics.ECTS > float(params["ects"])
                    )
                )
            elif params["ects_operator"] == "between" and params["ects_max"]:
                query = query.where(
                    CourseData.characteristics.has(
                        Characteristics.ECTS.between(
                            float(params["ects"]), float(params["ects_max"])
                        )
                    )
                )

        if params["type"]:
            query = query.where(CourseData.characteristics.has(type=params["type"]))

        if params["competition"]:
            query = query.where(
                CourseData.characteristics.has(competition=params["competition"])
            )

        if params["vacancies"]:
            if params["vacancies_operator"] == "equal":
                query = query.where(
                    CourseData.characteristics.has(
                        current_vacancies=int(params["vacancies"])
                    )
                )
            elif params["vacancies_operator"] == "less":
                query = query.where(
                    CourseData.characteristics.has(
                        Characteristics.current_vacancies < int(params["vacancies"])
                    )
                )
            elif params["vacancies_operator"] == "greater":
                query = query.where(
                    CourseData.characteristics.has(
                        Characteristics.current_vacancies > int(params["vacancies"])
                    )
                )
            elif params["vacancies_operator"] == "between" and params["vacancies_max"]:
                query = query.where(
                    CourseData.characteristics.has(
                        Characteristics.current_vacancies.between(
                            int(params["vacancies"]), int(params["vacancies_max"])
                        )
                    )
                )
            elif params["vacancies_operator"] == "available":
                query = query.where(
                    CourseData.characteristics.has(Characteristics.current_vacancies > 0)
                )

        # Entrance exam filters
        if params["exam_code"]:
            exam_codes = (
                params["exam_code"]
                if isinstance(params["exam_code"], list)
                else [params["exam_code"]]
            )

            if params["exam_combination"] == "all":
                # All selected exams must be present
                for code in exam_codes:
                    query = query.where(
                        CourseData.entrance_exams.has(
                            EntranceExams.exams.any(ExamBundle.exams.any(code=code))
                        )
                    )
            elif params["exam_combination"] == "only":
                # Exact match
                query = query.where(
                    CourseData.entrance_exams.has(
                        ~EntranceExams.exams.any(
                            ExamBundle.exams.any(
                                ~ExamBundle.exams.any(code.in_(exam_codes))
                            )
                        )
                    )
                )
            else:  # "any" or default behavior
                query = query.where(
                    CourseData.entrance_exams.has(
                        EntranceExams.exams.any(
                            ExamBundle.exams.any(code.in_(exam_codes))
                        )
                    )
                )

        # Classification filters
        if params["min_app_grade"]:
            if params["min_app_grade_operator"] == "equal":
                query = query.where(
                    CourseData.min_classification.has(
                        application_grade=float(params["min_app_grade"])
                    )
                )
            elif params["min_app_grade_operator"] == "less":
                query = query.where(
                    CourseData.min_classification.has(
                        MinimumClassification.application_grade < float(params["min_app_grade"])
                    )
                )
            elif params["min_app_grade_operator"] == "greater":
                query = query.where(
                    CourseData.min_classification.has(
                        MinimumClassification.application_grade > float(params["min_app_grade"])
                    )
                )
            elif (
                params["min_app_grade_operator"] == "between"
                and params["min_app_grade_max"]
            ):
                query = query.where(
                    CourseData.min_classification.has(
                        MinimumClassification.application_grade.between(
                            float(params["min_app_grade"]),
                            float(params["min_app_grade_max"]),
                        )
                    )
                )

        if params["min_exam_grade"]:
            if params["min_exam_grade_operator"] == "equal":
                query = query.where(
                    CourseData.min_classification.has(
                        entrance_exams=float(params["min_exam_grade"])
                    )
                )
            elif params["min_exam_grade_operator"] == "less":
                query = query.where(
                    CourseData.min_classification.has(
                        MinimumClassification.entrance_exams < float(params["min_exam_grade"])
                    )
                )
            elif params["min_exam_grade_operator"] == "greater":
                query = query.where(
                    CourseData.min_classification.has(
                        MinimumClassification.entrance_exams > float(params["min_exam_grade"])
                    )
                )
            elif (
                params["min_exam_grade_operator"] == "between"
                and params["min_exam_grade_max"]
            ):
                query = query.where(
                    CourseData.min_classification.has(
                        MinimumClassification.entrance_exams.between(
                            float(params["min_exam_grade"]),
                            float(params["min_exam_grade_max"]),
                        )
                    )
                )

        # Region filters
        if params["region"]:
            query = query.where(
                CourseData.regional_preference.has(
                    RegionalPreference.regions.any(name=params["region"])
                )
            )

        # Historical data filters
        if params["min_grade_last"] or params["max_grade_last"]:
            if params["year_filter"]:
                year_filter = int(params["year_filter"])
                historical_condition = PreviousApplications.year_data.any(
                    YearData.year == year_filter
                )
            else:
                historical_condition = true()

            if params["min_grade_last"] and params["max_grade_last"]:
                if params["last_grade_operator"] == "between":
                    # Find courses where last grade is between the specified values
                    phase_condition = or_(
                        YearData.phase1.has(
                            PhaseData.grade_last.between(
                                float(params["min_grade_last"]),
                                float(params["max_grade_last"]),
                            )
                        ),
                        YearData.phase2.has(
                            PhaseData.grade_last.between(
                                float(params["min_grade_last"]),
                                float(params["max_grade_last"]),
                            )
                        ),
                    )

                    if params["year_filter"]:
                        query = query.where(
                            CourseData.previous_applications.has(
                                PreviousApplications.year_data.any(historical_condition)
                            )
                        )
                        query = query.where(
                            CourseData.previous_applications.has(
                                PreviousApplications.year_data.any(phase_condition)
                            )
                        )
                    else:
                        # If no year filter, just apply the phase condition
                        query = query.where(
                            CourseData.previous_applications.has(
                                PreviousApplications.year_data.any(phase_condition)
                            )
                        )
            elif params["min_grade_last"]:
                # Find courses where last grade is greater than the minimum
                phase_condition = or_(
                    YearData.phase1.has(
                        PhaseData.grade_last >= float(params["min_grade_last"])
                    ),
                    YearData.phase2.has(
                        PhaseData.grade_last >= float(params["min_grade_last"])
                    ),
                )

                # Apply both conditions separately
                if params["year_filter"]:
                    query = query.where(
                        CourseData.previous_applications.has(
                            PreviousApplications.year_data.any(historical_condition)
                        )
                    )
                    query = query.where(
                        CourseData.previous_applications.has(
                            PreviousApplications.year_data.any(phase_condition)
                        )
                    )
                else:
                    query = query.where(
                        CourseData.previous_applications.has(
                            PreviousApplications.year_data.any(phase_condition)
                        )
                    )
            elif params["max_grade_last"]:
                # Find courses where last grade is less than the maximum
                phase_condition = or_(
                    YearData.phase1.has(
                        PhaseData.grade_last <= float(params["max_grade_last"])
                    ),
                    YearData.phase2.has(
                        PhaseData.grade_last <= float(params["max_grade_last"])
                    ),
                )

                # Apply both conditions separately
                if params["year_filter"]:
                    query = query.where(
                        CourseData.previous_applications.has(
                            PreviousApplications.year_data.any(historical_condition)
                        )
                    )
                    query = query.where(
                        CourseData.previous_applications.has(
                            PreviousApplications.year_data.any(phase_condition)
                        )
                    )
                else:
                    query = query.where(
                        CourseData.previous_applications.has(
                            PreviousApplications.year_data.any(phase_condition)
                        )
                    )

        # Apply sorting
        if params["sort_by"]:
            if params["sort_by"] == "course_id":
                query = query.join(CourseData.course).order_by(Course.course_id)
            elif params["sort_by"] == "name_asc":
                query = query.join(CourseData.course).order_by(Course.name.asc())
            elif params["sort_by"] == "institution_asc":
                query = (
                    query.join(CourseData.course)
                    .join(Course.institution)
                    .order_by(Institution.name.asc())
                )
            elif params["sort_by"] in ("grade_asc", "grade_desc"):
                phase_preference = params.get("grade_sort_phase", "1")
                year_preference = params.get("grade_sort_year", "latest")

                query = query.outerjoin(CourseData.previous_applications)
                query = query.outerjoin(PreviousApplications.year_data)

                if year_preference != "latest" and year_preference.isdigit():
                    query = query.where(YearData.year == int(year_preference))

                if phase_preference == "1":
                    query = query.outerjoin(YearData.phase1)
                    if params["sort_by"]  == "grade_asc":
                        query = query.order_by(PhaseData.grade_last.asc().nullslast())
                    else:
                        query = query.order_by(PhaseData.grade_last.desc().nullslast())
                elif phase_preference == "2":
                    query = query.outerjoin(YearData.phase2)
                    if params["sort_by"]  == "grade_asc":
                        query = query.order_by(PhaseData.grade_last.asc().nullslast())
                    else:
                        query = query.order_by(PhaseData.grade_last.desc().nullslast())
            elif params["sort_by"] in ("average_asc", "average_desc"):
                phase_preference = params.get("grade_sort_phase", "1")
                year_preference = params.get("grade_sort_year", "latest")

                query = query.outerjoin(CourseData.previous_applications)
                query = query.outerjoin(PreviousApplications.year_data)

                if year_preference != "latest" and year_preference.isdigit():
                    query = query.where(YearData.year == int(year_preference))

                if phase_preference == "1":
                    query = query.outerjoin(YearData.phase1)
                    # Add explicit join with Averages table
                    query = query.outerjoin(PhaseData.averages)
                    if params["sort_by"] == "average_asc":
                        query = query.order_by(
                            Averages.hs_average.asc().nullslast()
                        )
                    else:
                        query = query.order_by(
                            Averages.hs_average.desc().nullslast()
                        )
                elif phase_preference == "2":
                    query = query.outerjoin(YearData.phase2)
                    # Add explicit join with Averages table
                    query = query.outerjoin(PhaseData.averages)
                    if params["sort_by"] == "average_asc":
                        query = query.order_by(
                            Averages.hs_average.asc().nullslast()
                        )
                    else:
                        query = query.order_by(
                            Averages.hs_average.desc().nullslast()
                        )

        # Apply limit
        if limit:
            query = query.limit(limit)

        # Execute query
        result = session.exec(query.distinct()).all()

        return result


def course_data_to_dict(course_data):
    """Convert a CourseData object to a JSON dict."""
    if not course_data:
        return None

    result = {
        "id": course_data.id,
        "course": {
            "id": course_data.course.course_id,
            "name": course_data.course.name,
            "url": course_data.course.url,
            "institution": {
                "id": course_data.course.institution_id,
                "name": course_data.course.institution.name,
            },
        },
        "extra_stats_url": course_data.extra_stats_url,
    }

    # Characteristics
    if course_data.characteristics:
        char = course_data.characteristics
        result["characteristics"] = {
            "degree": char.degree,
            "CNAEF": char.CNAEF,
            "duration": char.duration,
            "ECTS": char.ECTS,
            "type": char.type,
            "competition": char.competition,
            "current_vacancies": char.current_vacancies,
        }

    # Entrance exams
    if course_data.entrance_exams:
        ee = course_data.entrance_exams
        result["entrance_exams"] = {
            "is_combination": ee.is_combination,
            "is_bundle": ee.is_bundle,
            "bundles": [],
        }

        for bundle in ee.exams:
            if bundle.exams:
                exam_bundle = {
                    "exams": [
                        {"code": exam.code, "name": exam.name} for exam in bundle.exams
                    ]
                }
                result["entrance_exams"]["bundles"].append(exam_bundle)

    # Minimum classification
    if course_data.min_classification:
        mc = course_data.min_classification
        result["min_classification"] = {
            "application_grade": mc.application_grade,
            "entrance_exams": mc.entrance_exams,
        }

    # Calculation formula
    if course_data.calculation_formula:
        cf = course_data.calculation_formula
        result["calculation_formula"] = {
            "hs_average": cf.hs_average,
            "entrance_exams": cf.entrance_exams,
            "prerequisites": cf.prerequisites,
        }

    # Regional preference
    if course_data.regional_preference:
        rp = course_data.regional_preference
        result["regional_preference"] = {
            "percentage": rp.percentage,
            "regions": [region.name for region in rp.regions],
        }

    # Other access preferences
    if course_data.other_access_preferences:
        oap = course_data.other_access_preferences
        result["other_access_preferences"] = {
            "percentage": oap.percentage,
            "courses": [],
        }

        if hasattr(oap, "courses") and oap.courses:
            result["other_access_preferences"]["courses"] = [
                {"id": course.course_id, "name": course.name} for course in oap.courses
            ]

    # Prerequisites
    if course_data.prerequisites:
        prereq = course_data.prerequisites
        result["prerequisites"] = {"type": prereq.type, "group": prereq.group}

    # Historical data
    if (
        course_data.previous_applications
        and course_data.previous_applications.year_data
    ):
        result["historical_data"] = []

        for year_data in sorted(
            course_data.previous_applications.year_data,
            key=lambda y: y.year,
            reverse=True,
        ):
            year_entry = {"year": year_data.year, "phase1": None, "phase2": None}

            # Phase 1
            for num in [1, 2]:
                if (year_data.phase1 and num == 1) or (year_data.phase2 and num == 2):
                    p = year_data.phase1 if num == 1 else year_data.phase2
                    phase_data = {
                        "vacancies": p.vacancies,
                        "grade_last": p.grade_last,
                    }

                    if p.candidates:
                        phase_data["candidates"] = {
                            "total": p.candidates.total,
                            "fem": p.candidates.fem,
                            "masc": p.candidates.masc,
                            "first_option": p.candidates.first_option,
                        }

                    if p.placed:
                        phase_data["placed"] = {
                            "total": p.placed.total,
                            "fem": p.placed.fem,
                            "masc": p.placed.masc,
                            "first_option": p.placed.first_option,
                        }

                    if p.averages:
                        phase_data["averages"] = {
                            "application_grade": p.averages.application_grade,
                            "entrance_exams": p.averages.entrance_exams,
                            "hs_average": p.averages.hs_average,
                        }

                    year_entry[f"phase{num}"] = phase_data

            result["historical_data"].append(year_entry)

    return result


if __name__ == "__main__":
    course_data = get_full_course_data()
    print("Course data retrieved successfully.")

    courses = []
    for course in course_data:
        course_dict = course_data_to_dict(course)
        courses.append(course_dict)

    with open("course_data.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

    with gzip.open("course_data.json.gz", "wt", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

    print(f"\nFound {len(course_data)} course(s).")
