from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import BagItem, DeliveryRoute, PackBag, RejectRecord, SubscriberStop
from app.schemas.schemas import (
    BagItemOut,
    BagOut,
    PackRequest,
    RejectOut,
    RouteOut,
    StopOut,
    StopUpdate,
    WeightOut,
)
from app.services.pack_engine import StopItem, pack_route

api_router = APIRouter()


@api_router.get("/health")
def health():
    return {"status": "ok"}


@api_router.get("/routes", response_model=list[RouteOut])
def routes(db: Session = Depends(get_db)):
    return db.scalars(select(DeliveryRoute).order_by(DeliveryRoute.id)).all()


@api_router.get("/stops", response_model=list[StopOut])
def stops(route_id: int | None = None, db: Session = Depends(get_db)):
    q = select(SubscriberStop).order_by(SubscriberStop.route_id, SubscriberStop.seq)
    if route_id is not None:
        q = q.where(SubscriberStop.route_id == route_id)
    bagged_ids = set(db.scalars(select(BagItem.stop_id)).all())
    return [
        StopOut(
            id=s.id,
            route_id=s.route_id,
            seq=s.seq,
            name=s.name,
            weight_kg=s.weight_kg,
            volume_l=s.volume_l,
            in_bag=s.id in bagged_ids,
        )
        for s in db.scalars(q).all()
    ]


@api_router.patch("/stops/{stop_id}", response_model=StopOut)
def update_stop(stop_id: int, body: StopUpdate, db: Session = Depends(get_db)):
    stop = db.get(SubscriberStop, stop_id)
    if not stop:
        raise HTTPException(404, "订户点不存在")
    bagged = db.scalar(select(BagItem.id).where(BagItem.stop_id == stop.id).limit(1))
    if bagged is not None:
        # 已入袋：袋行记录的是装袋时的快照，改主表会让袋明细/袋重失配，直接拒绝
        raise HTTPException(409, f"订户点「{stop.name}」已入袋，禁止修改重量或体积")
    stop.weight_kg = body.weight_kg
    stop.volume_l = body.volume_l
    db.commit()
    db.refresh(stop)
    return StopOut(
        id=stop.id,
        route_id=stop.route_id,
        seq=stop.seq,
        name=stop.name,
        weight_kg=stop.weight_kg,
        volume_l=stop.volume_l,
        in_bag=False,
    )


@api_router.post("/pack", response_model=list[BagOut])
def pack(body: PackRequest, db: Session = Depends(get_db)):
    route = db.get(DeliveryRoute, body.route_id)
    if not route:
        raise HTTPException(404, "路线不存在")
    # clear previous pack for route
    old_bags = db.scalars(select(PackBag).where(PackBag.route_id == route.id)).all()
    for b in old_bags:
        for it in list(b.items):
            db.delete(it)
        db.delete(b)
    old_rej = db.scalars(select(RejectRecord).where(RejectRecord.route_id == route.id)).all()
    for r in old_rej:
        db.delete(r)
    db.flush()

    stops = db.scalars(
        select(SubscriberStop).where(SubscriberStop.route_id == route.id).order_by(SubscriberStop.seq)
    ).all()
    items = [
        StopItem(s.id, s.seq, s.weight_kg, s.volume_l, s.name) for s in stops
    ]
    result = pack_route(items, route.max_weight_kg, route.max_volume_l)
    out_bags: list[PackBag] = []
    for bag in result.bags:
        row = PackBag(
            route_id=route.id,
            bag_index=bag.bag_index,
            weight_kg=round(bag.weight_kg, 3),
            volume_l=round(bag.volume_l, 3),
        )
        db.add(row)
        db.flush()
        for it in bag.items:
            db.add(
                BagItem(
                    bag_id=row.id,
                    stop_id=it.stop_id,
                    stop_name=it.label,
                    weight_kg=it.weight_kg,
                    volume_l=it.volume_l,
                )
            )
        out_bags.append(row)
    for stop, reason in result.rejects:
        db.add(
            RejectRecord(
                route_id=route.id,
                stop_id=stop.stop_id,
                stop_name=stop.label,
                reason=reason,
            )
        )
    db.commit()
    out = []
    for b in out_bags:
        items = [
            BagItemOut(
                stop_id=i.stop_id,
                stop_name=i.stop_name,
                weight_kg=i.weight_kg,
                volume_l=i.volume_l,
            )
            for i in db.scalars(select(BagItem).where(BagItem.bag_id == b.id)).all()
        ]
        out.append(
            BagOut(
                id=b.id,
                route_id=b.route_id,
                bag_index=b.bag_index,
                weight_kg=round(sum(i.weight_kg for i in items), 3),
                volume_l=round(sum(i.volume_l for i in items), 3),
                items=items,
            )
        )
    return out


@api_router.get("/bags", response_model=list[BagOut])
def bags(db: Session = Depends(get_db)):
    rows = db.scalars(select(PackBag).order_by(PackBag.route_id, PackBag.bag_index)).all()
    out = []
    for b in rows:
        items = db.scalars(select(BagItem).where(BagItem.bag_id == b.id)).all()
        out.append(
            BagOut(
                id=b.id,
                route_id=b.route_id,
                bag_index=b.bag_index,
                weight_kg=round(sum(i.weight_kg for i in items), 3),
                volume_l=round(sum(i.volume_l for i in items), 3),
                items=[
                    BagItemOut(
                        stop_id=i.stop_id,
                        stop_name=i.stop_name,
                        weight_kg=i.weight_kg,
                        volume_l=i.volume_l,
                    )
                    for i in items
                ],
            )
        )
    return out


@api_router.get("/rejects", response_model=list[RejectOut])
def rejects(db: Session = Depends(get_db)):
    return db.scalars(select(RejectRecord).order_by(RejectRecord.id.desc())).all()


@api_router.get("/weights", response_model=list[WeightOut])
def weights(db: Session = Depends(get_db)):
    bags = db.scalars(select(PackBag).order_by(PackBag.id)).all()
    out = []
    for b in bags:
        route = db.get(DeliveryRoute, b.route_id)
        assert route
        # 与袋明细同源：填充比按落库袋行聚合，不读可能陈旧的 PackBag 汇总列
        items = db.scalars(select(BagItem).where(BagItem.bag_id == b.id)).all()
        weight = round(sum(i.weight_kg for i in items), 3)
        volume = round(sum(i.volume_l for i in items), 3)
        out.append(
            WeightOut(
                bag_id=b.id,
                bag_index=b.bag_index,
                route_id=b.route_id,
                weight_kg=weight,
                volume_l=volume,
                fill_weight_pct=round(100 * weight / route.max_weight_kg, 1),
                fill_volume_pct=round(100 * volume / route.max_volume_l, 1),
            )
        )
    return out
