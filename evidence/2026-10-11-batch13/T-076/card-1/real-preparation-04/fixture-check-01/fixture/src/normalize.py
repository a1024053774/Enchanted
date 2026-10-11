def normalize(rows):
    totals = {}
    for row in rows:
        name, minutes = row.get("name"), row.get("minutes")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid_name")
        if not isinstance(minutes, int) or minutes < 0:
            raise ValueError("invalid_minutes")
        name = name.strip(); totals[name] = totals.get(name, 0) + minutes
    return {"entries": [{"name": name, "minutes": totals[name]} for name in sorted(totals)],
            "total_minutes": sum(totals.values())}
