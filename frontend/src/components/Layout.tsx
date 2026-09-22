import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { api } from "../api/client";

const stripLinks = [
  ["/pack", "装袋"],
  ["/routes", "路线"],
  ["/stops", "站点"],
  ["/bags", "袋明细"],
  ["/rejects", "拒收"],
  ["/weights", "袋重"],
];

type Stop = { id: number; route_id: number; seq: number; name: string; weight_kg: number; volume_l: number };
type Route = { id: number; name: string };
type Weight = {
  bag_id: number;
  bag_index: number;
  route_id: number;
  weight_kg: number;
  volume_l: number;
  fill_weight_pct: number;
  fill_volume_pct: number;
};

export default function Layout() {
  const loc = useLocation();
  const [routes, setRoutes] = useState<Route[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [stops, setStops] = useState<Stop[]>([]);
  const [weights, setWeights] = useState<Weight[]>([]);

  useEffect(() => {
    api<Route[]>("/routes").then((r) => {
      setRoutes(r);
      if (r[0]) setRid(r[0].id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (rid === "") return;
    api<Stop[]>(`/stops?route_id=${rid}`).then(setStops).catch(() => setStops([]));
  }, [rid, loc.pathname]);

  useEffect(() => {
    api<Weight[]>("/weights").then(setWeights).catch(() => setWeights([]));
    const t = setInterval(() => {
      api<Weight[]>("/weights").then(setWeights).catch(() => {});
    }, 10000);
    return () => clearInterval(t);
  }, [loc.pathname]);

  const meters = useMemo(() => weights.slice(0, 10), [weights]);

  return (
    <div className="routeboard-shell">
      <header className="route-strip-chrome">
        <div className="route-strip-top">
          <div className="route-brand">
            <span className="route-brand-mark">BR</span>
            <div>
              <div className="route-brand-name">BagRoute</div>
              <div className="route-brand-sub">投递路线条带</div>
            </div>
          </div>
          <label className="route-pick">
            路线
            <select value={rid} onChange={(e) => setRid(Number(e.target.value))}>
              {routes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <nav className="route-bead-nav" aria-label="功能">
            {stripLinks.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `route-bead-link${isActive ? " route-bead-link--on" : ""}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="stop-timeline" aria-label="站点时间线">
          <div className="stop-timeline-rail" />
          {stops.length === 0 && (
            <div className="stop-timeline-empty">选择路线后显示站点珠串</div>
          )}
          {stops.map((s, i) => (
            <div key={s.id} className="stop-bead" style={{ zIndex: stops.length - i }}>
              <div className="stop-bead-dot" />
              <div className="stop-bead-card">
                <span className="stop-bead-seq">#{s.seq}</span>
                <strong>{s.name}</strong>
                <span className="mono">
                  {s.weight_kg}kg · {s.volume_l}L
                </span>
              </div>
            </div>
          ))}
        </div>
      </header>

      <div className="route-twin-lanes">
        <section className="pack-plan-lane">
          <div className="lane-eyebrow">装袋计划台</div>
          <Outlet />
        </section>
        <aside className="meter-lane" aria-label="重量体积仪表">
          <div className="lane-eyebrow">重量 / 体积仪表</div>
          {meters.length === 0 && <p className="meter-empty">暂无袋重数据</p>}
          {meters.map((w) => (
            <div key={w.bag_id} className="meter-block">
              <div className="meter-head">
                <span>袋 {w.bag_index}</span>
                <span className="mono">
                  {w.weight_kg}kg / {w.volume_l}L
                </span>
              </div>
              <div className="meter-row">
                <span>重</span>
                <div className="meter-bar">
                  <span style={{ width: `${Math.min(100, w.fill_weight_pct)}%` }} />
                </div>
                <span className="mono">{w.fill_weight_pct}%</span>
              </div>
              <div className="meter-row">
                <span>体</span>
                <div className="meter-bar meter-bar--vol">
                  <span style={{ width: `${Math.min(100, w.fill_volume_pct)}%` }} />
                </div>
                <span className="mono">{w.fill_volume_pct}%</span>
              </div>
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
