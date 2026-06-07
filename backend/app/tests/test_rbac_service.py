from app.models.common import WorkspaceRole
from app.services.rbac_service import ROLE_ORDER, can_manage_users


def test_role_order_prevents_viewer_from_project_mutation() -> None:
    assert ROLE_ORDER[WorkspaceRole.viewer] < ROLE_ORDER[WorkspaceRole.developer]


def test_admin_cannot_manage_owner() -> None:
    assert can_manage_users(WorkspaceRole.admin, WorkspaceRole.owner) is False


def test_owner_can_manage_owner() -> None:
    assert can_manage_users(WorkspaceRole.owner, WorkspaceRole.owner) is True

