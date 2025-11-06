#profile routes provied endpoints to manage user-profile and lvas

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from collections import defaultdict
from ..models import (
    UserProfile, UserProfileUpdate,
    LVA, LVAModule, LVAHierarchyResponse,
    CompletedLVAsUpdate
)
from ..db import init_db_pool
from ..routes.planning_routes import get_current_user_email
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
    dependencies=[Depends(oauth2_scheme)]
)

# ========== Helper Functions ==========

async def get_user_id_by_email(email: str) -> int:
    """Holt die User-ID anhand der Email"""
    pool = await init_db_pool()
    async with pool.acquire() as conn:
        user_id = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            email
        )
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        return user_id

# ========== API Endpoints ==========

@router.get("/me", response_model=UserProfile)
async def get_my_profile(user_email: str = Depends(get_current_user_email)):
    """
    Gibt das Profil des eingeloggten Users zurück.
    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, username, email, studiengang
            FROM users
            WHERE email = $1
            """,
            user_email
        )

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        studiengang=row["studiengang"] or "Bachelor Wirtschaftsinformatik"
    )


@router.put("/me", response_model=UserProfile)
async def update_my_profile(
        profile_data: UserProfileUpdate,
        user_email: str = Depends(get_current_user_email)
):
    """
    Aktualisiert das Profil des eingeloggten Users.
    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        # Baue dynamisches UPDATE Statement
        update_fields = []
        params = []
        param_count = 1

        if profile_data.username is not None:
            update_fields.append(f"username = ${param_count}")
            params.append(profile_data.username)
            param_count += 1

        if profile_data.email is not None:
            #check if email existis already
            email_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1 AND email != $2)",
                profile_data.email,
                user_email
            )
            if email_exists:
                raise HTTPException(status_code=400, detail="Email already in use")

            update_fields.append(f"email = ${param_count}")
            params.append(profile_data.email)
            param_count += 1

        if profile_data.studiengang is not None:
            update_fields.append(f"studiengang = ${param_count}")
            params.append(profile_data.studiengang)
            param_count += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # WHERE-Bclause
        params.append(user_email)
        where_clause = f"WHERE email = ${param_count}"

        # run update
        query = f"UPDATE users SET {', '.join(update_fields)} {where_clause}"
        await conn.execute(query, *params)

        # get updated data
        row = await conn.fetchrow(
            "SELECT id, username, email, studiengang FROM users WHERE email = $1",
            profile_data.email if profile_data.email else user_email
        )

    return UserProfile(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        studiengang=row["studiengang"] or "Bachelor Wirtschaftsinformatik"
    )


@router.get("/pflichfächer", response_model=LVAHierarchyResponse)
async def get_pflichtfaecher(user_email: str = Depends(get_current_user_email)):
    """
    Returns only Pflichtfächer hierarchy.
    Completed lvas will be marked with boolean = true

    Hierarchy:
    - Level 1: Modules (e.g. "Grundlagen der Wirtschaftsinformatik")
    - Level 2: Single LVAs (e.g. "VL Einführung in die Wirtschaftsinformatik")
    """

    pool = await init_db_pool()
    user_id = await get_user_id_by_email(user_email)

    async with pool.acquire() as conn:
        # get only Pflichtfächer
        lva_rows = await conn.fetch(
            """
            SELECT id, hierarchielevel0, hierarchielevel1, hierarchielevel2,
                   type, name, ects
            FROM lvas
            WHERE hierarchielevel0 = 'Pflichtfach'
            ORDER BY hierarchielevel1, hierarchielevel2, type
            """
        )

        # fetch completed_lvas for user to provide boolean to frontend
        completed_lva_ids = await conn.fetch(
            "SELECT lva_id FROM completed_lvas WHERE user_id = $1",
            user_id
        )
        completed_set = {row["lva_id"] for row in completed_lva_ids}

    # organize lvas into hierarchy
    pflichtfaecher_dict: Dict[str, List[LVA]] = defaultdict(list)

    for row in lva_rows:
        lva = LVA(
            id=row["id"],
            hierarchielevel0=row["hierarchielevel0"],
            hierarchielevel1=row["hierarchielevel1"],
            hierarchielevel2=row["hierarchielevel2"],
            type=row["type"],
            name=row["name"],
            ects=row["ects"],
            is_completed=(row["id"] in completed_set)
        )
        pflichtfaecher_dict[row["hierarchielevel1"]].append(lva)

    # create modules
    pflichtfach_modules = []
    for module_name, lvas in pflichtfaecher_dict.items():
        total_ects = sum(lva.ects for lva in lvas)
        pflichtfach_modules.append(
            LVAModule(
                module_name=module_name,
                lvas=lvas,
                total_ects=total_ects
            )
        )

    return LVAHierarchyResponse(
        pflichtfaecher=pflichtfach_modules,
    )

@router.get("/wahlfaecher", response_model=LVAHierarchyResponse)
async def get_wahlfaecher(user_email: str = Depends(get_current_user_email)):
    """
    Returns only Wahlfächer hierarchy.
    Completed lvas will be marked with boolean = true

    Hierarchy:
    - Level 1: Modules (e.g. "Grundlagen der Volkswirtschaftslehre")
    - Level 2: Single LVAs (e.g. "VL Einführung in die VWL")
    """

    pool = await init_db_pool()
    user_id = await get_user_id_by_email(user_email)

    async with pool.acquire() as conn:
        # get only Wahlfächer
        lva_rows = await conn.fetch(
            """
            SELECT id, hierarchielevel0, hierarchielevel1, hierarchielevel2,
                   type, name, ects
            FROM lvas
            WHERE hierarchielevel0 = 'Wahlfach'
            ORDER BY hierarchielevel1, hierarchielevel2, type
            """
        )

        # fetch completed_lvas for user to provide boolean to frontend
        completed_lva_ids = await conn.fetch(
            "SELECT lva_id FROM completed_lvas WHERE user_id = $1",
            user_id
        )
        completed_set = {row["lva_id"] for row in completed_lva_ids}

    # organize lvas into hierarchy
    wahlfaecher_dict: Dict[str, List[LVA]] = defaultdict(list)

    for row in lva_rows:
        lva = LVA(
            id=row["id"],
            hierarchielevel0=row["hierarchielevel0"],
            hierarchielevel1=row["hierarchielevel1"],
            hierarchielevel2=row["hierarchielevel2"],
            type=row["type"],
            name=row["name"],
            ects=row["ects"],
            is_completed=(row["id"] in completed_set)
        )
        wahlfaecher_dict[row["hierarchielevel1"]].append(lva)

    # create modules
    wahlfach_modules = []
    for module_name, lvas in wahlfaecher_dict.items():
        total_ects = sum(lva.ects for lva in lvas)
        wahlfach_modules.append(
            LVAModule(
                module_name=module_name,
                lvas=lvas,
                total_ects=total_ects
            )
        )

    return LVAHierarchyResponse(
        wahlfaecher=wahlfach_modules
    )


@router.get("/lvas/completed", response_model=List[int])
async def get_completed_lvas(user_email: str = Depends(get_current_user_email)):
    """
    Gibt nur die IDs der abgeschlossenen LVAs zurück.
    Nützlich für schnelle Checks im Frontend.
    """
    pool = await init_db_pool()
    user_id = await get_user_id_by_email(user_email)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT lva_id FROM completed_lvas WHERE user_id = $1",
            user_id
        )

    return [row["lva_id"] for row in rows]


@router.put("/lvas/completed")
async def update_completed_lvas(
        data: CompletedLVAsUpdate,
        user_email: str = Depends(get_current_user_email)
):
    """
    Update completed lvas - only entries who have been edited
    will be updated (either if checkbox was checked or check
    was removed.
    """
    pool = await init_db_pool()
    user_id = await get_user_id_by_email(user_email)

    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. get everything completed from user
            current_completed = await conn.fetch(
                "SELECT lva_id FROM completed_lvas WHERE user_id = $1",
                user_id
            )
            current_set = {row["lva_id"] for row in current_completed}
            new_set = set(data.lva_ids)

            # 2. calculate differences
            to_add = new_set - current_set
            to_remove = current_set - new_set

            # 3. delete entries if no longer valid
            if to_remove:
                await conn.execute(
                    "DELETE FROM completed_lvas WHERE user_id = $1 AND lva_id = ANY($2)",
                    user_id, list(to_remove)
                )

            # 4. add new entries
            if to_add:
                values = [(user_id, lva_id) for lva_id in to_add]
                await conn.executemany(
                    "INSERT INTO completed_lvas (user_id, lva_id) VALUES ($1, $2)",
                    values
                )

    return {
        "status": "success",
        "message": f"{len(to_add)} LVAs hinzugefügt, {len(to_remove)} entfernt",
        "added": len(to_add),
        "removed": len(to_remove),
        "total_completed": len(data.lva_ids)
    }

