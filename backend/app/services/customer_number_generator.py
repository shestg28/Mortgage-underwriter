from sqlalchemy.dialects.postgresql import insert
from app.models import CustomerNumberSequence
from sqlalchemy.orm import Session

PREFIX_RULES = [
    (200000, 'AA'),
    (150000, 'AB'),
    (100000, 'BA'),
    (50000, 'BB'),
    (0, 'CA'),
]


def determine_prefix(salary: float | None) -> str:
    if salary is None:
        return 'CA'
    for threshold, prefix in PREFIX_RULES:
        if salary > threshold:
            return prefix
    return 'CA'


def format_customer_number(prefix: str, sequence: int) -> str:
    return f"{prefix}{sequence:05d}"


def generate_customer_number(db: Session, salary: float | None) -> str:
    prefix = determine_prefix(salary)
    stmt = insert(CustomerNumberSequence).values(prefix=prefix, last_sequence=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=[CustomerNumberSequence.prefix],
        set_={"last_sequence": CustomerNumberSequence.last_sequence + 1},
    ).returning(CustomerNumberSequence.last_sequence)

    result = db.execute(stmt)
    sequence = result.scalar_one()
    return format_customer_number(prefix, sequence)
