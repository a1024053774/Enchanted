"""Return a page of records ordered by timestamp and ID."""
import json
import sys


def paginate(request):
    limit = request["limit"]
    if type(limit) is not int or not 1 <= limit <= 100:
        return {"error": "invalid_limit"}

    after = request.get("after")
    if after is not None:
        if (
            not isinstance(after, list)
            or len(after) != 2
            or type(after[0]) is not int
            or not isinstance(after[1], str)
        ):
            return {"error": "invalid_cursor"}
        after = tuple(after)

    ordered = sorted(request["items"], key=lambda item: (item["ts"], item["id"]))
    eligible = [
        item for item in ordered
        if after is None or (item["ts"], item["id"]) > after
    ]
    page = eligible[:limit]
    next_cursor = [page[-1]["ts"], page[-1]["id"]] if len(eligible) > limit else None
    return {"items": page, "next_cursor": next_cursor}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    print(json.dumps(paginate(request)))
