"""站点改重量/体积的入袋锁定：已入袋禁止修改，未入袋可改，覆盖装袋后锁随新袋。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.models import DeliveryRoute, SubscriberStop


@pytest.fixture()
def env():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = TestingSession()
    route = DeliveryRoute(name="测试线", max_weight_kg=8.0, max_volume_l=18.0)
    db.add(route)
    db.flush()
    s1 = SubscriberStop(route_id=route.id, seq=1, name="甲站", weight_kg=2.0, volume_l=3.0)
    s2 = SubscriberStop(route_id=route.id, seq=2, name="乙站", weight_kg=3.0, volume_l=4.0)
    # 丙站单件超重，首次装袋必被拒收 → 未入袋
    s3 = SubscriberStop(route_id=route.id, seq=3, name="丙站大件", weight_kg=9.5, volume_l=6.0)
    db.add_all([s1, s2, s3])
    db.commit()
    ids = {"route": route.id, "s1": s1.id, "s2": s2.id, "s3": s3.id}
    db.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), ids
    app.dependency_overrides.clear()


def _pack(client: TestClient, route_id: int) -> list[dict]:
    r = client.post("/api/pack", json={"route_id": route_id})
    assert r.status_code == 200
    return r.json()


def _stops_by_id(client: TestClient, route_id: int) -> dict[int, dict]:
    r = client.get(f"/api/stops?route_id={route_id}")
    assert r.status_code == 200
    return {s["id"]: s for s in r.json()}


def test_bagged_stop_weight_change_fails(env):
    client, ids = env
    _pack(client, ids["route"])  # 甲、乙入袋；丙被拒
    assert _stops_by_id(client, ids["route"])[ids["s1"]]["in_bag"] is True

    r = client.patch(f"/api/stops/{ids['s1']}", json={"weight_kg": 5.0, "volume_l": 3.0})
    assert r.status_code == 409
    assert "已入袋" in r.json()["detail"]

    # 提交失败，重量保持原值
    assert _stops_by_id(client, ids["route"])[ids["s1"]]["weight_kg"] == 2.0


def test_unbagged_stop_weight_change_ok(env):
    client, ids = env
    _pack(client, ids["route"])
    assert _stops_by_id(client, ids["route"])[ids["s3"]]["in_bag"] is False

    r = client.patch(f"/api/stops/{ids['s3']}", json={"weight_kg": 2.5, "volume_l": 3.0})
    assert r.status_code == 200
    assert r.json()["weight_kg"] == 2.5
    assert r.json()["in_bag"] is False
    assert _stops_by_id(client, ids["route"])[ids["s3"]]["weight_kg"] == 2.5


def test_repack_after_edit_changes_bags_and_locks_follow(env):
    client, ids = env
    bags1 = _pack(client, ids["route"])
    packed1 = {it["stop_id"] for b in bags1 for it in b["items"]}
    assert ids["s3"] not in packed1  # 大件被拒，未入袋

    # 未入袋站点改重成功
    r = client.patch(f"/api/stops/{ids['s3']}", json={"weight_kg": 2.5, "volume_l": 3.0})
    assert r.status_code == 200

    # 覆盖装袋：旧袋清空重算，开袋结果变化——丙站进入新袋
    bags2 = _pack(client, ids["route"])
    packed2 = {it["stop_id"] for b in bags2 for it in b["items"]}
    assert packed2 != packed1
    assert ids["s3"] in packed2
    assert client.get("/api/rejects").json() == []

    # 锁随新袋：丙站现在已入袋，禁止再改
    stops = _stops_by_id(client, ids["route"])
    assert stops[ids["s3"]]["in_bag"] is True
    r = client.patch(f"/api/stops/{ids['s3']}", json={"weight_kg": 1.0, "volume_l": 1.0})
    assert r.status_code == 409
    assert "已入袋" in r.json()["detail"]


def test_update_missing_stop_404(env):
    client, _ = env
    r = client.patch("/api/stops/9999", json={"weight_kg": 1.0, "volume_l": 1.0})
    assert r.status_code == 404


def test_bag_totals_and_weights_match_persisted_bag_rows(env):
    client, ids = env
    _pack(client, ids["route"])  # 甲(2.0/3.0)、乙(3.0/4.0)入袋，丙被拒

    bags = client.get("/api/bags").json()
    by_id = {b["id"]: b for b in bags}
    for b in bags:
        # 袋明细汇总值必须等于落库袋行之和
        assert round(sum(i["weight_kg"] for i in b["items"]), 3) == b["weight_kg"]
        assert round(sum(i["volume_l"] for i in b["items"]), 3) == b["volume_l"]

    weights = {w["bag_id"]: w for w in client.get("/api/weights").json()}
    assert set(weights) == set(by_id)
    for bag_id, b in by_id.items():
        w = weights[bag_id]
        assert w["weight_kg"] == b["weight_kg"]
        assert w["volume_l"] == b["volume_l"]
        assert w["fill_weight_pct"] == round(100 * b["weight_kg"] / 8.0, 1)
        assert w["fill_volume_pct"] == round(100 * b["volume_l"] / 18.0, 1)

