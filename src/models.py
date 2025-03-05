from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# 模組與分類的多對多關聯表
mod_category = Table(
    "mod_category",
    Base.metadata,
    Column("mod_id", Integer, ForeignKey("mods.id")),
    Column("category_id", Integer, ForeignKey("categories.id")),
)

# 模組與前置的多對多關聯表
mod_dependency = Table(
    "mod_dependency",
    Base.metadata,
    Column("mod_id", Integer, ForeignKey("mods.id")),
    Column("dependency_id", Integer, ForeignKey("mods.id")),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    mods: Mapped[list["Mod"]] = relationship(secondary=mod_category, back_populates="categories")


class Mod(Base):
    __tablename__ = "mods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    is_translated: Mapped[bool] = mapped_column(Boolean, default=False)
    client_required: Mapped[bool] = mapped_column(Boolean, default=True)
    server_required: Mapped[bool] = mapped_column(Boolean, default=True)
    filename: Mapped[str] = mapped_column(String)

    # 關聯
    categories: Mapped[list[Category]] = relationship(secondary=mod_category, back_populates="mods")
    dependencies: Mapped[list["Mod"]] = relationship(
        secondary=mod_dependency,
        primaryjoin=(id == mod_dependency.c.mod_id),
        secondaryjoin=(id == mod_dependency.c.dependency_id),
        backref="dependent_mods",
    )
