from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base

def utcnow(): return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = 'organizations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default='')
    instagram: Mapped[str] = mapped_column(String(255), default='')
    events: Mapped[list['Event']] = relationship(back_populates='organization')

class Event(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    venue: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), default='São Luís')
    state: Mapped[str] = mapped_column(String(2), default='MA')
    description: Mapped[str] = mapped_column(Text, default='')
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    champion_prize: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runner_up_prize: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registration: Mapped[str] = mapped_column(String(160), default='')
    free: Mapped[bool] = mapped_column(Boolean, default=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    cover_url: Mapped[str] = mapped_column(String(512), default='')
    organization: Mapped['Organization'] = relationship(back_populates='events')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class MC(Base):
    __tablename__ = 'mcs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    stage_name: Mapped[str] = mapped_column(String(140))
    bio: Mapped[str] = mapped_column(Text, default='')
    instagram: Mapped[str] = mapped_column(String(255), default='')
    photo_url: Mapped[str] = mapped_column(String(512), default='')
    city: Mapped[str] = mapped_column(String(100), default='São Luís')
    published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    participations: Mapped[list['Participation']] = relationship(back_populates='mc', cascade='all, delete-orphan')

class Participation(Base):
    __tablename__ = 'participations'
    __table_args__ = (UniqueConstraint('event_id', 'mc_id', name='unique_event_mc'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'))
    mc_id: Mapped[int] = mapped_column(ForeignKey('mcs.id'))
    placement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mc: Mapped['MC'] = relationship(back_populates='participations')
