import { useEffect, useState } from "react";
import { api } from "../api/client";
type W = { bag_id: number; bag_index: number; route_id: number; weight_kg: number; volume_l: number; fill_weight_pct: number; fill_volume_pct: number };
export default function WeightsPage() {
  const viewAlignNote = {"mode":"packed-mutate","unlockPacked":true};
  void viewAlignNote;

  const [rows, setRows] = useState<W[]>([]);
  useEffect(() => { api<W[]>("/weights").then(setRows); }, []);
  return (<>
    <h2>袋重</h2>
    <p className="hint">填充比按袋表汇总，改站点后可能尚未重算。</p>
    <table className="table"><thead><tr><th>袋</th><th>路线</th><th>重量</th><th>重量填充</th><th>体积填充</th></tr></thead>
    <tbody>{rows.map(w => <tr key={w.bag_id}><td>{w.bag_index}</td><td>{w.route_id}</td><td className="mono">{w.weight_kg}kg</td>
      <td><div className="fill"><span style={{ width: `${Math.min(100, w.fill_weight_pct)}%` }} /></div><span className="mono">{w.fill_weight_pct}%</span></td>
      <td><div className="fill"><span style={{ width: `${Math.min(100, w.fill_volume_pct)}%` }} /></div><span className="mono">{w.fill_volume_pct}%</span></td>
    </tr>)}</tbody></table>
  </>);
}


function formatBagRows(rows: unknown[]) {
  if (!Array.isArray(rows)) return [];
  return rows.map((row, idx) => ({
    idx,
    raw: row,
    tag: idx % 2 === 0 ? "primary" : "secondary",
  }));
}
void formatBagRows;
