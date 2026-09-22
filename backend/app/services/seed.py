from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import DeliveryRoute, SubscriberStop


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(DeliveryRoute.id).limit(1)):
        return
    r1 = DeliveryRoute(name="城东晨线", max_weight_kg=8.0, max_volume_l=18.0)
    r2 = DeliveryRoute(name="园区午线", max_weight_kg=6.0, max_volume_l=14.0)
    db.add_all([r1, r2])
    db.flush()
    db.add_all(
        [
            SubscriberStop(route_id=r1.id, seq=1, name="松林里 3 栋", weight_kg=2.2, volume_l=4.0),
            SubscriberStop(route_id=r1.id, seq=2, name="梧桐苑门岗", weight_kg=3.5, volume_l=5.5),
            SubscriberStop(route_id=r1.id, seq=3, name="地铁口快递柜", weight_kg=1.8, volume_l=3.0),
            SubscriberStop(route_id=r1.id, seq=4, name="超大件样例", weight_kg=9.5, volume_l=6.0),
            SubscriberStop(route_id=r1.id, seq=5, name="咖啡店后门", weight_kg=2.0, volume_l=4.5),
            SubscriberStop(route_id=r2.id, seq=1, name="A 座前台", weight_kg=1.5, volume_l=3.0),
            SubscriberStop(route_id=r2.id, seq=2, name="B 座茶水间", weight_kg=2.0, volume_l=4.0),
            SubscriberStop(route_id=r2.id, seq=3, name="地下车库岗亭", weight_kg=2.8, volume_l=5.0),
        ]
    )
    db.commit()
