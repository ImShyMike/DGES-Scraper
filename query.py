"""Query examples and txt dumper for the database."""

from contextlib import redirect_stdout
from typing import Optional, Sequence

from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from models import (
    Course,
    CourseData,
    EntranceExams,
    ExamBundle,
    Institution,
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


def get_full_course_data(
    course_id: Optional[str] = None,
    course_name: Optional[str] = None,
    institution_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> Sequence[CourseData]:
    """
    Query full course data with all relationships.
    Allows for simple filtering.
    """
    with Session(engine) as session:
        query = QUERY_TEMPLATE

        if course_id:
            query = query.where(CourseData.course.has(Course.course_id == course_id))
        if course_name:
            query = query.where(
                CourseData.course.has(Course.name.like(f"%{course_name}%"))
            )
        if institution_id:
            query = query.where(
                CourseData.course.has(
                    Course.institution.has(Institution.id == institution_id)
                )
            )
        if limit:
            query = query.limit(limit)

        result = session.exec(query).all()

        return result


def print_full_course_data(course_data):
    """Print all available data for a course in a readable format."""
    if not course_data:
        print("No course data found")
        return

    print("\n" + "=" * 80)
    print(f"COURSE: {course_data.course.name} ({course_data.course.course_id})")
    print(
        f"INSTITUTION: {course_data.course.institution.name} ({course_data.course.institution_id})"
    )
    print("=" * 80)

    # Basic course information
    print("\n## BASIC INFORMATION")
    print(f"URL: {course_data.course.url}")
    if course_data.extra_stats_url:
        print(f"Extra stats URL: {course_data.extra_stats_url}")

    # Characteristics
    if course_data.characteristics:
        print("\n## CHARACTERISTICS")
        char = course_data.characteristics
        print(f"Degree: {char.degree}")
        print(f"CNAEF Area: {char.CNAEF}")
        print(f"Duration: {char.duration}")
        print(f"ECTS: {char.ECTS}")
        print(f"Teaching Type: {char.type}")
        print(f"Competition: {char.competition}")
        print(f"Current Vacancies: {char.current_vacancies}")

    # Entrance exams
    if course_data.entrance_exams:
        print("\n## ENTRANCE EXAMS\n")
        ee = course_data.entrance_exams

        if ee.is_combination:
            for i, bundle in enumerate(ee.exams):
                if i == 1:
                    print("    and")
                    print("One of the following:")
                for exam in bundle.exams:
                    print(f"{exam.code} {exam.name}")

        else:
            if ee.is_bundle:
                print("Two of the following:")

            for i, bundle in enumerate(ee.exams):
                if not ee.is_bundle and not i == 0:
                    print("    ou")
                for exam in bundle.exams:
                    print(f"{exam.code} {exam.name}")

    # Minimum classification
    if course_data.min_classification:
        print("\n## MINIMUM CLASSIFICATION")
        mc = course_data.min_classification
        print(f"Application Grade: {mc.application_grade}")
        print(f"Entrance Exams: {mc.entrance_exams}")

    # Calculation formula
    if course_data.calculation_formula:
        print("\n## CALCULATION FORMULA")
        cf = course_data.calculation_formula
        print(f"High School Average: {cf.hs_average}%")
        print(f"Entrance Exams: {cf.entrance_exams}%")

    # Regional preference
    if course_data.regional_preference:
        print("\n## REGIONAL PREFERENCE")
        rp = course_data.regional_preference
        print(f"Percentage: {rp.percentage}%")
        print("Regions:")
        for region in rp.regions:
            print(f"  - {region.name}")

    # Other access preferences
    if course_data.other_access_preferences:
        print("\n## OTHER ACCESS PREFERENCES")
        oap = course_data.other_access_preferences
        print(f"Percentage: {oap.percentage}%")
        if hasattr(oap, "courses") and oap.courses:
            print("Courses:")
            for course in oap.courses:
                print(f"  - {course.course_id} {course.name}")

    # Prerequisites
    if course_data.prerequisites:
        print("\n## PREREQUISITES")
        prereq = course_data.prerequisites
        print(f"Type: {prereq.type}")
        print(f"Group: {prereq.group}")

    # Previous applications data
    if (
        course_data.previous_applications
        and course_data.previous_applications.year_data
    ):
        print("\n## HISTORICAL DATA")

        for year_data in sorted(
            course_data.previous_applications.year_data,
            key=lambda y: y.year,
            reverse=True,
        ):
            print(f"\nYEAR: {year_data.year}")

            # Phase 1
            if year_data.phase1:
                p1 = year_data.phase1
                if not year_data.phase2:
                    if p1.grade_last:
                        print("  PHASE 1 (No Phase 2 Data)")
                else:
                    print("  PHASE 1:")

                if p1.grade_last:
                    print(f"    Vacancies: {p1.vacancies}")
                else:
                    print(f"  Vacancies: {p1.vacancies}")

                if p1.grade_last:
                    print(f"    Last Admitted Grade: {p1.grade_last}")

                if p1.candidates:
                    print(
                        f"    Candidates: {p1.candidates.total} (F: {p1.candidates.fem}, M: {p1.candidates.masc})"
                    )
                    print(f"    First Option: {p1.candidates.first_option}")

                if p1.placed:
                    print(
                        f"    Placed: {p1.placed.total} (F: {p1.placed.fem}, M: {p1.placed.masc})"
                    )
                    print(f"    First Option Placed: {p1.placed.first_option}")

                if p1.averages:
                    print(
                        f"    Averages - Application: {p1.averages.application_grade}, Exams: {p1.averages.entrance_exams}, HS: {p1.averages.hs_average}"
                    )

            # Phase 2
            if year_data.phase2:
                print("  PHASE 2:")
                p2 = year_data.phase2
                print(f"    Vacancies: {p2.vacancies}")
                print(f"    Last Admitted Grade: {p2.grade_last}")

                if p2.candidates:
                    print(
                        f"    Candidates: {p2.candidates.total} (F: {p2.candidates.fem}, M: {p2.candidates.masc})"
                    )
                    print(f"    First Option: {p2.candidates.first_option}")

                if p2.placed:
                    print(
                        f"    Placed: {p2.placed.total} (F: {p2.placed.fem}, M: {p2.placed.masc})"
                    )
                    print(f"    First Option Placed: {p2.placed.first_option}")

                if p2.averages:
                    print(
                        f"    Averages - Application: {p2.averages.application_grade}, Exams: {p2.averages.entrance_exams}, HS: {p2.averages.hs_average}"
                    )


def course_data_to_dict(course_data):
    """Convert a CourseData object to a JSON dict."""
    if not course_data:
        return None

    result = {
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
        }

    # Regional preference
    if course_data.regional_preference:
        rp = course_data.regional_preference
        result["regional_preference"] = {
            "percentage": rp.percentage,
            "regions": [{"name": region.name} for region in rp.regions],
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
    course_data = get_full_course_data()[:1]
    print("Course data retrieved successfully.")
    if course_data:
        for course in course_data:
            print_full_course_data(course)

        with open("courses.txt", "w", encoding="utf8") as f:
            with redirect_stdout(f):
                for course in course_data:
                    print_full_course_data(course)

    print(f"\nFound {len(course_data)} course(s).")
