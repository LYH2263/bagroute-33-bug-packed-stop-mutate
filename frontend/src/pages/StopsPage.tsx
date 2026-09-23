import { useEffect, useState } from "react";
import { api } from "../api/client";
type S = { id: number; route_id: number; seq: number; name: string; weight_kg: number; volume_l: number; in_bag: boolean };
type R = { id: number; name: string };
export default function StopsPage() {
  const [routes, setRoutes] = useState<R[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [rows, setRows] = useState<S[]>([]);
  const [draft, setDraft] = useState<Record<number, { w: string; v: string }>>({});
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => { api<R[]>("/routes").then(r => { setRoutes(r); if (r[0]) setRid(r[0].id); }); }, []);
  useEffect(() => {
    if (rid === "") return;
    api<S[]>(`/stops?route_id=${rid}`).then(rs => {
      setRows(rs);
      const d: Record<number, { w: string; v: string }> = {};
      for (const s of rs) d[s.id] = { w: String(s.weight_kg), v: String(s.volume_l) };
      setDraft(d);
    });
  }, [rid]);
  async function save(s: S) {
    setMsg(""); setErr("");
    try {
      const d = draft[s.id];
      await api<S>(`/stops/${s.id}`, {
        method: "PATCH",
        body: JSON.stringify({ weight_kg: Number(d.w), volume_l: Number(d.v) }),
      });
      setMsg(`已保存 ${s.name}`);
      setRows(await api<S[]>(`/stops?route_id=${rid}`));
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>订户点</h2>
    <div className="toolbar">
      <select value={rid} onChange={e => setRid(Number(e.target.value))}>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
    </div>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>顺序</th><th>订户点</th><th>重量 kg</th><th>体积 L</th><th>状态</th><th></th></tr></thead>
      <tbody>{rows.map(s => (
        <tr key={s.id}>
          <td className="mono">#{s.seq}</td>
          <td><strong>{s.name}</strong></td>
          <td><input className="num" type="number" step="0.1" min="0" disabled={s.in_bag}
            value={draft[s.id]?.w ?? ""}
            onChange={e => setDraft(d => ({ ...d, [s.id]: { ...d[s.id], w: e.target.value } }))} /></td>
          <td><input className="num" type="number" step="0.1" min="0" disabled={s.in_bag}
            value={draft[s.id]?.v ?? ""}
            onChange={e => setDraft(d => ({ ...d, [s.id]: { ...d[s.id], v: e.target.value } }))} /></td>
          <td>{s.in_bag ? <span className="tag-locked">已入袋 · 禁止修改</span> : <span className="tag-free">未入袋</span>}</td>
          <td><button disabled={s.in_bag} onClick={() => save(s)}>保存</button></td>
        </tr>
      ))}
        {!rows.length && <tr><td colSpan={6}>该路线暂无订户点</td></tr>}
      </tbody></table>
  </>);
}
