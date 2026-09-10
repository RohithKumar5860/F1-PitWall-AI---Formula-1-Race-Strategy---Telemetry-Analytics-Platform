"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-08 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Teams
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('nationality', sa.String(length=50), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=True)

    # 2. Drivers
    op.create_table(
        'drivers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('number', sa.Integer(), nullable=True),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('nationality', sa.String(length=50), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drivers_code'), 'drivers', ['code'], unique=True)

    # 3. Circuits
    op.create_table(
        'circuits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('length_km', sa.Float(), nullable=True),
        sa.Column('lap_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_circuits_name'), 'circuits', ['name'], unique=False)

    # 4. Races
    op.create_table(
        'races',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('event_name', sa.String(length=200), nullable=False),
        sa.Column('circuit_id', sa.Integer(), nullable=True),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['circuit_id'], ['circuits.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_races_event_name'), 'races', ['event_name'], unique=False)
    op.create_index(op.f('ix_races_year'), 'races', ['year'], unique=False)
    op.create_index('ix_race_year_round', 'races', ['year', 'round_number'], unique=False)

    # 5. Lap Times
    op.create_table(
        'lap_times',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('race_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('lap_number', sa.Integer(), nullable=False),
        sa.Column('lap_time_seconds', sa.Float(), nullable=True),
        sa.Column('sector1_seconds', sa.Float(), nullable=True),
        sa.Column('sector2_seconds', sa.Float(), nullable=True),
        sa.Column('sector3_seconds', sa.Float(), nullable=True),
        sa.Column('compound', sa.String(length=20), nullable=True),
        sa.Column('tyre_life', sa.Integer(), nullable=True),
        sa.Column('stint', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_laptime_race_driver', 'lap_times', ['race_id', 'driver_id'], unique=False)

    # 6. Tire Data
    op.create_table(
        'tire_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('race_id', sa.Integer(), nullable=False),
        sa.Column('driver_code', sa.String(length=3), nullable=False),
        sa.Column('lap_number', sa.Integer(), nullable=False),
        sa.Column('stint', sa.Integer(), nullable=True),
        sa.Column('compound', sa.String(length=20), nullable=True),
        sa.Column('tyre_life', sa.Integer(), nullable=True),
        sa.Column('fresh_tyre', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Pit Stops
    op.create_table(
        'pit_stops',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('race_id', sa.Integer(), nullable=False),
        sa.Column('driver_code', sa.String(length=3), nullable=False),
        sa.Column('pit_lap', sa.Integer(), nullable=False),
        sa.Column('stint', sa.Integer(), nullable=True),
        sa.Column('incoming_compound', sa.String(length=20), nullable=True),
        sa.Column('outgoing_compound', sa.String(length=20), nullable=True),
        sa.Column('pit_in_time', sa.Float(), nullable=True),
        sa.Column('pit_out_time', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Weather Records
    op.create_table(
        'weather_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('race_id', sa.Integer(), nullable=False),
        sa.Column('time_offset', sa.Float(), nullable=True),
        sa.Column('air_temp', sa.Float(), nullable=True),
        sa.Column('track_temp', sa.Float(), nullable=True),
        sa.Column('humidity', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Float(), nullable=True),
        sa.Column('rainfall', sa.Boolean(), nullable=True),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('wind_direction', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. Predictions
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('race_id', sa.Integer(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=20), nullable=True),
        sa.Column('prediction_type', sa.String(length=50), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('predictions')
    op.drop_table('weather_records')
    op.drop_table('pit_stops')
    op.drop_table('tire_data')
    op.drop_table('lap_times')
    op.drop_index('ix_race_year_round', table_name='races')
    op.drop_index(op.f('ix_races_year'), table_name='races')
    op.drop_index(op.f('ix_races_event_name'), table_name='races')
    op.drop_table('races')
    op.drop_index(op.f('ix_circuits_name'), table_name='circuits')
    op.drop_table('circuits')
    op.drop_index(op.f('ix_drivers_code'), table_name='drivers')
    op.drop_table('drivers')
    op.drop_index(op.f('ix_teams_name'), table_name='teams')
    op.drop_table('teams')
