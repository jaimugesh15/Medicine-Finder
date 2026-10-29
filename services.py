"""Business logic shared by the routes: stock summary, activity log, search, distance."""
from collections import Counter
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import func

from extensions import db
from models import InventoryActivity, Medicine, Pharmacy, now

FIELDS = ["name", "category", "strength", "dosage_form", "manufacturer",
          "quantity", "reorder_level", "verified", "notes"]


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two coordinates in kilometres."""
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def summary(pharmacy_id):
    """All dashboard numbers are calculated here from the database."""
    meds = Medicine.query.filter_by(pharmacy_id=pharmacy_id).all()
    c = Counter(m.status for m in meds)
    return {"total": len(meds), "low": c["low"], "out": c["out"], "unknown": c["unknown"],
            "available_items": c["available"],
            "available": len({m.name.lower() for m in meds if m.status == "available"})}


def category_distribution(pharmacy_id):
    rows = (db.session.query(Medicine.category, func.count(Medicine.id))
            .filter_by(pharmacy_id=pharmacy_id).group_by(Medicine.category).all())
    return sorted(rows, key=lambda r: -r[1])


def duplicate_exists(pharmacy_id, name, strength, form, exclude_id=None):
    q = Medicine.query.filter(Medicine.pharmacy_id == pharmacy_id,
                              func.lower(Medicine.name) == name.strip().lower(),
                              Medicine.strength == (strength or "").strip(),
                              Medicine.dosage_form == (form or ""))
    if exclude_id:
        q = q.filter(Medicine.id != exclude_id)
    return db.session.query(q.exists()).scalar()


def _log(pharmacy_id, med, action, prev, cur, user):
    db.session.add(InventoryActivity(pharmacy_id=pharmacy_id, medicine_id=med.id,
                                     medicine_name=med.display_name, action=action,
                                     previous_status=prev, current_status=cur, user_id=user.id))


def _apply(med, data):
    for f in FIELDS:
        value = data[f]
        if isinstance(value, str):
            value = value.strip()
        setattr(med, f, value)
    med.strength = med.strength or ""
    med.dosage_form = med.dosage_form or ""
    if med.verified:
        med.last_verified_at = now()


def create_medicine(pharmacy, data, user):
    med = Medicine(pharmacy_id=pharmacy.id)
    _apply(med, data)
    db.session.add(med)
    db.session.flush()                      # gives the new row an id for the log
    _log(pharmacy.id, med, "Added", None, med.status, user)
    db.session.commit()
    return med


def update_medicine(med, data, user):
    prev = med.status
    _apply(med, data)
    _log(med.pharmacy_id, med, "Updated", prev, med.status, user)
    db.session.commit()


def set_quantity(med, quantity, verified, user):
    prev = med.status
    med.quantity, med.verified = quantity, verified
    if verified:
        med.last_verified_at = now()
    med.updated_at = now()
    _log(med.pharmacy_id, med, "Stock updated", prev, med.status, user)
    db.session.commit()


def delete_medicine(med, user):
    _log(med.pharmacy_id, med, "Deleted", med.status, None, user)
    db.session.delete(med)
    db.session.commit()


def search_inventory(q="", city="", status="", lat=None, lng=None, radius=None, sort="medicine"):
    """Public search: returns (medicine, pharmacy, distance_km or None) tuples."""
    query = Medicine.query.join(Pharmacy)
    if q:
        like = f"%{q}%"
        query = query.filter(Medicine.name.ilike(like) | Pharmacy.name.ilike(like)
                             | Pharmacy.city.ilike(like))
    if city:
        query = query.filter(Pharmacy.city.ilike(f"%{city}%") | Pharmacy.address.ilike(f"%{city}%"))
    cond = Medicine.status_filter(status) if status else None
    if cond is not None:
        query = query.filter(cond)
    results = []
    for m in query.limit(300).all():
        p = m.pharmacy
        dist = None
        if lat is not None and lng is not None and p.has_coordinates:
            dist = haversine_km(lat, lng, p.latitude, p.longitude)
        if radius and (dist is None or dist > radius):
            continue
        results.append((m, p, dist))
    if sort == "distance" and lat is not None:
        results.sort(key=lambda r: (r[2] is None, r[2] or 0))
    elif sort == "pharmacy":
        results.sort(key=lambda r: (r[1].name.lower(), r[0].name.lower()))
    else:
        results.sort(key=lambda r: (r[0].name.lower(), r[1].name.lower()))
    return results
