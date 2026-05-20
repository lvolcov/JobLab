"""Mount one CRUD router per wiki entity under /wiki/<resource>."""

from __future__ import annotations

from fastapi import APIRouter

from joblab_api.wiki.crud import make_owner_router
from joblab_api.wiki.models import (
    WikiCV,
    WikiEducation,
    WikiExperience,
    WikiProject,
    WikiQualification,
    WikiSkill,
)
from joblab_api.wiki.schemas import (
    CVCreate,
    CVRead,
    CVUpdate,
    EducationCreate,
    EducationRead,
    EducationUpdate,
    ExperienceCreate,
    ExperienceRead,
    ExperienceUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    QualificationCreate,
    QualificationRead,
    QualificationUpdate,
    SkillCreate,
    SkillRead,
    SkillUpdate,
)

router = APIRouter(prefix="/wiki")

router.include_router(
    make_owner_router(
        prefix="/cvs",
        tag="wiki:cvs",
        Model=WikiCV,
        CreateSchema=CVCreate,
        UpdateSchema=CVUpdate,
        ReadSchema=CVRead,
    )
)
router.include_router(
    make_owner_router(
        prefix="/education",
        tag="wiki:education",
        Model=WikiEducation,
        CreateSchema=EducationCreate,
        UpdateSchema=EducationUpdate,
        ReadSchema=EducationRead,
        order_by_field="start",
    )
)
router.include_router(
    make_owner_router(
        prefix="/qualifications",
        tag="wiki:qualifications",
        Model=WikiQualification,
        CreateSchema=QualificationCreate,
        UpdateSchema=QualificationUpdate,
        ReadSchema=QualificationRead,
        order_by_field="date_awarded",
    )
)
router.include_router(
    make_owner_router(
        prefix="/skills",
        tag="wiki:skills",
        Model=WikiSkill,
        CreateSchema=SkillCreate,
        UpdateSchema=SkillUpdate,
        ReadSchema=SkillRead,
    )
)
router.include_router(
    make_owner_router(
        prefix="/projects",
        tag="wiki:projects",
        Model=WikiProject,
        CreateSchema=ProjectCreate,
        UpdateSchema=ProjectUpdate,
        ReadSchema=ProjectRead,
        order_by_field="start",
    )
)
router.include_router(
    make_owner_router(
        prefix="/experiences",
        tag="wiki:experiences",
        Model=WikiExperience,
        CreateSchema=ExperienceCreate,
        UpdateSchema=ExperienceUpdate,
        ReadSchema=ExperienceRead,
        order_by_field="start",
    )
)
