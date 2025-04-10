"""Pydantic models for the application."""

from typing import Dict, List, Optional

from sqlmodel import SQLModel #, Field, Relationship
#from pydantic import BaseModel


class Courses(SQLModel):
    """Model for a list of courses for a given year."""

    year: int
    courses: List["Course"]


class Institution(SQLModel):
    """Model for an institution."""

    id: str
    name: str

class Course(SQLModel):
    """Model for a course from an institution."""

    id: str
    name: str
    url: str
    institution: Institution
    vacancies: int


class CandidateStats(SQLModel):
    """Model for the candidates statistics."""

    total: Optional[int]
    fem: Optional[int]
    masc: Optional[int]
    first_option: Optional[int]


class Averages(SQLModel):
    """Model for the averages of candidates."""

    application_grade: Optional[float]
    entrance_exams: Optional[float]
    hs_average: Optional[float]


class PhaseData(SQLModel):
    """Model for a phase with its data."""

    vacancies: Optional[int]
    candidates: Optional[CandidateStats]
    placed: Optional[CandidateStats]
    averages: Optional[Averages]
    grade_last: Optional[float]
    info_url: Optional[str]


class YearData(SQLModel):
    """Model for a year with its data."""

    phase1: PhaseData
    phase2: Optional[PhaseData]


class Characteristics(SQLModel):
    """Model for the characteristics of a course."""

    degree: str
    CNAEF: str
    duration: str
    ECTS: int
    type: str
    competition: str
    current_vacancies: Optional[int]


class Exam(SQLModel):
    """Model for an exam."""

    name: str
    code: str


class ExamCombination(SQLModel):
    """Model for a combination of exams."""

    exam1: Exam
    exam2: List[Exam]


class ExamBundle(SQLModel):
    """Model for a bundle of exams."""

    exams: List[Exam]


class EntranceExams(SQLModel):
    """Model for the entrance exams of a course."""

    exams: ExamCombination | ExamBundle | List[ExamBundle]


class RegionalPreference(SQLModel):
    """Model for the regional preference of a course."""

    percentage: float
    regions: List[str]


class OtherAccessPreferences(SQLModel):
    """Model for other access preferences of a course."""

    percentage: int
    courses: List[Dict[str, str]]


class CalculationFormula(SQLModel):
    """Model for the calculation formula of a course."""

    hs_average: int
    entrance_exams: int


class MinimumClassification(SQLModel):
    """Model for the minimum classification of a course."""

    application_grade: int
    entrance_exams: int

class Prerequisites(SQLModel):
    """Model for the prerequisites of a course."""

    type: str
    groups: List[str]


class CourseData(SQLModel):
    """Model for a course with its data."""

    course: Course
    characteristics: Characteristics
    previous_data: Optional[Dict[str, YearData]]
    entrance_exams: Optional[EntranceExams]
    min_classification: Optional[MinimumClassification]
    calculation_formula: Optional[CalculationFormula]
    regional_preference: Optional[RegionalPreference]
    other_access_preferences: Optional[OtherAccessPreferences]
    prerequisites: Optional[Prerequisites]
    extra_stats_url: Optional[str]


class Database(SQLModel):
    """Model for the database."""

    courses: List["CourseData"]
