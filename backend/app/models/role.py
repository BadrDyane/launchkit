# launchkit/backend/app/models/role.py
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Role(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # owner=100, admin=50, member=10
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    # relationships
    memberships: Mapped[list["OrgMembership"]] = relationship(
        "OrgMembership", back_populates="role"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="role"
    )

    def __repr__(self) -> str:
        return f"<Role name={self.name} level={self.level}>"