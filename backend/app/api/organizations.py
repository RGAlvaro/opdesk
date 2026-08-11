"""HTTP endpoints for organizations, tenant membership, and role management."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.schemas.organizations import (
    MembershipListResponse,
    MembershipRead,
    MembershipRoleUpdateRequest,
    MembershipUserRead,
    OrganizationCreateRequest,
    OrganizationListResponse,
    OrganizationRead,
    OrganizationUpdateRequest,
    OwnershipTransferRequest,
)
from app.services.organizations import OrganizationService

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


def organization_read(
    organization: Organization, membership: OrganizationMembership
) -> OrganizationRead:
    """Combine persisted organization fields with the requesting user's role."""
    return OrganizationRead(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        role=membership.role,
        employee_count=organization.employee_count,
        industry=organization.industry,
        website=organization.website,
        contact_email=organization.contact_email,
        phone=organization.phone,
        address_line1=organization.address_line1,
        address_line2=organization.address_line2,
        city=organization.city,
        region=organization.region,
        postal_code=organization.postal_code,
        country=organization.country,
        tax_id=organization.tax_id,
        logo_url=organization.logo_url,
        description=organization.description,
        created_at=organization.created_at,
        updated_at=organization.updated_at,
    )


def membership_read(membership: OrganizationMembership, user: User) -> MembershipRead:
    """Build a membership response containing only safe user fields."""
    return MembershipRead(
        id=membership.id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        role=membership.role,
        user=MembershipUserRead.model_validate(user),
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


@router.post("", response_model=OrganizationRead, status_code=201)
def create_organization(
    payload: OrganizationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationRead:
    """Create a tenant workspace owned by the authenticated user."""
    organization, membership = OrganizationService(db).create_organization(
        current_user,
        name=payload.name,
        fields_set=payload.model_fields_set,
        metadata=payload.model_dump(),
    )
    return organization_read(organization, membership)


@router.get("", response_model=OrganizationListResponse)
def list_organizations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OrganizationListResponse:
    """List the authenticated user's organizations with standard pagination."""
    rows, total = OrganizationService(db).list_organizations(current_user, limit, offset)
    return OrganizationListResponse(
        items=[organization_read(organization, membership) for organization, membership in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{organization_id}", response_model=OrganizationRead)
def get_organization(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationRead:
    """Return an organization only when the authenticated user is a member."""
    organization, membership = OrganizationService(db).get_organization(
        current_user, organization_id
    )
    return organization_read(organization, membership)


@router.patch("/{organization_id}", response_model=OrganizationRead)
def update_organization(
    organization_id: uuid.UUID,
    payload: OrganizationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationRead:
    """Update organization identity fields when the actor is an owner."""
    organization, membership = OrganizationService(db).update_organization(
        current_user,
        organization_id,
        payload.name,
        fields_set=payload.model_fields_set,
        metadata=payload.model_dump(),
    )
    return organization_read(organization, membership)


@router.delete("/{organization_id}", status_code=204)
def delete_organization(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Permanently delete an organization when requested by its owner."""
    OrganizationService(db).delete_organization(current_user, organization_id)
    return Response(status_code=204)


@router.get("/{organization_id}/members", response_model=MembershipListResponse)
def list_members(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MembershipListResponse:
    """List tenant memberships for an owner or admin."""
    rows, total = OrganizationService(db).list_members(current_user, organization_id, limit, offset)
    return MembershipListResponse(
        items=[membership_read(membership, user) for membership, user in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch("/{organization_id}/members/{user_id}", response_model=MembershipRead)
def change_member_role(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: MembershipRoleUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MembershipRead:
    """Replace a member's role when requested by an organization owner."""
    membership, user = OrganizationService(db).change_member_role(
        current_user, organization_id, user_id, payload.role
    )
    return membership_read(membership, user)


@router.delete("/{organization_id}/members/{user_id}", status_code=204)
def remove_member(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Remove a tenant membership while retaining its user account."""
    OrganizationService(db).remove_member(current_user, organization_id, user_id)
    return Response(status_code=204)


@router.post("/{organization_id}/transfer-ownership", status_code=204)
def transfer_ownership(
    organization_id: uuid.UUID,
    payload: OwnershipTransferRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Transfer the sole owner role to an existing organization member."""
    OrganizationService(db).transfer_ownership(
        current_user, organization_id, payload.new_owner_user_id
    )
    return Response(status_code=204)
