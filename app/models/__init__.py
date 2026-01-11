"""
Модели данных для финансового карьерного коуча

Модели - это структуры данных, которые используются в API.
Они определяют, какие данные принимает и возвращает API.
"""

from app.models.schemas import (
    Message,
    MessageRole,
    Session,
    SessionState,
    CreateSessionRequest,
    CreateSessionResponse,
    GetSessionResponse,
    ListSessionsResponse,
    SessionListItem,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    UserProfile,
    ProfileResponse,
    ProfessionalContext,
    Skills,
    ResumeItem,
    CourseItem,
    Goals,
    Preferences,
    SalaryExpectation,
)

from app.models.match_models import (
    MatchedVacancy,
    MatchVacanciesRequest,
    MatchVacanciesBySessionRequest,
    MatchVacanciesResponse,
    MatchedCourse,
    MatchCoursesRequest,
    MatchCoursesResponse,
    CareerDevelopmentRequest,
    CareerDevelopmentResponse,
)

__all__ = [
    "Message",
    "MessageRole",
    "Session",
    "SessionState",
    "CreateSessionRequest",
    "CreateSessionResponse",
    "GetSessionResponse",
    "ListSessionsResponse",
    "SessionListItem",
    "ChatRequest",
    "ChatResponse",
    "HealthResponse",
    "UserProfile",
    "ProfileResponse",
    "ProfessionalContext",
    "Skills",
    "ResumeItem",
    "CourseItem",
    "Goals",
    "Preferences",
    "SalaryExpectation",
    "MatchedVacancy",
    "MatchVacanciesRequest",
    "MatchVacanciesBySessionRequest",
    "MatchVacanciesResponse",
    "MatchedCourse",
    "MatchCoursesRequest",
    "MatchCoursesResponse",
    "CareerDevelopmentRequest",
    "CareerDevelopmentResponse",
]










