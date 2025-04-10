"""Pydantic models for the application."""

from typing import List, Optional

# from pydantic import BaseModel
from sqlmodel import JSON, Column, Field, Relationship, SQLModel, create_engine

# Specify the database URL. Here we use a local SQLite database file.
SQLITE_URL = "sqlite:///database.db"
engine = create_engine(
    SQLITE_URL, echo=True
)  # echo=True prints SQL commands for debugging


class Courses(SQLModel):
    """Model for a list of courses for a given year."""

    year: int
    courses: List["Course"]


class Institution(SQLModel, table=True):
    """Model for an institution."""

    id: str = Field(primary_key=True)
    name: str
    courses: List["Course"] = Relationship(back_populates="institution")


class Course(SQLModel, table=True):
    """Model for a course from an institution."""

    id: Optional[int] = Field(default=None, primary_key=True)

    course_id: str
    name: str
    url: str
    institution_id: Optional[str] = Field(default=None, foreign_key="institution.id")
    institution: Optional[Institution] = Relationship(back_populates="courses")
    vacancies: int


class CandidateStats(SQLModel, table=True):
    """Model for the candidates statistics."""

    id: Optional[int] = Field(default=None, primary_key=True)

    is_placed: bool = Field(default=False)
    total: Optional[int]
    fem: Optional[int]
    masc: Optional[int]
    first_option: Optional[int]


class Averages(SQLModel, table=True):
    """Model for the averages of candidates."""

    id: Optional[int] = Field(default=None, primary_key=True)

    application_grade: Optional[float]
    entrance_exams: Optional[float]
    hs_average: Optional[float]


class PhaseData(SQLModel, table=True):
    """Model for a phase with its data."""

    id: Optional[int] = Field(default=None, primary_key=True)

    candidates_id: Optional[int] = Field(default=None, foreign_key="candidatestats.id")
    placed_id: Optional[int] = Field(default=None, foreign_key="candidatestats.id")
    averages_id: Optional[int] = Field(default=None, foreign_key="averages.id")

    vacancies: Optional[int]
    candidates: Optional[CandidateStats] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PhaseData.candidates_id]"}
    )
    placed: Optional[CandidateStats] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PhaseData.placed_id]"}
    )
    averages: Optional[Averages] = Relationship()
    grade_last: Optional[float]
    info_url: Optional[str]


class YearData(SQLModel, table=True):
    """Model for a year with its data."""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_data_id: Optional[int] = Field(default=None, foreign_key="coursedata.id")

    year: int

    phase1_id: Optional[int] = Field(default=None, foreign_key="phasedata.id")
    phase2_id: Optional[int] = Field(default=None, foreign_key="phasedata.id")

    phase1: Optional["PhaseData"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[YearData.phase1_id]"}
    )
    phase2: Optional["PhaseData"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[YearData.phase2_id]"}
    )
    course_data: Optional["CourseData"] = Relationship(
        back_populates="year_data",
        sa_relationship_kwargs={"foreign_keys": "[YearData.course_data_id]"},
    )


class Characteristics(SQLModel, table=True):
    """Model for the characteristics of a course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    degree: str
    CNAEF: str
    duration: str
    ECTS: int
    type: str
    competition: str
    current_vacancies: Optional[int]


class Exam(SQLModel, table=True):
    """Model for an exam."""

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    code: str
    exam_bundle_id: Optional[int] = Field(
        default=None, foreign_key="exambundle.id"
    )
    exam_bundle: Optional["ExamBundle"] = Relationship(back_populates="exams")


class ExamBundle(SQLModel, table=True):
    """Model for a bundle of exams."""

    id: Optional[int] = Field(default=None, primary_key=True)

    exams: List[Exam] = Relationship(back_populates="exam_bundle")
    entrance_exams_id: Optional[int] = Field(
        default=None, foreign_key="entranceexams.id"
    )
    entrance_exams: Optional["EntranceExams"] = Relationship(back_populates="exams")


class EntranceExams(SQLModel, table=True):
    """Model for the entrance exams of a course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    is_combination: bool = Field(default=False)
    is_bundle: bool = Field(default=False)
    exams: List[ExamBundle] = Relationship(back_populates="entrance_exams")


class Region(SQLModel, table=True):
    """Model for a region."""

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    regional_preference_id: Optional[int] = Field(
        default=None, foreign_key="regionalpreference.id"
    )
    regional_preference: Optional["RegionalPreference"] = Relationship(
        back_populates="regions"
    )

class RegionalPreference(SQLModel, table=True):
    """Model for the regional preference of a course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    percentage: float
    regions: List[Region] = Relationship(
        back_populates="regional_preference",
    )


class ShallowCourse(SQLModel, table=True):
    """Model for a shallow course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    course_id: str
    name: str
    other_access_preferences_id: Optional[int] = Field(
        default=None, foreign_key="otheraccesspreferences.id"
    )
    other_access_preferences: Optional["OtherAccessPreferences"] = Relationship(
        back_populates="courses",
    )


class OtherAccessPreferences(SQLModel, table=True):
    """Model for other access preferences of a course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    percentage: int

    courses: List[ShallowCourse] = Relationship(
        back_populates="other_access_preferences",
    )


class CalculationFormula(SQLModel, table=True):
    """Model for the calculation formula of a course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    hs_average: int
    entrance_exams: int


class MinimumClassification(SQLModel, table=True):
    """Model for the minimum classification of a course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    application_grade: int
    entrance_exams: int


class Prerequisites(SQLModel, table=True):
    """Model for the prerequisites of a course."""

    id: Optional[int] = Field(default=None, primary_key=True)

    type: str
    group: str


class CourseData(SQLModel, table=True):
    """Model for a course with its data."""

    id: Optional[int] = Field(default=None, primary_key=True)

    course_id: Optional[str] = Field(default=None, foreign_key="course.id")
    characteristics_id: Optional[int] = Field(
        default=None, foreign_key="characteristics.id"
    )
    year_data_id: Optional[int] = Field(default=None, foreign_key="yeardata.id")
    entrance_exams_id: Optional[int] = Field(
        default=None, foreign_key="entranceexams.id"
    )
    min_classification_id: Optional[int] = Field(
        default=None, foreign_key="minimumclassification.id"
    )
    calculation_formula_id: Optional[int] = Field(
        default=None, foreign_key="calculationformula.id"
    )
    regional_preference_id: Optional[int] = Field(
        default=None, foreign_key="regionalpreference.id"
    )
    other_access_preferences_id: Optional[int] = Field(
        default=None, foreign_key="otheraccesspreferences.id"
    )
    prerequisites_id: Optional[int] = Field(
        default=None, foreign_key="prerequisites.id"
    )

    course: Course = Relationship()
    characteristics: Characteristics = Relationship()
    year_data: List[YearData] = Relationship(
        back_populates="course_data",
        sa_relationship_kwargs={"foreign_keys": "[YearData.course_data_id]"},
    )
    entrance_exams: Optional[EntranceExams] = Relationship()
    min_classification: Optional[MinimumClassification] = Relationship()
    calculation_formula: Optional[CalculationFormula] = Relationship()
    regional_preference: Optional[RegionalPreference] = Relationship()
    other_access_preferences: Optional[OtherAccessPreferences] = Relationship()
    prerequisites: Optional[Prerequisites] = Relationship()

    extra_stats_url: Optional[str]


class Database(SQLModel):
    """Model for the database."""

    courses: List["CourseData"]
