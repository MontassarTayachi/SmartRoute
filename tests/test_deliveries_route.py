from flask import Flask

import app.routers.deliveries as deliveries_module


def test_list_deliveries_route_uses_scheduled_at_alias(monkeypatch):
    app = Flask(__name__)
    app.mongodb = object()

    captured = {}

    def fake_list_deliveries(db, *, page, limit, status_filter, date_filter, paginate):
        captured["db"] = db
        captured["page"] = page
        captured["limit"] = limit
        captured["status_filter"] = status_filter
        captured["date_filter"] = date_filter
        captured["paginate"] = paginate
        return {"items": []}

    monkeypatch.setattr(deliveries_module, "list_deliveries", fake_list_deliveries)

    with app.test_request_context("/api/v1/deliveries?paginate=false&scheduled_at=2026-08-05"):
        response, status_code = deliveries_module.list_deliveries_route.__wrapped__()

    assert status_code == 200
    assert response.get_json() == {"items": []}
    assert captured == {
        "db": app.mongodb,
        "page": 1,
        "limit": 20,
        "status_filter": None,
        "date_filter": "2026-08-05",
        "paginate": False,
    }